#! /usr/bin/env python3

# Personal Robotics Laboratory - Imperial College London, 2022
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

import rospy

import spot_driver.srv
from geometry_msgs.msg import PoseStamped, PoseArray


input_topic_name = '/hololens/goal_pose'

class HoloSpot():

    def __init__(self):

        # Define service proxies
        self.trajectory_srv_pub = rospy.ServiceProxy("trajectory_cmd", spot_driver.srv.Trajectory)
        # Define service requests
        self.trajectory_srv_req = spot_driver.srv.TrajectoryRequest()

        self.goal_pose_subscriber = rospy.Subscriber(input_topic_name, PoseStamped, self.callback, queue_size=1)
    
    def callback(self, message):

        waypoints = PoseArray()
        waypoints.header.stamp = rospy.Time.now()
        waypoints.header.frame_id = message.header.frame_id
        waypoints.poses.append(message.pose)

        self.trajectory_srv_req.waypoints = waypoints

        try:
            rospy.wait_for_service("trajectory_cmd", timeout=2.0)
            self.trajectory_srv_pub(self.trajectory_srv_req)
        except rospy.ServiceException as e:
            print("Service call failed: %s"%e)


if __name__ == "__main__":
    rospy.init_node("holo_lense_to_spot_callback")
    holo_spot = HoloSpot()
    
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
