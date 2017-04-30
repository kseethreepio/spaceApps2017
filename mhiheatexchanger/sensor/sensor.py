from __future__ import print_function

# Author: "Mars Home Improvement" Space Apps 2017 Team.

# Built upon jhd1313m1-lcd.py and grovetemp.py scripts
# Original header comments from those script(s) are below:

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

import atexit, os, sys, signal, time
sys.path.append(os.getcwd())  # Workaround for import errors for MHI module
from datetime import datetime

from upm import pyupm_grove as grove
from upm import pyupm_jhd1313m1 as lcd
from upm import pyupm_uln200xa as upmULN200XA

UTHRESHOLD = 24  # Deg C
LTHRESHOLD = 20  # Deg C
TEMP_LABEL_STRING = "Current temp:"
TEMP_STRING = "{0} C / {1} F"

STEPPER_SPEED = 8  # RPMs
STEPPER_STEPS = 4096

POLL_INTERVAL = 10  # Seconds
TEST_RUN_LENGTH = 120  # Seconds; if running code for finite time for testing
DEBUG = True  # For running sensor in test mode (i.e. for finite period of time)

CENTRAL_CMD_MESSAGE_COLD = "lower_threshold_passed"
CENTRAL_CMD_MESSAGE_HOT = "upper_threshold_passed"
CENTRAL_CMD_MESSAGE_HAPPY = "no_longer_past_threshold"

ERROR_VALVE_OPEN = "ERROR: Valve already open."
ERROR_VALVE_CLOSED = "ERROR: Valve already closed."

LOCAL_OUTPUT_PATH = os.path.join(os.path.expanduser("~"),"sensorTemps")
LOCAL_OUTPUT_FILENAME = "{0}_{1}_{2}_sensorTemps.csv"
TEMP_RECORD_FILE_HEADER = "Date-UTC,Time-UTC,Room,Sensor,TempC,TempF\n"


class Sensor(object):
    '''Sensor module object. Exposes attributes/properties for accessing the
    sensor module's temperature sensor, LCD, stepper motor, and most recent temp 
    reading (in degrees C and F).
    '''

    def __init__(self, commander, sensor_room, sensor_name, sensor_id, \
        temp_sensor_pin, temp_sensor_only=False):
        '''Init method for Sensor object.

        Note: 'has_passed_threshold' is a flag for tracking when sensor has passed 
        uppoer or lower threshold (to help track whether to evaluate calling 
        closeValve()).

        :param MissionControl commander: MissionControl object instance that 
            started the sensor.
        :param str sensor_room: Room name where physical sensor HW module is located.
        :param str sensor_name: Name of individual sensor HW module in the room.
        :param int temp_sensor_pin: AIO pin that temp sensor is on (typically 0).
        :param bool temp_sensor_only: Optional param to indicate that the module only
            has a temperature sensor (typically for demo purposes).

        :return: Sensor object
        '''

        self.commander = commander
        self.sensor_room = sensor_room
        self.sensor_name = sensor_name
        self.sensor_id = sensor_id
        self.temp_sensor_pin = temp_sensor_pin
        self.temp_sensor_only = temp_sensor_only
        self.latest_temp_c = None
        self.latest_temp_f = None
        self.has_passed_threshold = False
        self.valve_open = False

        self.temp = grove.GroveTemp(self.temp_sensor_pin)  # Create temp sensor obj

        if not self.temp_sensor_only:
            # Instantiate a Stepper motor on a ULN200XA Darlington Motor Driver
            # This was tested with the Grove Geared Step Motor with Driver
            # Instantiate a ULN2003XA stepper object
            self.stepperMotor = upmULN200XA.ULN200XA(4096, 8, 9, 10, 11)
            atexit.register(self.exitHandler)  # Register exit handlers
            signal.signal(signal.SIGINT, self.SIGINTHandler)
            self.stepperMotor.setSpeed(STEPPER_SPEED)

            # Set up the LCD
            self.lcd = lcd.Jhd1313m1(0, 0x3E, 0x62)

    def recordTemp(self):
        '''Helper method to write temperature readings to file.
        TODO: Write hsitorical readings to DB (ideally via ORM)

        :return: File handle to output file.
        '''

        # Info needed for writing file + recording temps
        current_timestamp = datetime.utcnow()
        current_date_utc = current_timestamp.strftime("%Y-%d-%m")
        current_time_utc = current_timestamp.strftime("%H:%M:%S")

        # Prep string to write to file
        # "Date-UTC,Time-UTC,Room,Sensor,TempC,TempF"
        tempRecord = "{0},{1},{2},{3},{4},{5}\n".\
            format(current_date_utc, current_time_utc, self.sensor_room, \
                self.sensor_name, self.latest_temp_c, self.latest_temp_f)

        # Double-check that path for output exists
        if not os.path.isdir(LOCAL_OUTPUT_PATH):
            os.mkdir(LOCAL_OUTPUT_PATH)

        # Prep name of file to write data to
        output_filename = LOCAL_OUTPUT_FILENAME.\
            format(current_date_utc, self.sensor_room, self.sensor_name)
        output_full_path = os.path.join(LOCAL_OUTPUT_PATH, output_filename)

        # If output file doesn't already exist, create it
        if not os.path.isfile(output_full_path):
            with open(output_full_path, "w") as f:
                f.write(TEMP_RECORD_FILE_HEADER + tempRecord)
        else:
            with open(output_full_path, "a") as f:
                f.write(tempRecord)

        return True

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

        if not self.temp_sensor_only:
            self.lcd.setColor(255, 0, 0)
            self.lcd.write(TEMP_STRING.format(self.latest_temp_c, self.latest_temp_f))
        
        self.sendSignalToMissionControl(CENTRAL_CMD_MESSAGE_HOT)

        return True

    def handleLowerThresholdPassed(self):
        '''Handles case where runTempCheck() determines lower temp threshold passed.'''

        if not self.temp_sensor_only:
            self.lcd.setColor(0, 0, 255)
            self.lcd.write(TEMP_STRING.format(self.latest_temp_c, self.latest_temp_f))
        
        self.sendSignalToMissionControl(CENTRAL_CMD_MESSAGE_COLD)

        return True

    def checkLedger(self):
        '''Checks to see whether the current sensor has other sensors in the sys
        actively helping it.
        '''

        if self.sensor_id in self.commander.favor_ledger.keys():
            return self.commander.favor_ledger[self.sensor_id]
        else:
            return False

    def runTempCheck(self):
        '''Runs iteration of checking temperature sensor for current reading.'''

        self.latest_temp_c = self.temp.value()
        self.latest_temp_f = self.latest_temp_c * 9.0/5.0 + 32.0

        if not self.temp_sensor_only: self.lcd.setCursor(1,0)

        # Check whether temp has passed upper or lower threshold
        if self.latest_temp_c >= UTHRESHOLD:
            self.handleUpperThresholdPassed()
        elif self.latest_temp_c < LTHRESHOLD:
            self.handleLowerThresholdPassed()
        else:
            if not self.temp_sensor_only:
                if self.has_passed_threshold and self.valve_open:
                    self.has_passed_threshold = False  # Reset the flag
                    self.closeValve()  # Now that temp has stabilized, close valve

                    # Also tell mission control that temp is now good, so that
                    # mission control can square up the sensor's ledger
                    self.sendSignalToMissionControl(CENTRAL_CMD_MESSAGE_HAPPY)

                self.lcd.setColor(0, 255, 0)
                self.lcd.write(TEMP_STRING.\
                    format(self.latest_temp_c, self.latest_temp_f))

            else:  # Just reset the flag for the temp_sensor_only case
                self.has_passed_threshold = False

        self.recordTemp()  # Write output to local file (for historical readings)

        return True

    def SIGINTHandler(self, signum, frame):
        '''This stops Python from printing a stacktrace when you hit control-C.'''
        raise SystemExit

    def exitHandler(self):
        '''This lets you run code on exit, including functions from myUln200xa.'''
        print("Exiting")
        sys.exit(0)

    @staticmethod
    def respondToMissionControl(self, orders):
        '''Handles message/command from central module to open valve.'''

        if orders == 'open_valve':
            self.openValve()

        elif orders == 'close_valve':
            self.closeValve()

        return True

    def sendSignalToMissionControl(self, signal):
        '''Sends message to central command indicating that threshold passed.'''

        request = {
            'sensor': self,
            'signal': signal
        }

        self.commander.receiveAlertFromSensor(self.commander, request)

        return True

    def openValve(self):
        '''Activates stepper motor in order to open valve for heat transfer.'''

        if not self.valve_open and not self.temp_sensor_only:
            self.stepperMotor.setDirection(upmULN200XA.ULN200XA_DIR_CW)
            self.stepperMotor.stepperSteps(STEPPER_STEPS)
            self.valve_open = True
            return True
        else:
            print(ERROR_VALVE_OPEN)
            return False

    def closeValve(self):
        '''Activates stepper motor in order to close valve after heat transfer.'''

        if self.valve_open and not self.temp_sensor_only:
            self.stepperMotor.setDirection(upmULN200XA.ULN200XA_DIR_CCW)
            self.stepperMotor.stepperSteps(STEPPER_STEPS)
            self.valve_open = False
            return True
        else:
            print(ERROR_VALVE_CLOSED)
            return False

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

    def startSensor(self):
        '''Main loop for checking temperature. Runs indefinitely.'''

        try:
            # Read temperature, waiting POLL_INTERVAL seconds between readings
            if not DEBUG:  # In standard operating mode, run indefinitely
                if not self.temp_sensor_only:
                    self.prepScreen("start")    
                while True:
                    self.runTempCheck()
                    time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            # Teardown/cleanup
            del self.temp  # Delete the temperature sensor object
            if not self.temp_sensor_only:  # Close valve, turn off display
                if self.valve_open: self.closeValve()
                self.prepScreen("stop")

        return True        

    def runSensorTest(self):
        '''Main loop for checking temperature. Runs for TEST_RUN_LENGTH seconds.'''

        if DEBUG:
            print("Starting temp check cycle...")
            for i in range(0, TEST_RUN_LENGTH / POLL_INTERVAL):
                self.runTempCheck()
                print("Sleeping till next temp check...")
                time.sleep(POLL_INTERVAL)
        else:
            print("ERROR: Please set DEBUG flag to True, then try again.")
            return False

        # Teardown/cleanup
        del self.temp  # Delete the temperature sensor object
        if not self.temp_sensor_only:
            self.prepScreen("stop")  # Turn off the display
            self.testMotor()  # FOR DEMO - Run motor test

        return True       
