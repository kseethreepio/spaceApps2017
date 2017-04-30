# Author: "Mars Home Improvement" Space Apps 2017 Team.

from mhiheatexchanger.sensor import Sensor

ACTIVE_SENSORS = {
	{
		sensor_id: 0,
		sensor_room: "Room_A",
		sensor_name: "Sensor_1",
		temp_sensor_pin: 0
	},
	{
		sensor_id: 3,
		sensor_room: "Room_B",
		sensor_name: "Sensor_1",
		temp_sensor_pin: 3
	},
}

DEBUG = True

class CentralCommand(Object):
	'''Class for the central module that handles incoming requests from sensors,
	and issues commands for opening valves connected to sensors in the system, for 
	heat exchange.

	Future considerations:
		- Handle sensors added/removed on the fly, w/o having to restart system.
		- Expose REST API for receiving requests from sensors, and issuing commands.
	'''

	def __init__(self):
		'''Init method for command module object. This requires an inventory of 
		sensors in the ACTIVE_SENSORS dict.
		'''

		# Generate list of currently-connected sensors
		self.connected_sensors = []
		for sensor in ACTIVE_SENSORS:
			self.connected_sensors.append(Sensor(\
				sensor['sensor_room'], sensor['sensor_name'], sensor['sensor_id'], \
				sensor['temp_sensor_pin']))

		# Now, start the temp check loop on each active sensor
		for 

	@staticmethod
	def receiveRequestFromSensor(self, request):
		return False
