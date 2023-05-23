# Personal Robotics Laboratory - Imperial College London, 2022
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

THIS_FILE := $(lastword $(MAKEFILE_LIST))

.PHONY: help .pull .build .catkin_build start body_driver keyboard description colocalisation anchor_id stop

help:			## Show this help
	@echo 'Usage: make [target]'
	@echo
	@echo 'Targets:'
	@echo
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

default:		## Clone dependencies, build Docker image and catkin workspace
	@$(MAKE) -s .pull
	@$(MAKE) -s .build
	@$(MAKE) -s .catkin_build

.pull:			## Clone dependencies
	git -C ${PWD}/asa_ws/src clone https://github.com/ImperialCollegeLondon/catkin_simple.git
	git -C ${PWD}/asa_ws/src clone https://github.com/ImperialCollegeLondon/azure_spatial_anchors_ros.git

.build:			## Build Docker image
	docker build --tag=holospot .

.catkin_build:		## Build catkin workspace
	docker run --detach --rm -v ${PWD}/asa_ws:/asa_ws:rw --name holospot holospot bash -c "source /opt/ros/noetic/setup.bash; roscore"
	@sleep 5
	@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; cd /asa_ws; catkin config --init --merge-devel --cmake-args -DCMAKE_BUILD_TYPE=Release; catkin build"
	@$(MAKE) -s -f $(THIS_FILE) stop

start:			## Start Docker image and roscore
	@xhost +si:localuser:root >> /dev/null
	@docker run --detach --rm --net host --privileged -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v ${PWD}/asa_ws:/asa_ws:rw --name holospot holospot bash -c "source /opt/ros/noetic/setup.bash; source /catkin_ws/devel/setup.bash; roscore"
	@sleep 5

body_driver:		## Start Docker image, roscore and launche Spot ROS interface
body_driver: start
	-@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; source /asa_ws/devel/setup.bash; roslaunch spot_driver spot_interface.launch motors_on:=n stairs_mode:=Y"
	@$(MAKE) -s -f $(THIS_FILE) stop  # this shouldn't be reached from above, it should stop it but just in case, we'll cleanly exit

keyboard:		## Start keyboard node; body_driver has to be running in a separate terminal
	@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; source /asa_ws/devel/setup.bash; roslaunch spot_driver keyboard.launch"

description:		## Visualise Spot in Rviz; body_driver has to be running in a separate terminal
	@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; source /asa_ws/devel/setup.bash; roslaunch spot_description robot_model.launch"

anchor_id:		## Subscribe to the topic that publishes the anchor id of the anchor created using the HoloLens; body_driver has to be running in a separate terminal
	@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; source /asa_ws/devel/setup.bash; rostopic echo /hololens/anchor_id"

colocalisation:		## Ask Spot to find anchors created with the HoloLens, you need to provide the anchor id obtained using the previous target; body_driver has to be running in a separate terminal
	@docker exec -it holospot bash -c "source /opt/ros/noetic/setup.bash; source /asa_ws/devel/setup.bash; roslaunch holo_spot_prl spot_asa_ros.launch"

stop:			## Stop Docker container
	@docker stop holospot >> /dev/null