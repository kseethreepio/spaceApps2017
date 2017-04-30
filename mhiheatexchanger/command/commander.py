# Author: "Mars Home Improvement" Space Apps 2017 Team.

import time, os, sys
sys.path.append(os.getcwd())  # Workaround for import errors for MHI module

from mhiheatexchanger.sensor.sensor import Sensor, DEBUG, \
	CENTRAL_CMD_MESSAGE_COLD, CENTRAL_CMD_MESSAGE_HOT, CENTRAL_CMD_MESSAGE_HAPPY

ACTIVE_SENSORS = [
	{
		'sensor_id': 0,
		'sensor_room': "Room_A",
		'sensor_name': "Sensor_1",
		'temp_sensor_pin': 0
	},
	{
		'sensor_id': 1,
		'sensor_room': "Room_B",
		'sensor_name': "Sensor_1",
		'temp_sensor_pin': 3
	}
]

ALERT_QUEUE_CHECK_PULSE = 5  # Interval (s) that central module checks for sensor alerts

# Console message strings
ALERT_SENSOR_HOT = "Sensor {0} too hot. Searching for cooler area..."
ALERT_SENSOR_COLD = "Sensor {0} too cold. Searching for warmer area..."
ALERT_FOUND_HELPER_SENSOR = "Sensor {0} to the rescue. Exchanging heat..."
ALERT_CLOSING_HELPER_VALVE = "Sensor {0} temp is now nominal. Closing sensor {1} valve..."
ALERT_CHECK_FOR_MORE  = "Checking for more alerts..."
ALERT_DONE_PROCESSING_QUEUE = "Alert queue has been fully processed."
NO_WORK_MSG = "Queue empty: No work to do."
SHUTDOWN_MSG = "Shutting down command center..."

SPACE_APPS_DEMO_VIRTUAL_SENSOR_ID = 1

class MissionControl(object):
	'''Class for the central module that handles incoming alerts from sensors,
	and issues commands for opening valves connected to sensors in the system, for 
	heat exchange.

	Future considerations:
		- Handle sensors added/removed on the fly, w/o having to restart system.
		- Expose REST API for receiving alerts from sensors, and issuing commands.
	'''

	def __init__(self):
		'''Init method for command module object. This requires an inventory of 
		sensors in the ACTIVE_SENSORS dict.
		'''

		self.alert_queue = []  # List tracking alerts from sensors
		self.favor_ledger = {}  # Dict tracking which sensors are currently helping others

		# Generate list of currently-connected sensors
		self.connected_sensors = []
		for sensor in ACTIVE_SENSORS:
			# Override for Space Apps 2017 demo on single Edison box (Sensor ID 1 
			# is a 'virtual' sensor module -- it only has a dedicated temp sensor, 
			# no LCD or stepper motor)
			if sensor['sensor_id'] == SPACE_APPS_DEMO_VIRTUAL_SENSOR_ID:
				self.connected_sensors.append(Sensor(self, \
					sensor['sensor_room'], sensor['sensor_name'], \
					sensor['sensor_id'], sensor['temp_sensor_pin'], \
					temp_sensor_only=True))			

			# Otherwise, set up as a sensor module matching the HW schematic
			else:
				self.connected_sensors.append(Sensor(self, \
					sensor['sensor_room'], sensor['sensor_name'], \
					sensor['sensor_id'], sensor['temp_sensor_pin']))

		# Now, start the temp check loop on each active sensor
		for active_sensor in self.connected_sensors:
			if DEBUG:
				active_sensor.runSensorTest()
			else:
				active_sensor.startSensor()

	@staticmethod
	def receiveAlertFromSensor(self, alert):
		'''Receives alerts from sensors when they pass the upper or lower temp
		threshold. Possible future improvement: create separate thread for 
		processAlertQueue() call.
		'''

		self.alert_queue.append(alert)
		self.processAlertQueue()

		return True

	def sendCommandToSensor(self, sensor, command):
		'''Sends command/orders to a given sensor.'''

		sensor.respondToMissionControl(sensor, command)

		return True

	def closeAssistingSensorValves(self, sensor_to_help):
		if sensor_to_help.sensor_id in self.favor_ledger.keys():
			if len(self.favor_ledger[sensor_to_help.sensor_id]) > 0:
				assisting_sensor = self.favor_ledger[sensor_to_help.sensor_id].pop(0)
				print(ALERT_CLOSING_HELPER_VALVE.\
					format(sensor_to_help.sensor_id, assisting_sensor.sensor_id))
				self.sendCommandToSensor(assisting_sensor, 'close_valve')

				if len(self.favor_ledger[sensor_to_help.sensor_id]) > 0:
					self.closeAssistingSensorValves(sensor_to_help)

		return True

	def checkAlertQueue(self):
		'''Method for checking the alert queue on demand.'''

		if len(self.alert_queue) > 0:
			self.processAlertQueue()
			return True
		else:
			return False

	def processAlertQueue(self):
		'''Goes through queue of alerts from sensors, and decides what action
		to take. Results in calls to self.sendCommandToSensor().

		Many possible future improvements in terms of algorithms that could be
		used to optimize the heat exchange between hot/cold sensor areas.
		'''

		if len(self.alert_queue) == 0:
			print(NO_WORK_MSG)

		elif len(self.alert_queue) > 0:
			alert_to_process = self.alert_queue.pop(0)
			print("Processing sensor alert...")
			sensor_to_help = alert_to_process['sensor']
			sensor_ask = alert_to_process['signal']
			sensor_temp_c = sensor_to_help.latest_temp_c

			if sensor_ask == CENTRAL_CMD_MESSAGE_HAPPY:
				print()
				self.closeAssistingSensorValves(sensor_to_help)
				return True

			# If the sensor temp is too high, find first sensor with lower temp
			elif sensor_ask == CENTRAL_CMD_MESSAGE_HOT:
				print(ALERT_SENSOR_HOT.format(sensor_to_help.sensor_id))
				for active_sensor in self.connected_sensors:
					# Skip the current sensor being helped
					if active_sensor.sensor_id == sensor_to_help.sensor_id:
						active_sensor = None
						pass
					else:
						if active_sensor.latest_temp_c < sensor_temp_c:
							print(ALERT_FOUND_HELPER_SENSOR.format(active_sensor.sensor_id))
							self.sendCommandToSensor(sensor_to_help, 'open_valve')
							self.sendCommandToSensor(active_sensor, 'open_valve')

						else:
							active_sensor = None

			# Else if sensor temp is too low, find sensor with higher temp
			elif sensor_ask == CENTRAL_CMD_MESSAGE_COLD:
				print(ALERT_SENSOR_COLD.format(sensor_to_help.sensor_id))
				for active_sensor in self.connected_sensors:
					# Skip the current sensor being helped
					if active_sensor.sensor_id == sensor_to_help.sensor_id:
						active_sensor = None
						pass
					else:
						if active_sensor.latest_temp_c > sensor_temp_c:
							print(ALERT_FOUND_HELPER_SENSOR.format(active_sensor.sensor_id))
							self.sendCommandToSensor(sensor_to_help, 'open_valve')
							self.sendCommandToSensor(active_sensor, 'open_valve')

						else:
							active_sensor = None

			if active_sensor:  # If a sensor helped out, update the 'sensor IOU' ledger
				if sensor_to_help.sensor_id in self.favor_ledger.keys():
					sensors_curr_helping = self.favor_ledger[sensor_to_help.sensor_id]		
					if active_sensor.sensor_id not in sensors_curr_helping:
						self.favor_ledger[sensor_to_help.sensor_id].append(active_sensor.sensor_id)

				else:
					self.favor_ledger[sensor_to_help.sensor_id] = [active_sensor.sensor_id]

			print(ALERT_CHECK_FOR_MORE)
			if len(alert_to_process) > 0:  # Check for more alerts to process
				self.processAlertQueue()
			else:
				print(ALERT_DONE_PROCESSING_QUEUE)
				return True

def main():
	'''Main loop for executing command center. To quit, just kill the process
	(ctrl+c).
	'''

	houston = MissionControl()

	try:	
		while True:
			work_to_do = houston.checkAlertQueue()
			if not work_to_do:
				print(NO_WORK_MSG)
				time.sleep(ALERT_QUEUE_CHECK_PULSE)

	except KeyboardInterrupt:
		print(SHUTDOWN_MSG)


if __name__ == '__main__':
	main()
