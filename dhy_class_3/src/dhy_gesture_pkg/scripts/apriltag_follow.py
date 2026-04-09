#!/usr/bin/env python3

import rospy
import cv2
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge, CvBridgeError
import apriltag

class ImageSubscriberNode:

    def __init__(self):
        rospy.init_node("image_subscriber_node", anonymous=True)
        self.tag_detector = apriltag.Detector(apriltag.DetectorOptions(families="tag36h11"))
        self.follow_tag_id = 1  # 跟随 ID=1 的 AprilTag
        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/camera/color/image_raw", Image, self.image_callback)
        self.image_pub = rospy.Publisher("/image_result", Image, queue_size=10)
        self.vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            frame = cv_image.copy()
            gray_frame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            height, width = gray_frame.shape
            tags = self.tag_detector.detect(gray_frame)
            for tag in tags:
                if tag.tag_id == self.follow_tag_id:
                    top_left, _, bottom_right, _ = tag.corners
                    center_x = int((top_left[0] + bottom_right[0]) / 2)
                    center_y = int((top_left[1] + bottom_right[1]) / 2)
                    area = int((bottom_right[0] - top_left[0]) * (bottom_right[1] - top_left[1]))
                    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 0, 255), 2)
                    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 0, 255), 2)
                    twist = Twist()
                    if center_x > width / 2 + 20:
                        twist.angular.z = -0.5   # 右偏，左转
                    elif center_x < width / 2 - 20:
                        twist.angular.z = 0.5    # 左偏，右转
                    else:
                        twist.angular.z = 0.0
                    if area < 300:
                        twist.linear.x = 0.3     # 目标较小，前进
                    self.vel_pub.publish(twist)
            ros_image = self.bridge.cv2_to_imgmsg(frame, "bgr8")
            self.image_pub.publish(ros_image)
        except CvBridgeError as e:
            rospy.logerr(e)
            return

    def spin(self):
        rospy.spin()

if __name__ == "__main__":
    try:
        node = ImageSubscriberNode()
        node.spin()
    except rospy.ROSInterruptException:
        pass
