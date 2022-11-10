cmake_minimum_required(VERSION 2.8.3)
project(spot_driver)

## Find catkin and any catkin packages
find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  genmsg
  cv_bridge
  std_msgs
  geometry_msgs
  sensor_msgs
  diagnostic_msgs
  message_generation
)

## Generate messages in the 'msg' folder
add_message_files(
  FILES
  KinematicState.msg
  ImageCapture.msg
  PowerState.msg
  CommsState.msg
  SystemFault.msg
  SystemFaultState.msg
  EStopState.msg
  BehaviorFaultState.msg
  FootState.msg
  RobotState.msg
)
## Generate services in the 'srv' folder
add_service_files(
  FILES
  Stand.srv
  Trajectory.srv
  Velocity.srv
  Stairs.srv
)

include_directories(include ${catkin_INCLUDE_DIRS})

catkin_python_setup()

## Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs
  geometry_msgs
  sensor_msgs
  diagnostic_msgs
)

## Declare a catkin package
catkin_package(
  CATKIN_DEPENDS message_runtime std_msgs geometry_msgs sensor_msgs
)