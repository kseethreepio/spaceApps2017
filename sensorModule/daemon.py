from __future__ import print_function

# Author: "Mars Home Improvement" Space Apps 2017 Team.

# Built upon jhd1313m1-lcd.py and grovetemp.py scripts
# Original header comments from those script(s) are below.
# 
# Author: Brendan Le Foll <brendan.le.foll@intel.com>
# Contributions: Sarah Knepper <sarah.knepper@intel.com>
# Copyright (c) 2014 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time
from upm import pyupm_grove as grove
from upm import pyupm_jhd1313m1 as lcd

UTHRESHOLD = 25  # Deg C
LTHRESHOLD = 24  # Deg C

TEMP_STRING = "{0} C / {1} F"

POLL_INTERVAL = 1  # Seconds
TEST_RUN_LENGTH = 30  # Seconds; if running code for finite time for testing
DEBUG = True  # For running sensor in test mode (i.e. for finite period of time)


def prepScreen(command, lcdObj=None):
    '''Function for clearing and turning the screen on/off.'''

    if command == 'start':
        # Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
        lcdObj = lcd.Jhd1313m1(0, 0x3E, 0x62)
        lcdObj.clear()        
        lcdObj.displayOn()
        lcdObj.backlightOn()

        # Write initial message to LCD
        lcdObj.setCursor(0,0)  # Set LCD cursory to write out the top line
        lcdObj.setColor(0, 0, 255)  # By default, set LCD color to blue
        lcdObj.write("Current temp:")  # Write out label for temperature

        return lcdObj

    elif command == 'stop':  # Turn off the display
        # Clear messages from LCD and put into lower-power mode
        lcdObj.clear()
        lcdObj.displayOff()
        lcdObj.backlightOff()

        return False


def handleUpperThresholdPassed(tempObj, lcdObj):
    '''Handles case where runTempCheck() determines upper temp threshold passed.'''

    lcdObj.setColor(255, 0, 0)
    lcdObj.write(TEMP_STRING.format(tempObj.value(), tempObj.fahrenheit))

    # TODO: Signal central module that upper threshold passed

    return False


def handleLowerThresholdPassed(tempObj, lcdObj):
    '''Handles case where runTempCheck() determines lower temp threshold passed.'''

    lcdObj.setColor(0, 255, 0)
    lcdObj.write(TEMP_STRING.format(tempObj.value(), tempObj.fahrenheit))

    # TODO: Signal central module that lower threshold passed

    return False


def runTempCheck(tempObj, lcdObj):
    '''Runs iteration of checking temperature sensor for current reading.'''

    celsius = temp.value()
    fahrenheit = celsius * 9.0/5.0 + 32.0;
    temp.fahrenheit = fahrenheit  # temp obj appears to be mutable; storing F val

    lcdObj.setCursor(1,0)  # Move cursor to next line, to write out temp

    # Check whether temp has passed upper or lower threshold
    if celsius >= UTHRESHOLD:
        handleUpperThresholdPassed(temp, lcdObj)
    elif (celsius < LTHRESHOLD):
        handleLowerThresholdPassed(temp, lcdObj)
    else:
        lcdObj.setColor(0, 0, 255)
        lcdObj.write(TEMP_STRING.format(tempObj.value(), tempObj.fahrenheit))

    return False


def respondToCentralCommand():
    '''Handles message/command from central module to open valve.'''

    return False


def openValve():
    '''Activates stepper motor in order to open valve for heat transfer.'''

    return False


def closeValve():
    '''Activates stepper motor in order to close valve after heat transfer.'''

    return False


def main():
    '''Main loop.'''

    lcd = prepScreen("start")  # Start up the LCD
    temp = grove.GroveTemp(0)  # Create the temperature sensor obj via AIO pin 0

    # Read temperature, waiting 1 s between readings, providing temp in deg C/F
    if not DEBUG:  # In standard operating mode, run indefinitely
        while True:
            runTempCheck(temp)
            # TODO: Handle signal from central module to activate motor/open value
            time.sleep(1)

    elif DEBUG:  # Run temp check loop for TEST_RUN_LENGTH seconds
        for i in range(0, TEST_RUN_LENGTH):
            runTempCheck(temp, lcd)
            # TODO: Handle signal from central module to activate motor/open value
            time.sleep(1)

    # Teardown/cleanup
    del temp  # Delete the temperature sensor object
    prepScreen("stop", lcd)  # Turn off the display


if __name__ == '__main__':
    main()