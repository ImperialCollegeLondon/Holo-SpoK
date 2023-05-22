#!/usr/bin/env python3

# Personal Robotics Laboratory - Imperial College London, 2022
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

import rospy
import geometry_msgs.msg
import std_msgs.msg
import sensor_msgs.msg
import spot_driver.msg
import spot_driver.srv

import argparse
import time
import math
import readchar
import sys
import os


line='\u2500'
instructions="\n\
\u250C{} SPOT KEYBOARD TELEOP {}\u2510 \n\
\u2502                            \u2502\n\
\u2502     wasd - Move            \u2502\n\
\u2502     qe - Turn              \u2502\n\
\u2502     r - Self-right         \u2502\n\
\u2502     j - Height up          \u2502\n\
\u2502     o - Stairs on          \u2502\n\
\u2502     p - Stairs off         \u2502\n\
\u2502     k - Height down        \u2502\n\
\u2502                            \u2502\n\
\u2502     SPACE - E-Stop (TODO)  \u2502\n\
\u2502     Q - Quit               \u2502\n\
\u2502                            \u2502\n\
\u2514{}\u2518\
".format(line*3,line*3,line*28)

# Get size of terminal window
rows, columns = os.popen('stty size', 'r').read().split()


class keyboard_teleop:

    def __init__(self, config):

        self.lin_vel = float(config.lin_vel)
        self.ang_vel = float(config.ang_vel)
        self.height_up = float(config.height_up)
        self.height_down = float(config.height_down)

        rospy.init_node('keyboard_teleop')
        self.rate = rospy.Rate(60)

        # Define service proxies
        self.self_right_srv_pub = rospy.ServiceProxy("self_right_cmd", spot_driver.srv.Stand)
        self.stand_srv_pub = rospy.ServiceProxy("stand_cmd", spot_driver.srv.Stand)
        self.vel_srv_pub = rospy.ServiceProxy("velocity_cmd", spot_driver.srv.Velocity)
        self.stairs_mode_srv_pub = rospy.ServiceProxy("stairs_mode", spot_driver.srv.Stairs)

        # Define service requests
        self.self_right_srv_req = spot_driver.srv.StandRequest()
        self.stand_srv_req = spot_driver.srv.StandRequest()
        self.vel_srv_req = spot_driver.srv.VelocityRequest()
        self.stairs_mode_srv_req = spot_driver.srv.StairsRequest()

        print(instructions)

    def self_right_service(self, key):
        tf = geometry_msgs.msg.Transform()

        self.self_right_srv_req.body_pose.translation = tf.translation
        self.self_right_srv_req.body_pose.rotation = tf.rotation

        try:
            rospy.wait_for_service("self_right_cmd", timeout=2.0)
            self.self_right_srv_pub(self.self_right_srv_req)
        except rospy.ServiceException as e:
            print("Service call failed: %s"%e)


    def stand_service(self, key):
        tf = geometry_msgs.msg.Transform()

        if key=='j':
            tf.translation.z = self.height_up
        elif key=='k':
            tf.translation.z = self.height_down

        self.stand_srv_req.body_pose.translation = tf.translation
        self.stand_srv_req.body_pose.rotation = tf.rotation

        try:
            rospy.wait_for_service("stand_cmd", timeout=2.0)
            self.stand_srv_pub(self.stand_srv_req)
        except rospy.ServiceException as e:
            print("Service call failed: %s"%e)

    def vel_service(self, key):
        twist = geometry_msgs.msg.Twist()

        if key=='w':
            twist.linear.x = self.lin_vel
        elif key=='a':
            twist.linear.y = self.lin_vel
        elif key=='s':
            twist.linear.x = -1*self.lin_vel
        elif key=='d':
            twist.linear.y = -1*self.lin_vel
        elif key=='q':
            twist.angular.z = self.ang_vel
        elif key=='e':
            twist.angular.z = -1*self.ang_vel

        self.vel_srv_req.velocity.linear = twist.linear
        self.vel_srv_req.velocity.angular = twist.angular

        try:
            rospy.wait_for_service("velocity_cmd", timeout=2.0)
            self.vel_srv_pub(self.vel_srv_req)
        except rospy.ServiceException as e:
            print("Service call failed: %s"%e, end='')

    def stairs_mode_service(self, key):
        flag = std_msgs.msg.Bool()
        if key == "o":
            flag.data = True
        if key == "p":
            flag.data = False
        self.stairs_mode_srv_req.enable = flag

        try:
            rospy.wait_for_service("stairs_mode", timeout=2.0)
            self.stairs_mode_srv_pub(self.stairs_mode_srv_req)
        except rospy.ServiceException as e:
            print("Service call failed: %s"%e, end='')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--lin_vel', help='Define the linear velocity at which Spot will move in m/s', default="0.5")
    parser.add_argument('--ang_vel', help='Define the angular velocity at which Spot will move in rad/s', default="0.5")
    parser.add_argument('--height_up', help='Height, meters, to stand at relative to a nominal stand height ', default="1.0")
    parser.add_argument('--height_down', help='Height, meters, to stand at relative to a nominal stand height ', default="-1.0")
    
    options, unknown = parser.parse_known_args(sys.argv[1:])
    print(unknown)
    
    keyboard_teleop_ros = keyboard_teleop(options) 
    
    while not rospy.is_shutdown():
        key = readchar.readkey()
        print('{}\rKey pressed: {}\r'.format(' '*int(columns), key), end="")

        if key=="Q":
            sys.exit()
        if key in 'wasdqe':
            keyboard_teleop_ros.vel_service(key)
        elif key in 'jk':
            keyboard_teleop_ros.stand_service(key)
        elif key in 'r':
            keyboard_teleop_ros.self_right_service(key)
        elif key in 'op':
            keyboard_teleop_ros.stairs_mode_service(key)


        keyboard_teleop_ros.rate.sleep()
