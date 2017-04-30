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
TEMP_LABEL_STRING = "Current temp:"
TEMP_STRING = "{0} C / {1} F"

STEPPER_SPEED = 8  # RPMs
STEPPER_STEPS = 4096

POLL_INTERVAL = 2  # Seconds
TEST_RUN_LENGTH = 30  # Seconds; if running code for finite time for testing
DEBUG = True  # For running sensor in test mode (i.e. for finite period of time)

CENTRAL_CMD_MESSAGE_COLD = "lower_threshold_passed"
CENTRAL_CMD_MESSAGE_HOT = "upper_threshold_passed"


class Sensor(Object):
    '''Sensor module object. Exposes attributes/properties for accessing the
    sensor module's temperature sensor, LCD, stepper motor, and most recent temp 
    reading (in degrees C and F).
    '''

    def __init__(self, sensor_room, sensor_name, temp_sensor_pin):
        '''Init method for Sensor object.

        :param str sensor_room: Room name where physical sensor HW module is located
        :param str sensor_name: Name of individual sensor HW module in the room
        :param int temp_sensor_pin: AIO pin that temperature sensor is on (should be 0)
        :return: Sensor object
        '''

        self.sensor_room = sensor_room
        self.sensor_name = sensor_name
        self.temp_sensor_pin = temp_sensor_pin
        self.latest_temp_c = None
        self.latest_temp_f = None

        # Instantiate a Stepper motor on a ULN200XA Darlington Motor Driver
        # This was tested with the Grove Geared Step Motor with Driver
        # Instantiate a ULN2003XA stepper object
        self.stepperMotor = upmULN200XA.ULN200XA(4096, 8, 9, 10, 11)
        atexit.register(self.exitHandler)  # Register exit handlers
        signal.signal(signal.SIGINT, self.SIGINTHandler)
        self.stepperMotor.setSpeed(STEPPER_SPEED)

        self.lcd = lcd.Jhd1313m1(0, 0x3E, 0x62)
        self.temp = grove.GroveTemp(self.temp_sensor_pin)  # Create temp sensor obj

    def prepScreen(self, command):
        '''Function for clearing and turning the screen on/off.'''

        if command == 'start':
            # Initialize Jhd1313m1 at 0x3E (LCD_ADDRESS) and 0x62 (RGB_ADDRESS)
            self.lcd.clear()        
            self.lcd.displayOn()
            self.lcd.backlightOn()

            # Write initial message to LCD
            self.lcd.setCursor(0,0)  # Set LCD cursory to write out the top line
            self.lcd.setColor(0, 0, 0)  # By default, set LCD color to white
            self.lcd.write(TEMP_LABEL_STRING)  # Write out label for temperature

            return True

        elif command == 'stop':  # Turn off the display
            # Clear messages from LCD and put into lower-power mode
            self.lcd.clear()
            self.lcd.displayOff()
            self.lcd.backlightOff()

            return True

    def handleUpperThresholdPassed(self):
        '''Handles case where runTempCheck() determines upper temp threshold passed.'''

        self.lcd.setColor(255, 0, 0)
        self.lcd.write(TEMP_STRING.format(self.temp_c, self.temp_f))
        self.sendSignalToCentralCommand(CENTRAL_CMD_MESSAGE_HOT)

        return True

    def handleLowerThresholdPassed(self):
        '''Handles case where runTempCheck() determines lower temp threshold passed.'''

        self.lcd.setColor(0, 0, 255)
        self.lcd.write(TEMP_STRING.format(self.temp_c, self.temp_f))
        self.sendSignalToCentralCommand(CENTRAL_CMD_MESSAGE_COLD)

        return True

    def runTempCheck(self):
        '''Runs iteration of checking temperature sensor for current reading.'''

        self.latest_temp_c = self.temp.value()
        self.latest_temp_f = self.latest_temp_c * 9.0/5.0 + 32.0

        self.lcd.setCursor(1,0)  # Move cursor to next line, to write out temp

        # Check whether temp has passed upper or lower threshold
        if self.latest_temp_c >= UTHRESHOLD:
            handleUpperThresholdPassed()
        elif self.latest_temp_c < LTHRESHOLD:
            handleLowerThresholdPassed()
        else:
            self.lcd.setColor(0, 255, 0)
            self.lcd.write(TEMP_STRING.format(self.latest_temp_c, self.latest_temp_f))

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

    def sendSignalToCentralCommand(self, signal):
        '''Sends message to central command indicating that threshold passed.'''

        # TODO

        return signal

    def openValve(self):
        '''Activates stepper motor in order to open valve for heat transfer.'''

        self.stepperMotor.setDirection(upmULN200XA.ULN200XA_DIR_CW)
        self.stepperMotor.stepperSteps(STEPPER_STEPS)

        return True

    def closeValve(self):
        '''Activates stepper motor in order to close valve after heat transfer.'''

        self.stepperMotor.setDirection(upmULN200XA.ULN200XA_DIR_CCW)
        self.stepperMotor.stepperSteps(STEPPER_STEPS)

        return True

    def testMotor(self):
        '''Test function for trying out the sensor module's motor.'''

        print("Done with temp check cycle.")
        print("Opening valve...")
        self.openValve()
        print("Changing directions...")
        time.sleep(5)
        self.closeValve()
        print("Done.")

        return True


def main():
    '''Main loop.'''

    sensor = Sensor("Room_A", "Sensor_1", 0)
    lcd = sensor.lcd  # Start up the LCD
    temp = sensor.temp  # Start the temp sensor

    # Read temperature, waiting 1 s between readings, providing temp in deg C/F
    if not DEBUG:  # In standard operating mode, run indefinitely
        while True:
            sensor.runTempCheck()
            # TODO: Handle signal from central module to activate motor/open value
            time.sleep(POLL_INTERVAL)

    elif DEBUG:  # Run temp check loop for TEST_RUN_LENGTH seconds
        print("Starting temp check cycle...")
        for i in range(0, TEST_RUN_LENGTH / POLL_INTERVAL):
            sensor.runTempCheck(temp, lcd)
            # TODO: Handle signal from central module to activate motor/open value
            print("Sleeping till next temp check...")
            time.sleep(POLL_INTERVAL)

    # Teardown/cleanup
    del temp  # Delete the temperature sensor object
    sensor.prepScreen("stop")  # Turn off the display
    sensor.testMotor()  # FOR DEMO - Run motor test


if __name__ == '__main__':
    main()