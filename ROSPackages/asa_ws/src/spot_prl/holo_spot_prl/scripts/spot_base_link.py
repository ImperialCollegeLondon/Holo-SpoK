#!/usr/bin/env python3

# Personal Robotics Laboratory - Imperial College London, 2022
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

import rospy
from geometry_msgs.msg import TransformStamped
import tf2_ros

def tf_transform_publisher():
  rospy.init_node('spot_base_link', anonymous=False)

  # TF interface
  tf_buffer = tf2_ros.Buffer()
  tf_listener = tf2_ros.TransformListener(tf_buffer)

  # Publishers and subscribers
  pub = rospy.Publisher('spot_base_link', TransformStamped, queue_size=1, latch=True)

  # ROS params
  parent_frame = rospy.get_param('~sbl_parent_frame', 'odom')
  child_frame = rospy.get_param('~sbl_child_frame', 'base_link')
  update_rate = rospy.get_param('~update_rate', 10.0)

  rate = rospy.Rate(update_rate)
  while not rospy.is_shutdown():
    try:
      # Will get the latest transform
      trans = tf_buffer.lookup_transform(parent_frame, child_frame, rospy.Time())
    except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException):
      # Just wait if we can't look up the transform.
      rate.sleep()
      continue
    pub.publish(trans)
    rate.sleep()

if __name__ == '__main__':
  try:
    tf_transform_publisher()
  except rospy.ROSInterruptException:
    pass
