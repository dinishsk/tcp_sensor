1. - Copy the package to the workspace (sensor, sensor_interfaces)
   - Colcon build
   - Source the workspace
   
	ros2 run sensor sensor --ros-args -p interval:=1000
	
     Note: The interval parameter is optional and its Default value is 1000ms

2. The data that is transferred from sensor to controllers are decoded and published through the follwing topics.
   	Name         		Topic Type
	supply_voltage		example_interfaces/msg/UInt16
	env_temp		example_interfaces/msg/Int16
	yaw			example_interfaces/msg/Int16
	pitch			example_interfaces/msg/Int16
	roll			example_interfaces/msg/Int16

3. The sensor can be started by calling the service "Start"
	Type: sensor_interfaces/srv/Start
	Interface prototype: "{interval: 1000}"
   
   The sensor can be stoped by calling the service "Stop"
   	Type: sensor_interfaces/srv/Stop
   	Interface prototype: "{}"	
