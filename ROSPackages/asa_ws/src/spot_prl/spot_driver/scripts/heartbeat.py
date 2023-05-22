#!/usr/bin/env python3

# Personal Robotics Laboratory - Imperial College London, 2023
# Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
#Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

import rospy
from std_msgs.msg import String

def heartbeat():
    pub = rospy.Publisher('heartbeat', String, queue_size = 10)
    rospy.init_node('heartbeat', anonymous = True)
    rate = rospy.Rate(10) 
    while not rospy.is_shutdown():
        heartbeat_str = "beat at %s" % rospy.get_time()
        pub.publish(heartbeat_str)
        rate.sleep()

if __name__ == "__main__":
    try:
        heartbeat()
    except rospy.ROSInterruptException:
        passs