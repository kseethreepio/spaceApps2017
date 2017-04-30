from __future__ import print_function
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


from __future__ import print_function
import time, sys, signal, atexit
from upm import pyupm_uln200xa as upmULN200XA
from upm import pyupm_grove as grove

HTHRESHOLD = 20 # temperature threshold (high) in celsius

def main():
    # Create the temperature sensor object using AIO pin 0
    temp = grove.GroveTemp(0)
    #print(temp.name())

    # Instantiate a Stepper motor on a ULN200XA Darlington Motor Driver
    # This was tested with the Grove Geared Step Motor with Driver
    # Instantiate a ULN2003XA stepper object
    myUln200xa = upmULN200XA.ULN200XA(4096, 8, 9, 10, 11)
    ## Exit handlers ##
    # This stops python from printing a stacktrace when you hit control-C
    def SIGINTHandler(signum, frame):
        raise SystemExit
    # This lets you run code on exit,
    # including functions from myUln200xa
    def exitHandler():
        print("Exiting")
        sys.exit(0)    
    # Register exit handlers
    atexit.register(exitHandler)
    signal.signal(signal.SIGINT, SIGINTHandler)   
    myUln200xa.setSpeed(5) # 5 RPMs
    myUln200xa.setDirection(upmULN200XA.ULN200XA_DIR_CW)
    
    # Read the temperature ten times, printing both the Celsius and
    # equivalent Fahrenheit temperature, waiting 5 second between readings
    # if temperature > HTHRESHOLD, turn stepper motor by 1 revolution
    for i in range(0, 10):
        celsius = temp.value()
        fahrenheit = celsius * 9.0/5.0 + 32.0;
        print("%d degrees Celsius, or %d degrees Fahrenheit" \
            % (celsius, fahrenheit))
        if celsius > HTHRESHOLD:
            myUln200xa.stepperSteps(4096)
        time.sleep(5)

    # Delete the temperature sensor object
    del temp

    #print("Rotating 1 revolution clockwise.")
    #myUln200xa.stepperSteps(4096)

    #print("Sleeping for 2 seconds...")
    #time.sleep(2)

    #print("Rotating 1/2 revolution counter clockwise.")
    #myUln200xa.setDirection(upmULN200XA.ULN200XA_DIR_CCW)
    #myUln200xa.stepperSteps(2048)

    # release
    myUln200xa.release()

    # exitHandler is called automatically

if __name__ == '__main__':
    main()
