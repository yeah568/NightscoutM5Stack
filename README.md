# Nightscout M5Stack
Nightscout display for an M5Stack, based on [Scott Hanselman's version for the Adafruit PyPortal](https://github.com/shanselman/NightscoutPyPortal).

## Installing MicroPython on the M5Stack
This is pretty poorly documented. Here's my best attempt at describing it.

### Windows Users
Use Windows Subsystem for Linux - it's much easier. If you're using what's known as "Bash on Ubuntu on Windows", install Ubuntu from the Windows Store instead and use that.


1. Clone the [M5Stack_MicroPython repo](https://github.com/m5stack/M5Stack_MicroPython)
2. Follow the steps for [building MicroPython for ESP32](https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/wiki/build)
    1. Get dependencies:

       `sudo apt-get install git wget make libncurses-dev flex bison gperf python python-serial`
    2. Clone the M5Stack_MicroPython repo

       `git clone --depth 1 https://github.com/m5stack/M5Stack_MicroPython.git`
    3. Change to the MicroPython_BUILD directory

       `cd M5Stack_MicroPython/MicroPython_BUILD`
    4. Create the initial sdkconfig. You may also want to update the serial flashing port at this point to the correct serial port. (`COMx` is mapped to `/dev/ttySx`, replace x as needed).

      `./BUILD.sh menuconfig`

    5. Build the firmware

      `./BUILD.sh`

    6. Flash the firmware

      `./BUILD.sh flash`

Congrats, you should now have MicroPython running on your M5Stack.

Use ampy (or similar) to get the code onto the device.

1. Get dependencies
   `sudo pip3 install adafruit-ampy`
2. Push the files to the M5Stack
   `ampy --port /dev/ttySx put main.py secrets.py UbuntuMono-B40.fon`
3. Reboot the M5Stack, and things should work!