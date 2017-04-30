from __future__ import print_function

# Author: "Mars Home Improvement" Space Apps 2017 Team

# Built upon jhd1313m1-lcd.py and grovetemp.py scripts:
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

UTHRESHOLD = 25
LTHRESHOLD = 24

def prepScreen(command):
    '''Function for clearing and turning the screen on/off
    '''

    if command == 'start':
        # Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
        myLcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
        myLcd.clear()        
        myLcd.displayOn()
        myLcd.backlightOn()

        return myLcd

    elif command == 'stop':  # Turn off the display (conserve power)
        myLcd.clear()
        myLcd.displayOff()
        myLcd.backlightOff()

        return False

def main():
    # Start up the LCD
    myLcd = prepScreen("start")
    myLcd.setCursor(0,0)  # Set LCD cursory to write out the top line
    myLcd.setColor(0, 0, 255)  # By default, set LCD color to blue
    myLcd.write("Current temp:")  # Write out label for temperature

    # Create the temperature sensor object using AIO pin 0
    temp = grove.GroveTemp(0)
    # print(temp.name())

    # Read the temperature ten times, printing both the Celsius and
    # equivalent Fahrenheit temperature, waiting one second between readings
    for i in range(0, 30):
        celsius = temp.value()
        fahrenheit = celsius * 9.0/5.0 + 32.0;
        # print("%d degrees Celsius, or %d degrees Fahrenheit" \
        #     % (celsius, fahrenheit))
        tempString = "%s C / %s F" % (celsius, fahrenheit)

        # Update LCD output
        myLcd.setCursor(1,0)  # Move cursor to next line
        if celsius >= UTHRESHOLD:  # If it gets above 24 C, turn screen red
            myLcd.setColor(255, 0, 0)
            myLcd.write(tempString)
        elif (celsius == LTHRESHOLD):
            myLcd.setColor(0, 255, 0)
            myLcd.write(tempString)
        else:  # TODO: Is there a getColor method?
            myLcd.setColor(0, 0, 255)
            myLcd.write(tempString)

        time.sleep(1)

    # Delete the temperature sensor object
    del temp

    # Turn off the display
    prepScreen("stop")

if __name__ == '__main__':
    main()