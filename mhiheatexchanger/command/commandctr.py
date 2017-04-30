# Author: "Mars Home Improvement" Space Apps 2017 Team.

import time

from mhiheatexchanger.sensor.sensor import Sensor,\
	CENTRAL_CMD_MESSAGE_COLD, CENTRAL_CMD_MESSAGE_HOT

ACTIVE_SENSORS = {
	{
		sensor_id: 0,
		sensor_room: "Room_A",
		sensor_name: "Sensor_1",
		temp_sensor_pin: 0
	},
	{
		sensor_id: 1,
		sensor_room: "Room_B",
		sensor_name: "Sensor_1",
		temp_sensor_pin: 3
	},
}

VALVE_TRANS_BACKOFF = 1  # Num seconds to wait before checking again whether valves have opened/closed

ALERT_SENSOR_HOT = "Sensor {0} too hot. Searching for cooler area..."
ALERT_SENSOR_COLD = "Sensor {0} too cold. Searching for warmer area..."
ALERT_FOUND_HELPER_SENSOR = "Sensor {0} to the rescue. Exchanging heat..."
ALERT_CHECK_FOR_MORE  = "Checking for more alerts..."
ALERT_DONE_PROCESSING_QUEUE = "Alert queue has been fully processed."

SPACE_APPS_DEMO_VIRTUAL_SENSOR_ID = 1

class CentralCommand(Object):
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
				self.connected_sensors.append(Sensor(\
					sensor['sensor_room'], sensor['sensor_name'], \
					sensor['sensor_id'], sensor['temp_sensor_pin'], \
					temp_sensor_only=True))			

			# Otherwise, set up as a sensor module matching the HW schematic
			else:
				self.connected_sensors.append(Sensor(\
					sensor['sensor_room'], sensor['sensor_name'], \
					sensor['sensor_id'], sensor['temp_sensor_pin']))

		# Now, start the temp check loop on each active sensor
		for active_sensor in connected_sensors:
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

		sensor.respondToCentralCommand(command)

		return True

	def processAlertQueue(self):
		'''Goes through queue of alerts from sensors, and decides what action
		to take. Results in calls to self.sendCommandToSensor().

		Many possible future improvements in terms of algorithms that could be
		used to optimize the heat exchange between hot/cold sensor areas. Also,
		add a max wait period for VALVE_TRANS_BACKOFF backoffs.
		'''

		alert_to_process = self.alert_queue.pop(0)
		print("Processing sensor alert...")
		sensor_to_help = alert_to_process['sensor']
		sensor_ask = alert_to_process['signal']
		sensor_temp_c = sensor_to_help.latest_temp_c

		# If the sensor temp is too high, find first sensor with lower temp
		if sensor_ask == CENTRAL_CMD_MESSAGE_HOT:
			print(ALERT_SENSOR_HOT.format(sensor_to_help['sensor_id']))
			for active_sensor in self.connected_sensors:
				# Skip the current sensor being helped
				if active_sensor.sensor_id == sensor_to_help.sensor_id:
					active_sensor = None
					pass
				else:
					if active_sensor.latest_temp_c < sensor_temp_c:
						print(ALERT_FOUND_HELPER_SENSOR.format(active_sensor['sensor_id']))
						sendCommandToSensor(sensor_to_help, 'open_valve')
						sendCommandToSensor(active_sensor, 'open_valve')

						# Wait till valves confirmed open before proceeding
						if not (sensor_to_help.valve_open and active_sensor.valve_open):
							time.sleep(VALVE_TRANS_BACKOFF)

					else:
						active_sensor = None

		# Else if sensor temp is too low, find sensor with higher temp
		elif sensor_ask == CENTRAL_CMD_MESSAGE_COLD:
			print(ALERT_SENSOR_COLD.format(sensor_to_help['sensor_id']))
			for active_sensor in self.connected_sensors:
				# Skip the current sensor being helped
				if active_sensor.sensor_id == sensor_to_help.sensor_id:
					active_sensor = None
					pass
				else:
					if active_sensor.latest_temp_c > sensor_temp_c:
						print(ALERT_FOUND_HELPER_SENSOR.format(active_sensor['sensor_id']))
						sendCommandToSensor(sensor_to_help, 'open_valve')
						sendCommandToSensor(active_sensor, 'open_valve')

						# Wait till valves confirmed open before proceeding
						if not (sensor_to_help.valve_open and active_sensor.valve_open):
							time.sleep(VALVE_TRANS_BACKOFF)

					else:
						active_sensor = None

		if active_sensor:  # If a sensor helped out, update the 'sensor IOU' ledger
			try:
				sensors_curr_helping = self.favor_ledger[sensor_to_help.sensor_id]
				if active_sensor.sensor_id not in sensors_curr_helping:
					self.favor_ledger[sensor_to_help.sensor_id].append(active_sensor.sensor_id)

			except KeyError:
				self.favor_ledger[sensor_to_help.sensor_id] = [active_sensor.sensor_id]

		print(ALERT_CHECK_FOR_MORE)
		if len(alert_to_process) > 0:  # Check for more alerts to process
			self.processAlertQueue()
		else:
			print(ALERT_DONE_PROCESSING_QUEUE)
			return True
