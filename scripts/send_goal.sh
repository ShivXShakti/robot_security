#!/bin/bash

source /opt/ros/humble/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 run robot_security e_send_goal

