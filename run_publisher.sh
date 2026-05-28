#!/bin/bash
source ~/ros_ws/devel/setup.bash
source /home/enabled/.pyenv/versions/er_data_publisher/bin/activate
rostopic echo /er/system/status | /home/enabled/.pyenv/versions/er_data_publisher/bin/python /home/enabled/repos/er_data_publisher/battery_to_mqtt.py
