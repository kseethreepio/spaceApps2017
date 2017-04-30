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

import time, sys, signal, atexit

from upm import pyupm_grove as grove
from upm import pyupm_jhd1313m1 as lcd
from upm import pyupm_uln200xa as upmULN200XA

UTHRESHOLD = 25  # Deg C
LTHRESHOLD = 16  # Deg C
TEMP_STRING = "{0} C / {1} F"
TEMP_SENSOR_PIN = 0

STEPPER_SPEED = 8  # RPMs
STEPPER_STEPS = 4096

POLL_INTERVAL = 2  # Seconds
TEST_RUN_LENGTH = 30  # Seconds; if running code for finite time for testing
DEBUG = True  # For running sensor in test mode (i.e. for finite period of time)


class Sensor(Object):
    '''TODO'''

    def __init__(self, sensor_room, sensor_name):
        self.sensor_room = sensorRoom
        self.sensor_name = sensorName
        self.latest_temp = None

        # Instantiate a Stepper motor on a ULN200XA Darlington Motor Driver
        # This was tested with the Grove Geared Step Motor with Driver
        # Instantiate a ULN2003XA stepper object
        self.sensorValveMotor = upmULN200XA.ULN200XA(4096, 8, 9, 10, 11)
        atexit.register(self.exitHandler)  # Register exit handlers
        signal.signal(signal.SIGINT, self.SIGINTHandler)
        self.sensorValveMotor.setSpeed(STEPPER_SPEED)

        self.lcd = lcd.Jhd1313m1(0, 0x3E, 0x62)

        self.temp = grove.GroveTemp(TEMP_SENSOR_PIN)  # Create the temperature sensor obj via AIO pin 0

    def prepScreen(self, command, lcdObj=None):
        '''Function for clearing and turning the screen on/off.'''

        if command == 'start':
            # Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
            lcdObj.clear()        
            lcdObj.displayOn()
            lcdObj.backlightOn()

            # Write initial message to LCD
            lcdObj.setCursor(0,0)  # Set LCD cursory to write out the top line
            lcdObj.setColor(0, 0, 0)  # By default, set LCD color to white
            lcdObj.write("Current temp:")  # Write out label for temperature

            return True

        elif command == 'stop':  # Turn off the display
            # Clear messages from LCD and put into lower-power mode
            lcdObj.clear()
            lcdObj.displayOff()
            lcdObj.backlightOff()

            return True

    def handleUpperThresholdPassed(self, tempObj, lcdObj):
        '''Handles case where runTempCheck() determines upper temp threshold passed.'''

        lcdObj.setColor(255, 0, 0)
        lcdObj.write(TEMP_STRING.format(self.temp_c, self.temp_f))

        # TODO: Signal central module that upper threshold passed

        return False

    def handleLowerThresholdPassed(self, tempObj, lcdObj):
        '''Handles case where runTempCheck() determines lower temp threshold passed.'''

        lcdObj.setColor(0, 0, 255)
        lcdObj.write(TEMP_STRING.format(self.temp_c, self.temp_f))

        # TODO: Signal central module that lower threshold passed

        return False

    def runTempCheck(self, tempObj, lcdObj):
        '''Runs iteration of checking temperature sensor for current reading.'''

        celsius = tempObj.value()
        self.temp_c = celsius
        self.temp_f = celsius * 9.0/5.0 + 32.0

        lcdObj.setCursor(1,0)  # Move cursor to next line, to write out temp

        # Check whether temp has passed upper or lower threshold
        if celsius >= UTHRESHOLD:
            handleUpperThresholdPassed(tempObj, lcdObj)
        elif celsius < LTHRESHOLD:
            handleLowerThresholdPassed(tempObj, lcdObj)
        else:
            lcdObj.setColor(0, 255, 0)
            lcdObj.write(TEMP_STRING.format(self.temp_c, self.temp_f))

        return True

    def SIGINTHandler(self, signum, frame):
        '''This stops Python from printing a stacktrace when you hit control-C.'''
        raise SystemExit

    def exitHandler(self):
        '''This lets you run code on exit, including functions from myUln200xa.'''
        print("Exiting")
        sys.exit(0)

    @staticmethod
    def respondToCentralCommand(self, orders):
        '''Handles message/command from central module to open valve.'''

        if orders == 'open_valve':
            openValve()

        elif orders == 'close_valve':
            close_valve()

        return True

    def openValve(self, stepperObj):
        '''Activates stepper motor in order to open valve for heat transfer.'''

        stepperObj.setDirection(upmULN200XA.ULN200XA_DIR_CW)
        stepperObj.stepperSteps(4096)

        return True

    def closeValve(self, stepperObj):
        '''Activates stepper motor in order to close valve after heat transfer.'''

        stepperObj.setDirection(upmULN200XA.ULN200XA_DIR_CCW)
        stepperObj.stepperSteps(4096)

        return True


def main():
    '''Main loop.'''

    sensor = Sensor()
    lcd = sensor.lcd  # Start up the LCD
    temp = sensor.temp  # Start the temp sensor

    # Read temperature, waiting 1 s between readings, providing temp in deg C/F
    if not DEBUG:  # In standard operating mode, run indefinitely
        while True:
            runTempCheck(temp, lcd)
            # TODO: Handle signal from central module to activate motor/open value
            time.sleep(POLL_INTERVAL)

    elif DEBUG:  # Run temp check loop for TEST_RUN_LENGTH seconds
        print("Starting temp check cycle...")
        for i in range(0, TEST_RUN_LENGTH / POLL_INTERVAL):
            runTempCheck(temp, lcd)
            # TODO: Handle signal from central module to activate motor/open value
            print("Sleeping till next temp check...")
            time.sleep(POLL_INTERVAL)

    # Teardown/cleanup
    del temp  # Delete the temperature sensor object
    prepScreen("stop", lcd)  # Turn off the display

    # TEMP - Testing motor
    print("Done with temp check cycle.")
    print("Opening valve...")
    openValve(motor)
    print("Changing directions...")
    time.sleep(5)
    closeValve(motor)
    print("Done.")


if __name__ == '__main__':
    main()