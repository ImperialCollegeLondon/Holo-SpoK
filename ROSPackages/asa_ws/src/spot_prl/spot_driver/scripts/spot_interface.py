#!/usr/bin/env python3

# Personal Robotics Laboratory - Imperial College London, 2022
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

import argparse
import logging
import math
import sys
import os
import subprocess
import time
import numpy as np

# Bosdyn specific imports
import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
import bosdyn.geometry

from bosdyn.client import math_helpers
from bosdyn.client.image import ImageClient, build_image_request
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.local_grid import LocalGridClient
from bosdyn.api import trajectory_pb2, image_pb2, robot_state_pb2, local_grid_pb2

from bosdyn.client.frame_helpers import get_a_tform_b, get_vision_tform_body, get_odom_tform_body,\
    BODY_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME, VISION_FRAME_NAME, ODOM_FRAME_NAME 

from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from google.protobuf.timestamp_pb2 import Timestamp

# ROS specific imports
import rospy
import diagnostic_msgs.msg
import geometry_msgs.msg
import std_msgs.msg
import sensor_msgs.msg
import visualization_msgs.msg
import spot_driver.msg
import spot_driver.srv

import tf2_ros 

from grid_utils import get_terrain_markers

front_image_sources = ['frontleft_fisheye_image', 'frontright_fisheye_image', 'frontleft_depth', 'frontright_depth']

class DefaultCameraInfo(sensor_msgs.msg.CameraInfo):
    """Blank class extending CameraInfo ROS topic that defaults most parameters"""
    def __init__(self):
        super().__init__()
        self.distortion_model = "plumb_bob"

        self.D.append(0)
        self.D.append(0)
        self.D.append(0)
        self.D.append(0)
        self.D.append(0)

        self.K[1] = 0
        self.K[3] = 0
        self.K[6] = 0
        self.K[7] = 0
        self.K[8] = 1

        self.R[0] = 1
        self.R[1] = 0
        self.R[2] = 0
        self.R[3] = 0
        self.R[4] = 1
        self.R[5] = 0
        self.R[6] = 0
        self.R[7] = 0
        self.R[8] = 1

        self.P[1] = 0
        self.P[3] = 0
        self.P[4] = 0
        self.P[7] = 0
        self.P[8] = 0
        self.P[9] = 0
        self.P[10] = 1
        self.P[11] = 0

class AsyncImageService(AsyncPeriodicQuery):
    """Class to get images at regular intervals.  get_image_from_sources_async query sent to the robot at every tick.  Callback registered to defined callback function.
        Attributes:
            client: The Client to a service on the robot
            logger: Logger object
            rate: Rate (Hz) to trigger the query
            callback: Callback function to call when the results of the query are available
    """
    def __init__(self, client, logger, rate, callback, image_requests):
        super(AsyncImageService, self).__init__("robot_image_service", client, logger,
                                           period_sec=1.0/max(rate, 1.0))
        self._callback = None
        if rate > 0.0:
            self._callback = callback
        self._image_requests = image_requests

    def _start_query(self):
        if self._callback:
            callback_future = self._client.get_image_async(self._image_requests)
            callback_future.add_done_callback(self._callback)
            return callback_future

class SpotInterface:
    '''Callbacks for an instance of a Spot robot'''

    # 0.6 s is the standard duration for cmds in boston dynamics Spot examples
    VELOCITY_CMD_DURATION = 0.6  # [seconds]
    TRAJECTORY_CMD_TIMEOUT = 20.0  # [seconds]
    x_goal_tolerance = 0.05 #[m]
    y_goal_tolerance = 0.05 #[m]
    angle_goal_tolerance = 0.075 #[rad]
    LOGGER = logging.getLogger()

    def __init__(self, config):
        # Ensure interface can ping Spot
        try:
            with open(os.devnull, 'wb') as devnull:
                resp = subprocess.check_call(['ping', '-c', '1', config.hostname], stdout=devnull, stderr=subprocess.STDOUT)
                if resp != 0:
                    print ("ERROR: Cannot detect a Spot with IP: {}.\nMake sure Spot is powered on and on the same network".format(config.hostname))
                    sys.exit()
        except:
            print("ERROR: Cannot detect a Spot with IP: {}.\nMake sure Spot is powered on and on the same network".format(config.hostname))
            sys.exit()

        # Set up SDK
        bosdyn.client.util.setup_logging(config.verbose)
        self.sdk = bosdyn.client.create_standard_sdk('spot_ros_interface_sdk')
        #self.sdk.load_app_token(config.app_token)

        # Create instance of a robot
        try:
            self.robot = self.sdk.create_robot(config.hostname)
            self.robot.authenticate(config.username, config.password)
            self.robot.time_sync.wait_for_sync()
        except bosdyn.client.RpcError as err:
            self.LOGGER.error("Failed to communicate with robot: %s", err)

        # Client to send cmds to Spot
        self.command_client = self.robot.ensure_client(
            RobotCommandClient.default_service_name)

        # Client to request images from Spot
        self.image_client = self.robot.ensure_client(
            ImageClient.default_service_name)

        self.image_source_names = [
            src.name for src in self.image_client.list_image_sources() if "image" in src.name
        ]

        self.depth_image_sources = [
            src.name for src in self.image_client.list_image_sources() if "depth" in src.name
        ]

        # Client to request robot state
        self.robot_state_client = self.robot.ensure_client(
            RobotStateClient.default_service_name)

        # Client to request local occupancy grid
        self.grid_client = self.robot.ensure_client(
            LocalGridClient.default_service_name)
        self.local_grid_types = self.grid_client.get_local_grid_types()

        # Spot requires a software estop to be activated.
        estop_client = self.robot.ensure_client(
            bosdyn.client.estop.EstopClient.default_service_name)
        self.estop_endpoint = bosdyn.client.estop.EstopEndpoint(
            client=estop_client, name='spot_ros_interface', estop_timeout=9.0)
        self.estop_endpoint.force_simple_setup()

        # Only one client at a time can operate a robot.
        self.lease_client = self.robot.ensure_client(
            bosdyn.client.lease.LeaseClient.default_service_name)
        try:
            self.lease = self.lease_client.acquire()
        except bosdyn.client.lease.ResourceAlreadyClaimedError as err:
            print("ERROR: Lease cannot be acquired. Ensure no other client has the lease. Shutting down.")
            print(err)
            sys.exit()
            
        # True for RViz visualization of Spot in 3rd person with occupancy grid
        self.third_person_view = True

        # Power on motors
        self.motors_on = config.motors_on.lower()!="n"
        # Stairs mode
        self.stair_hint = config.stairs_mode.lower()!="n"


        self.logger = logging.getLogger('rosout')

        self._front_image_requests = []
        for source in front_image_sources:
            self._front_image_requests.append(build_image_request(source, image_format=image_pb2.Image.FORMAT_RAW))
        
        self._front_image_task = AsyncImageService(self.image_client, self.logger, rate=10.0, callback=self.FrontImageCB, image_requests=self._front_image_requests)
        self._async_tasks = AsyncTasks([self._front_image_task])
    
    def updateTasks(self):
        """Loop through all periodic tasks and update their data if needed."""
        try:
            self._async_tasks.update()
        except Exception as e:
            print(f"Update tasks failed with error: {str(e)}")
    
    def getImageMsg(self, data):
        """Takes the imag and  camera data and populates the necessary ROS messages
        Args:
            data: Image proto
            spot_wrapper: A SpotWrapper object
        Returns:
            (tuple):
                * Image: message of the image captured
                * CameraInfo: message to define the state and config of the camera that took the image
        """

        image_msg = sensor_msgs.msg.Image()
        local_time = self.robotToLocalTime(data.shot.acquisition_time)
        image_msg.header.stamp = rospy.Time(local_time.seconds, local_time.nanos)
        image_msg.header.frame_id = data.source.name
        image_msg.height = data.shot.image.rows
        image_msg.width = data.shot.image.cols

        # Color/greyscale formats.
        # JPEG format
        if data.shot.image.format == image_pb2.Image.FORMAT_JPEG:
            image_msg.encoding = "rgb8"
            image_msg.is_bigendian = True
            image_msg.step = 3 * data.shot.image.cols
            image_msg.data = data.shot.image.data

        # Uncompressed.  Requires pixel_format.
        if data.shot.image.format == image_pb2.Image.FORMAT_RAW:
            # One byte per pixel.
            if data.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
                image_msg.encoding = "mono8"
                image_msg.is_bigendian = True
                image_msg.step = data.shot.image.cols
                image_msg.data = data.shot.image.data

            # Three bytes per pixel.
            if data.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
                image_msg.encoding = "rgb8"
                image_msg.is_bigendian = True
                image_msg.step = 3 * data.shot.image.cols
                image_msg.data = data.shot.image.data

            # Four bytes per pixel.
            if data.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGBA_U8:
                image_msg.encoding = "rgba8"
                image_msg.is_bigendian = True
                image_msg.step = 4 * data.shot.image.cols
                image_msg.data = data.shot.image.data

            # Little-endian uint16 z-distance from camera (mm).
            if data.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
                image_msg.encoding = "16UC1"
                image_msg.is_bigendian = False
                image_msg.step = 2 * data.shot.image.cols
                image_msg.data = data.shot.image.data

        camera_info_msg = DefaultCameraInfo()
        local_time = self.robotToLocalTime(data.shot.acquisition_time)
        camera_info_msg.header.stamp = rospy.Time(local_time.seconds, local_time.nanos)
        camera_info_msg.header.frame_id = data.source.name
        camera_info_msg.height = data.shot.image.rows
        camera_info_msg.width = data.shot.image.cols

        camera_info_msg.K[0] = data.source.pinhole.intrinsics.focal_length.x
        camera_info_msg.K[2] = data.source.pinhole.intrinsics.principal_point.x
        camera_info_msg.K[4] = data.source.pinhole.intrinsics.focal_length.y
        camera_info_msg.K[5] = data.source.pinhole.intrinsics.principal_point.y

        camera_info_msg.P[0] = data.source.pinhole.intrinsics.focal_length.x
        camera_info_msg.P[2] = data.source.pinhole.intrinsics.principal_point.x
        camera_info_msg.P[5] = data.source.pinhole.intrinsics.focal_length.y
        camera_info_msg.P[6] = data.source.pinhole.intrinsics.principal_point.y

        # Transform from base_link to camera for current img
        body_tform_cam = get_a_tform_b(data.shot.transforms_snapshot,BODY_FRAME_NAME,data.shot.frame_name_image_sensor)
                            
        # Generate camera to body Transform
        body_tform_cam_tf = geometry_msgs.msg.Transform()
        body_tform_cam_tf.translation.x = body_tform_cam.position.x
        body_tform_cam_tf.translation.y = body_tform_cam.position.y
        body_tform_cam_tf.translation.z = body_tform_cam.position.z
        body_tform_cam_tf.rotation.x = body_tform_cam.rotation.x
        body_tform_cam_tf.rotation.y = body_tform_cam.rotation.y
        body_tform_cam_tf.rotation.z = body_tform_cam.rotation.z
        body_tform_cam_tf.rotation.w = body_tform_cam.rotation.w

        camera_transform_stamped_msg = geometry_msgs.msg.TransformStamped()
        local_time = self.robotToLocalTime(data.shot.acquisition_time)
        camera_transform_stamped_msg.header.stamp = rospy.Time(local_time.seconds, local_time.nanos)
        camera_transform_stamped_msg.header.frame_id = "base_link"
        camera_transform_stamped_msg.transform = body_tform_cam_tf
        camera_transform_stamped_msg.child_frame_id = data.source.name

        return image_msg, camera_info_msg, camera_transform_stamped_msg

    def robotToLocalTime(self, timestamp):
        """Takes a timestamp and an estimated skew and return seconds and nano seconds in local time
        Args:
            timestamp: google.protobuf.Timestamp
        Returns:
            google.protobuf.Timestamp
        """

        rtime = Timestamp()

        rtime.seconds = timestamp.seconds - self.time_skew.seconds
        rtime.nanos = timestamp.nanos - self.time_skew.nanos
        if rtime.nanos < 0:
            rtime.nanos = rtime.nanos + 1000000000
            rtime.seconds = rtime.seconds - 1

        # Workaround for timestamps being incomplete
        if rtime.seconds < 0:
            rtime.seconds = 0
            rtime.nanos = 0

        return rtime
    
    @property
    def time_skew(self):
        """Return the time skew between local and spot time"""
        return self.robot.time_sync.endpoint.clock_skew
    
    @property
    def front_images(self):
        """Return latest proto from the _front_image_task"""
        return self._front_image_task.proto


    ### Callback functions ###

    def FrontImageCB(self, results):
        """Callback for when the Spot Wrapper gets new front image data.
        Args:
            results: FutureWrapper object of AsyncPeriodicQuery callback
        """
        data = self.front_images
        if data:
            image_msg0, camera_info_msg0, camera_transform_stamped_msg0 = self.getImageMsg(data[0])
            self.frontleft_image_pub.publish(image_msg0)
            self.frontleft_image_info_pub.publish(camera_info_msg0)
            self.spot_tf_static_broadcaster.sendTransform(camera_transform_stamped_msg0)
            image_msg1, camera_info_msg1, camera_transform_stamped_msg1 = self.getImageMsg(data[1])
            self.frontright_image_pub.publish(image_msg1)
            self.frontright_image_info_pub.publish(camera_info_msg1)
            self.spot_tf_static_broadcaster.sendTransform(camera_transform_stamped_msg1)
            image_msg2, camera_info_msg2, camera_transform_stamped_msg2 = self.getImageMsg(data[2])
            self.frontleft_depth_pub.publish(image_msg2)
            self.frontleft_depth_info_pub.publish(camera_info_msg2)
            self.spot_tf_static_broadcaster.sendTransform(camera_transform_stamped_msg2)
            image_msg3, camera_info_msg3, camera_transform_stamped_msg3 = self.getImageMsg(data[3])
            self.frontright_depth_pub.publish(image_msg3)
            self.frontright_depth_info_pub.publish(camera_info_msg3)
            self.spot_tf_static_broadcaster.sendTransform(camera_transform_stamped_msg3)

    def self_right_cmd_srv(self, stand):
        """ Callback that sends self-right cmd"""
        cmd = RobotCommandBuilder.selfright_command()
        ret = self.command_client.robot_command(cmd)
        rospy.loginfo("Robot self right cmd sent. {}".format(ret))

        return []

    def stand_cmd_srv(self, stand):
        """Callback that sends stand cmd at a given height delta [m] from standard configuration"""

        cmd = RobotCommandBuilder.stand_command(
            body_height=stand.body_pose.translation.z,
            footprint_R_body=self.quat_to_euler(stand.body_pose.rotation)
            )
        ret = self.command_client.robot_command(cmd)
        rospy.loginfo("Robot stand cmd sent. {}".format(ret))

        return []

    def trajectory_cmd_srv(self, trajectory):
        '''
        Callback that specifies waypoint(s) (Point) [m] with a final orientation [rad]

        The name of the frame that trajectory is relative to.
        The trajectory must be expressed in a gravity aligned frame, so either "vision", "odom", or "flat_body".
        Any other provided se2_frame_name will be rejected and the trajectory command will not be exectuted.
        '''
        # TODO: Support other reference frames (currently only VISION ref. frame)

        for pose in trajectory.waypoints.poses:
            x = pose.position.x
            y = pose.position.y
            # Pose heading (yaw) in radians.
            heading = math.atan2(2 * pose.orientation.z * pose.orientation.w + 2 * pose.orientation.x * pose.orientation.y, 1 - 2 * pose.orientation.y**2 - 2 * pose.orientation.z**2)
            frame = VISION_FRAME_NAME

            prms = RobotCommandBuilder.mobility_params(
                body_height=0.0,
                locomotion_hint =1,
                stair_hint = self.stair_hint
            )

            cmd = RobotCommandBuilder.trajectory_command(
                goal_x=x,
                goal_y=y,
                goal_heading=heading,
                frame_name=frame,
                params = prms
            )
            self.command_client.robot_command(lease=None, command=cmd, end_time_secs=time.time() + self.TRAJECTORY_CMD_TIMEOUT)
            
        robot_state = self.get_robot_state()[0].vision_tform_body
        final_pose = geometry_msgs.msg.Pose()
        final_pose.position = robot_state.translation
        final_pose.orientation = robot_state.rotation

        spot_driver.srv.TrajectoryResponse(final_pose)

    def velocity_cmd_srv(self, twist):
        """Callback that sends instantaneous velocity [m/s] commands to Spot"""
        
        v_x = twist.velocity.linear.x
        v_y = twist.velocity.linear.y
        v_rot = twist.velocity.angular.z

        prms = RobotCommandBuilder.mobility_params(
            body_height=0.0,
            locomotion_hint =1,
            stair_hint = self.stair_hint
        )
        
        cmd = RobotCommandBuilder.velocity_command(
            v_x=v_x,
            v_y=v_y,
            v_rot=v_rot,
            params = prms
        )

        self.command_client.robot_command(
            cmd,
            end_time_secs=time.time() + self.VELOCITY_CMD_DURATION
        )
        rospy.loginfo(
            "Robot velocity cmd sent: v_x=${},v_y=${},v_rot${}".format(v_x, v_y, v_rot))
        return []

    def stairs_mode_srv(self, rqst):
        """Stairs mode on/off"""
        self.stair_hint = rqst.enable.data
        return []
    
    ### Helper functions ###

    def block_until_pose_reached(self, cmd, goal):
        """Do not return until goal waypoint is reached, or TRAJECTORY_CMD_TIMEOUT is reached."""
        # TODO: Make trajectory_cmd_timeout part of the service request
        
        self.command_client.robot_command(
            cmd,
            end_time_secs = time.time()+self.TRAJECTORY_CMD_TIMEOUT if self.TRAJECTORY_CMD_TIMEOUT else None
        )

        start_time = time.time()
        current_time = time.time()
        while (not self.is_final_state(goal) and (current_time - start_time < self.TRAJECTORY_CMD_TIMEOUT if self.TRAJECTORY_CMD_TIMEOUT else True)):
            time.sleep(.25)
            current_time = time.time()
        return self.is_final_state(goal)

    def is_final_state(self, goal):
        """Check if the current robot state is within range of the specified position."""
        goal_x=goal[0]
        goal_y=goal[1]
        goal_heading=goal[2]
        robot_state = self.get_robot_state()[0].vision_tform_body
        robot_pose = robot_state.translation
        robot_angle = self.quat_to_euler((robot_state.rotation.x, robot_state.rotation.y,
                                          robot_state.rotation.z, robot_state.rotation.w)).yaw

        x_dist = abs(goal_x - robot_pose.x)
        y_dist = abs(goal_y - robot_pose.y)
        angle = abs(goal_heading - robot_angle)
        if ((x_dist < self.x_goal_tolerance) and (y_dist < self.y_goal_tolerance) and (angle < self.angle_goal_tolerance)):
            return True
        return False

    def quat_to_euler(self, quat):
        """Convert a quaternion to xyz Euler angles."""
        q = [quat.x, quat.y, quat.z, quat.w]
        roll = math.atan2(2 * q[3] * q[0] + q[1] * q[2], 1 - 2 * q[0]**2 + 2 * q[1]**2)
        pitch = math.atan2(2 * q[1] * q[3] - 2 * q[0] * q[2], 1 - 2 * q[1]**2 - 2 * q[2]**2)
        yaw = math.atan2(2 * q[2] * q[3] + 2 * q[0] * q[1], 1 - 2 * q[1]**2 - 2 * q[2]**2)
        return bosdyn.geometry.EulerZXY(yaw=yaw, roll=roll, pitch=pitch)

    # TODO: Unit test the get_state method conversion from pbuf to ROS msg (test repeated fields, etc)
    def get_robot_state(self):
        ''' Returns tuple of kinematic_state, robot_state
            kinematic_state:
                timestamp
                joint_states []
                ko_tform_body
                body_twist_rt_ko
                ground_plane_rt_ko
                vo_tform_body
            robot_state:
                power_state
                battery_states[]
                comms_states[]
                system_fault_state
                estop_states[]
                behavior_fault_state
        '''
        robot_state = self.robot_state_client.get_robot_state()
        rs_msg = spot_driver.msg.RobotState()
        
        ''' PowerState conversion '''
        rs_msg.power_state.header.stamp.secs =  robot_state.power_state.timestamp.seconds
        rs_msg.power_state.header.stamp.nsecs =  robot_state.power_state.timestamp.nanos
        rs_msg.power_state.motor_power_state = robot_state.power_state.motor_power_state #[enum]
        rs_msg.power_state.shore_power_state = robot_state.power_state.shore_power_state #[enum]
        rs_msg.power_state.locomotion_charge_percentage = robot_state.power_state.locomotion_charge_percentage.value #[google.protobuf.DoubleValue]
        rs_msg.power_state.locomotion_estimated_runtime.secs = robot_state.power_state.locomotion_estimated_runtime.seconds #[google.protobuf.Duration]

        ''' BatteryState conversion [repeated field] ''' 
        for battery_state in robot_state.battery_states:
            battery_state_msg = sensor_msgs.msg.BatteryState()

            header = std_msgs.msg.Header()
            header.stamp.secs = battery_state.timestamp.seconds
            header.stamp.nsecs = battery_state.timestamp.nanos
            header.frame_id = battery_state.identifier #[string]

            battery_state_msg.header = header

            battery_state_msg.percentage = battery_state.charge_percentage.value/100 #[double]
            # NOTE: Using battery_state_msg.charge as the estimated runtime in sec
            battery_state_msg.charge = battery_state.estimated_runtime.seconds #[google.protobuf.Duration]
            battery_state_msg.current = battery_state.current.value #[DoubleValue]
            battery_state_msg.voltage = battery_state.voltage.value #[DoubleValue]
            # NOTE: Ignoring battery_state.temperatures for now; no field in BatteryState maps directly to it
            battery_state_msg.power_supply_status = battery_state.status #[enum]

            rs_msg.battery_states.append(battery_state_msg)

        ''' CommsState conversion [repeated field] '''
        for comms_state in robot_state.comms_states:
            comms_state_msg = spot_driver.msg.CommsState()

            comms_state_msg.header.stamp.secs = comms_state.timestamp.seconds #[google.protobuf.Timestamp]
            comms_state_msg.header.stamp.nsecs = comms_state.timestamp.nanos #[google.protobuf.Timestamp]
            comms_state_msg.wifi_mode = comms_state.wifi_state.current_mode #[enum] Note: wifi_state is oneof
            comms_state_msg.essid = comms_state.wifi_state.essid #[string]

            rs_msg.comms_states.append(comms_state_msg)

        ''' SystemFaultState conversion '''
        ### faults is Repeated ###
        for fault in robot_state.system_fault_state.faults:
            system_fault_msg = spot_driver.msg.SystemFault()

            system_fault_msg.header.frame_id = fault.name #[string]
            system_fault_msg.header.stamp.secs = fault.onset_timestamp.seconds #[google.protobuf.Timestamp]
            system_fault_msg.header.stamp.nsecs = fault.onset_timestamp.nanos #[google.protobuf.Timestamp]
            system_fault_msg.duration.secs = fault.duration.seconds #[google.protobuf.Duration]
            system_fault_msg.duration.nsecs = fault.duration.nanos #[google.protobuf.Duration]
            system_fault_msg.code = fault.code #[int32]
            system_fault_msg.uid =  fault.uid #[uint64]
            system_fault_msg.error_message = fault.error_message #[string]
            system_fault_msg.attributes = fault.attributes #[repeated-string]
            system_fault_msg.severity = fault.severity #[enum]

            rs_msg.system_fault_state.faults.append(system_fault_msg)

        ### historical_faults is Repeated ###
        for historical_fault in robot_state.system_fault_state.faults:
            system_fault_msg = spot_driver.msg.SystemFault()

            system_fault_msg.header.frame_id = historical_fault.name #[string]
            system_fault_msg.header.stamp.secs = historical_fault.onset_timestamp.seconds #[google.protobuf.Timestamp]
            system_fault_msg.header.stamp.nsecs = historical_fault.onset_timestamp.nanos #[google.protobuf.Timestamp]
            system_fault_msg.duration.secs = historical_fault.duration.seconds #[google.protobuf.Duration]
            system_fault_msg.duration.nsecs = historical_fault.duration.nanos #[google.protobuf.Duration]
            system_fault_msg.code = historical_fault.code #[int32]
            system_fault_msg.uid =  historical_fault.uid #[uint64]
            system_fault_msg.error_message = historical_fault.error_message #[string]
            system_fault_msg.attributes = historical_fault.attributes #[repeated-string]
            system_fault_msg.severity = historical_fault.severity #[enum]

            rs_msg.system_fault_state.historical_faults.append(system_fault_msg)

        #[map<string,enum>]
        if robot_state.system_fault_state.aggregated:
            for key, value in robot_state.system_fault_state.aggregated.items():
                kv = diagnostic_msgs.msg.KeyValue()
                kv.key = key
                kv.value = value
                rs_msg.system_fault_state.aggregated.append(kv)

        ''' EStopState conversion [repeated field] '''
        for estop_state in robot_state.estop_states:
            estop_msg = spot_driver.msg.EStopState()

            estop_msg.header.stamp.secs = estop_state.timestamp.seconds #[google.protobuf.Timestamp]
            estop_msg.header.stamp.nsecs = estop_state.timestamp.nanos #[google.protobuf.Timestamp]
            estop_msg.header.frame_id = estop_state.name #[string]
            estop_msg.type = estop_state.type #[enum]
            estop_msg.state = estop_state.state #[enum]
            estop_msg.state_description = estop_state.state_description #[string]

            rs_msg.estop_states.append(estop_msg)

        ''' KinematicState conversion '''
        ks_msg = spot_driver.msg.KinematicState()

        ks_msg.header.stamp.secs = robot_state.kinematic_state.acquisition_timestamp.seconds
        ks_msg.header.stamp.nsecs = robot_state.kinematic_state.acquisition_timestamp.nanos

        joint_dict = {"fl.hx": "front_left_hip_x", "fl.hy": "front_left_hip_y", "fl.kn": "front_left_knee", "fr.hx": "front_right_hip_x", 
        "fr.hy": "front_right_hip_y", "fr.kn": "front_right_knee", "hl.hx": "rear_left_hip_x", "hl.hy": "rear_left_hip_y", "hl.kn": "rear_left_knee", 
        "hr.hx": "rear_right_hip_x", "hr.hy": "rear_right_hip_y", "hr.kn": "rear_right_knee"}

        ### joint_states is repeated ###
        js = sensor_msgs.msg.JointState()
        js.header.stamp = ks_msg.header.stamp
        for joint_state in robot_state.kinematic_state.joint_states:
            js.name.append(joint_dict[joint_state.name]) # [string]
            js.position.append(joint_state.position.value) # Note: angle in rad
            js.velocity.append(joint_state.velocity.value) # Note: ang vel
            # NOTE: ang accel. JointState doesn't have accel. Ignoring joint_state.acceleration for now.
            js.effort.append(joint_state.load.value) # Note: Torque in N-m

        ks_msg.joint_states = js

        # SE3Pose representing transform of Spot's Body frame relative to the inertial Vision frame
        vision_tform_body = get_vision_tform_body(robot_state.kinematic_state.transforms_snapshot)

        ks_msg.vision_tform_body.translation.x = vision_tform_body.x
        ks_msg.vision_tform_body.translation.y = vision_tform_body.y
        ks_msg.vision_tform_body.translation.z = vision_tform_body.z

        ks_msg.vision_tform_body.rotation.x = vision_tform_body.rot.x
        ks_msg.vision_tform_body.rotation.y = vision_tform_body.rot.y
        ks_msg.vision_tform_body.rotation.z = vision_tform_body.rot.z
        ks_msg.vision_tform_body.rotation.w = vision_tform_body.rot.w

        # odom_tform_body: SE3Pose representing transform of Spot's Body frame relative to the odometry frame
        odom_tform_body = get_odom_tform_body(robot_state.kinematic_state.transforms_snapshot)

        ks_msg.odom_tform_body.translation.x = odom_tform_body.x
        ks_msg.odom_tform_body.translation.y = odom_tform_body.y
        ks_msg.odom_tform_body.translation.z = odom_tform_body.z

        ks_msg.odom_tform_body.rotation.x = odom_tform_body.rot.x
        ks_msg.odom_tform_body.rotation.y = odom_tform_body.rot.y
        ks_msg.odom_tform_body.rotation.z = odom_tform_body.rot.z
        ks_msg.odom_tform_body.rotation.w = odom_tform_body.rot.w

        ''' velocity_of_body_in_vision '''
        ks_msg.velocity_of_body_in_vision.linear.x = robot_state.kinematic_state.velocity_of_body_in_vision.linear.x
        ks_msg.velocity_of_body_in_vision.linear.y = robot_state.kinematic_state.velocity_of_body_in_vision.linear.y
        ks_msg.velocity_of_body_in_vision.linear.z = robot_state.kinematic_state.velocity_of_body_in_vision.linear.z

        ks_msg.velocity_of_body_in_vision.angular.x = robot_state.kinematic_state.velocity_of_body_in_vision.angular.x
        ks_msg.velocity_of_body_in_vision.angular.y = robot_state.kinematic_state.velocity_of_body_in_vision.angular.y
        ks_msg.velocity_of_body_in_vision.angular.z = robot_state.kinematic_state.velocity_of_body_in_vision.angular.z

        ''' velocity_of_body_in_odom '''

        ks_msg.velocity_of_body_in_odom.linear.x = robot_state.kinematic_state.velocity_of_body_in_odom.linear.x
        ks_msg.velocity_of_body_in_odom.linear.y = robot_state.kinematic_state.velocity_of_body_in_odom.linear.y
        ks_msg.velocity_of_body_in_odom.linear.z = robot_state.kinematic_state.velocity_of_body_in_odom.linear.z

        ks_msg.velocity_of_body_in_odom.angular.x = robot_state.kinematic_state.velocity_of_body_in_odom.angular.x
        ks_msg.velocity_of_body_in_odom.angular.y = robot_state.kinematic_state.velocity_of_body_in_odom.angular.y
        ks_msg.velocity_of_body_in_odom.angular.z = robot_state.kinematic_state.velocity_of_body_in_odom.angular.z


        ### BehaviorFaultState conversion
        '''faults is repeated'''
        for fault in robot_state.behavior_fault_state.faults:
            behaviour_fault_state_msg = spot_driver.msg.BehaviorFaultState()

            behaviour_fault_state_msg.header.frame_id = fault.behavior_fault_id #[uint32]
            behaviour_fault_state_msg.header.stamp.secs = fault.onset_timestamp.seconds #[google.protobuf.Timestamp]
            behaviour_fault_state_msg.header.stamp.nsecs = fault.onset_timestamp.nanos #[google.protobuf.Timestamp]
            behaviour_fault_state_msg.cause = fault.cause #[enum]
            behaviour_fault_state_msg.status = fault.status #[enum]

            rs_msg.behavior_fault_states.append(behaviour_fault_state_msg)

        ### FootState conversion [repeated]
        for foot_state in robot_state.foot_state:
            foot_state_msg = spot_driver.msg.FootState()

            foot_state_msg.foot_position_rt_body.x = foot_state.foot_position_rt_body.x #[double]
            foot_state_msg.foot_position_rt_body.y = foot_state.foot_position_rt_body.y #[double]
            foot_state_msg.foot_position_rt_body.z = foot_state.foot_position_rt_body.z #[double]
            foot_state_msg.contact = foot_state.contact #[enum]

            rs_msg.foot_states.append(foot_state_msg)
        

        return ks_msg, rs_msg  #kinematic state message, robot state message
    

    def start_spot_ros_interface(self):

        # ROS Node initialization
        rospy.init_node('spot_ros_interface_py')
        rate = rospy.Rate(200)  # Update at 200 Hz

        # Each service will handle a specific command to Spot instance
        rospy.Service("self_right_cmd", spot_driver.srv.Stand, self.self_right_cmd_srv)
        rospy.Service("stand_cmd", spot_driver.srv.Stand, self.stand_cmd_srv)
        rospy.Service("trajectory_cmd", spot_driver.srv.Trajectory, self.trajectory_cmd_srv)
        rospy.Service("velocity_cmd", spot_driver.srv.Velocity, self.velocity_cmd_srv)
        rospy.Service("stairs_mode", spot_driver.srv.Stairs, self.stairs_mode_srv)

        # Single image publisher will publish all images from all Spot cameras
        kinematic_state_pub = rospy.Publisher(
            "kinematic_state", spot_driver.msg.KinematicState, queue_size=20)
        robot_state_pub = rospy.Publisher(
            "robot_state", spot_driver.msg.RobotState, queue_size=20)
        occupancy_grid_pub = rospy.Publisher(
            "occupancy_grid", visualization_msgs.msg.Marker, queue_size=20)

        # Publish tf2 from visual odometry frame to Spot's base link
        spot_tf_broadcaster = tf2_ros.TransformBroadcaster()

        # Publish static tf2 from Spot's base link to front-left camera
        self.spot_tf_static_broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Images #
        self.frontleft_image_pub = rospy.Publisher('camera/frontleft/image', sensor_msgs.msg.Image, queue_size=10)
        self.frontright_image_pub = rospy.Publisher('camera/frontright/image', sensor_msgs.msg.Image, queue_size=10)
        # Depth #
        self.frontleft_depth_pub = rospy.Publisher('depth/frontleft/image', sensor_msgs.msg.Image, queue_size=10)
        self.frontright_depth_pub = rospy.Publisher('depth/frontright/image', sensor_msgs.msg.Image, queue_size=10)

        # Image Camera Info #
        self.frontleft_image_info_pub = rospy.Publisher('camera/frontleft/camera_info', sensor_msgs.msg.CameraInfo, queue_size=10)
        self.frontright_image_info_pub = rospy.Publisher('camera/frontright/camera_info', sensor_msgs.msg.CameraInfo, queue_size=10)
        # Depth Camera Info #
        self.frontleft_depth_info_pub = rospy.Publisher('depth/frontleft/camera_info', sensor_msgs.msg.CameraInfo, queue_size=10)
        self.frontright_depth_info_pub = rospy.Publisher('depth/frontright/camera_info', sensor_msgs.msg.CameraInfo, queue_size=10)

        # For RViz 3rd person POV visualization
        if self.third_person_view:
            joint_state_pub = rospy.Publisher(
                "joint_state_from_spot", sensor_msgs.msg.JointState, queue_size=20)

        try:
            with bosdyn.client.lease.LeaseKeepAlive(self.lease_client), bosdyn.client.estop.EstopKeepAlive(
                    self.estop_endpoint):
                rospy.loginfo("Acquired lease")
                if self.motors_on:
                    rospy.loginfo("Powering on robot... This may take a several seconds.")
                    self.robot.power_on(timeout_sec=20)
                    assert self.robot.is_powered_on(), "Robot power on failed."
                    rospy.loginfo("Robot powered on.")
                else:
                    rospy.loginfo("Not powering on robot, continuing")

                while not rospy.is_shutdown():
                    ''' Publish Robot State'''
                    kinematic_state, robot_state = self.get_robot_state()

                    kinematic_state_pub.publish(kinematic_state)
                    robot_state_pub.publish(robot_state)
                    
                    # Publish tf2 from the fixed vision_odometry_frame to the Spot's base_link
                    t = geometry_msgs.msg.TransformStamped()
                    t.header.stamp = rospy.Time.now()
                    t.header.frame_id = "vision_odometry_frame"
                    t.child_frame_id = "base_link"
                    t.transform.translation.x = kinematic_state.vision_tform_body.translation.x
                    t.transform.translation.y = kinematic_state.vision_tform_body.translation.y
                    t.transform.translation.z = kinematic_state.vision_tform_body.translation.z
                    t.transform.rotation.x = kinematic_state.vision_tform_body.rotation.x
                    t.transform.rotation.y = kinematic_state.vision_tform_body.rotation.y
                    t.transform.rotation.z = kinematic_state.vision_tform_body.rotation.z
                    t.transform.rotation.w = kinematic_state.vision_tform_body.rotation.w
                    spot_tf_broadcaster.sendTransform(t)

                    if self.third_person_view:
                        joint_state_pub.publish(kinematic_state.joint_states)

                    ''' Publish Images'''
                    self.updateTasks()
                    
                    ''' Publish occupancy grid'''
                    if occupancy_grid_pub.get_num_connections() > 0:
                        local_grid_proto = self.grid_client.get_local_grids(['terrain'])
                        markers = get_terrain_markers(local_grid_proto)
                        occupancy_grid_pub.publish(markers)

                    rospy.logdebug("Looping...")
                    rate.sleep()

        finally:
            # If we successfully acquired a lease, return it.
            self.lease_client.return_lease(self.lease)

if __name__ == '__main__':
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--motors_on', help='Power on motors [Y/n]', default="Y")
    parser.add_argument('--stairs_mode', help='Stairs mode [Y/n]', default="n")
    options, unknown = parser.parse_known_args(sys.argv[1:])
    print(unknown)

    try:
        robot = SpotInterface(options)
        robot.start_spot_ros_interface()
    except rospy.ROSInterruptException:
        pass
