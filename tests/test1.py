import time
from upm import pyupm_grovemd as upmGrovemd

def main():
    I2C_BUS = upmGrovemd.GROVEMD_I2C_BUS
    I2C_ADDR = upmGrovemd.GROVEMD_DEFAULT_I2C_ADDR

    # Instantiate an I2C Grove Motor Driver on I2C bus 0
    myMotorDriver = upmGrovemd.GroveMD(I2C_BUS, I2C_ADDR)

    # This example demonstrates using the GroveMD to drive a stepper motor

    # configure it, for this example, we'll assume 200 steps per rev
    myMotorDriver.configStepper(200)

    # set for half a rotation
    myMotorDriver.setStepperSteps(100)

    # let it go - clockwise rotation, 10 RPM speed
    myMotorDriver.enableStepper(upmGrovemd.GroveMD.STEP_DIR_CW, 10)

    time.sleep(3)

    # Now do it backwards...
    myMotorDriver.setStepperSteps(100)
    myMotorDriver.enableStepper(upmGrovemd.GroveMD.STEP_DIR_CCW, 10)

    # now disable
    myMotorDriver.disableStepper()

if __name__ == '__main__':
    main()