import _thread
import json
import machine
import math
import time
import urequests as requests

from m5stack import lcd


try:
    from secrets import secrets
except ImportError:
    print("WiFi and API secrets are kept in secrets.py, please add them there!")
    raise

# Basic config options
USE_METRIC = True # Use mmol/L instead of mg/dL
GRAPH_DURATION = 3 * 60 * 60 # Duration represented by the graph
GRAPH_MAX_POINTS = 36 # Max number of points on the graph. Usually GRAPH_DURATION / 300 seconds

# max sgv in mg/dl, min is 0
GRAPH_MAX = 300

# Dimensions of graph in px
GRAPH_HEIGHT = 160
GRAPH_WIDTH = 320

SCREEN_HEIGHT = 240

# Set up where we'll be fetching data from
DATA_SOURCE = secrets['nightscout_url']
BG_VALUE = [0, 'sgv']
BG_DIRECTION = [0, 'direction']
DATA_AGE = [0, 'date'] # This is in GMT time

# Alert Colors
RED = 0xee4035;     # CRIT HIGH, CRIT LOW
ORANGE = 0xf37736;  # WARN LOW 
YELLOW = 0xfdf498;  # WARN HIGH
GREEN = 0x7bc043;   # BASE
BLUE = 0x0392cf;  # STALE DATA

BLACK = 0x000000

# Alert Levels
CRIT_HIGH = 280
WARN_HIGH = 200
CRIT_LOW = 56
WARN_LOW = 80

WARN_HIGH_Y = round(WARN_HIGH / GRAPH_MAX * GRAPH_HEIGHT)
WARN_LOW_Y = round(WARN_LOW / GRAPH_MAX * GRAPH_HEIGHT)


def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        lcd.print("Connecting to " + secrets['ssid'] + "\n")
        sta_if.active(True)
        sta_if.connect(secrets['ssid'], secrets['password'])
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())
    lcd.print("Connected! IP: " + sta_if.ifconfig()[0] + "\n")

    rtc = machine.RTC()
    rtc.ntp_sync(server="time.google.com")
    lcd.print("Syncing time\n")
    while not rtc.synced():
        pass
    lcd.print("Time synced! Time: " + str(time.time()) + "\n")


def stale_data(timestamp):
    # stale results is the age at which results are no longer considered valid.
    # This is in minutes
    stale_time = 6

    # Get the current timestamp in GMT
    epoch_time = time.time()
    print("Epoch GMT time:", epoch_time)

    current_time_str = str(timestamp)

    # nightscout sends a higher percision then is necessary and does not use dot notation
    # so we need to cut the last three 0's off the end
    current_time_str = current_time_str[:-3] 
    current_time_int = int(current_time_str)

    # The number of minutes ago that the data was last checked
    last_check = (epoch_time - current_time_int) /60
    print("Data age: ", last_check)

    if last_check > stale_time:
        return True
    else:
        return False
    
def get_bg_color(val, timestamp):
    # If the data is stale then we don't want to rely on it as an alert mech but we do need
    # to know about it.
    if stale_data(timestamp):
        return BLUE
    else:    
        if val > CRIT_HIGH:
            return RED
        elif val > WARN_HIGH:
            return YELLOW
        elif val < CRIT_LOW:
            return RED
        elif val < WARN_LOW:
            return ORANGE
        return GREEN

def text_transform_bg(val):
    conversion_factor = 18 if USE_METRIC else 1
    unit = "mmol/L" if USE_METRIC else "mg/dl"
    return "{:.1f}".format(val / conversion_factor) + ' ' + unit

def text_transform_direction(val):
    if val == "Flat":
        return "->"
    if val == "SingleUp":
        return "^"
    if val == "DoubleUp":
        return "^^"
    if val == "DoubleDown":
        return "vv"
    if val == "SingleDown":
        return "v"
    if val == "FortyFiveDown":
        return ">v"
    if val == "FortyFiveUp":
        return ">^"
    return val


def draw_graph(resp, timeStart, timeEnd):
    # Coloured background for high/low areas
    lcd.rect(0, SCREEN_HEIGHT - GRAPH_HEIGHT, GRAPH_WIDTH, GRAPH_HEIGHT - WARN_HIGH_Y, YELLOW, YELLOW)
    lcd.rect(0, SCREEN_HEIGHT - WARN_LOW_Y, GRAPH_WIDTH, WARN_LOW_Y, RED, RED)

    # Prints lines between graph sections.
    # lcd.line(0, SCREEN_HEIGHT - GRAPH_HEIGHT, GRAPH_WIDTH, SCREEN_HEIGHT - GRAPH_HEIGHT)
    # lcd.line(0, SCREEN_HEIGHT - WARN_HIGH_Y, GRAPH_WIDTH, SCREEN_HEIGHT - WARN_HIGH_Y)
    # lcd.line(0, SCREEN_HEIGHT - WARN_LOW_Y, GRAPH_WIDTH, SCREEN_HEIGHT - WARN_LOW_Y)

    for idx, point in enumerate(resp):
        x = round(GRAPH_WIDTH * (int(point["date"] / 1000)  - timeStart) / (timeEnd - timeStart))
        y = round(min(point["sgv"] / GRAPH_MAX, 1.0) * GRAPH_HEIGHT)
        lcd.circle(x, SCREEN_HEIGHT - y, 3, BLACK, BLACK)



# connect to wifi
do_connect()

def main_loop():
    while True:
        try:
            now = time.time()
            dateStart = now - GRAPH_DURATION
            resp = requests.get(DATA_SOURCE + "?count=" + str(GRAPH_MAX_POINTS) + "&find[date][$gte]=" + str(dateStart)).json()

            current = resp[0]
            bg_color = get_bg_color(current["sgv"], current["date"])
            lcd.clear(bg_color)

            lcd.font("UbuntuMono-B40.fon")
            lcd.setTextColor(color=BLACK, bcolor=bg_color)
            lcd.print(text_transform_bg(current["sgv"]) + " " + text_transform_direction(current["direction"]), lcd.CENTER, 20)

            draw_graph(resp, dateStart, now)
            print("Response is", resp[0]["sgv"])

        except RuntimeError as e:
            print("Some error occured, retrying! -", e)
        time.sleep(180)

# Put the main loop with sleep in a thread to allow normal REPL access.
_thread.start_new_thread("main_loop", main_loop, ())
