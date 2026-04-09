#!/usr/bin/env python3
"""
实验四+五合并：AprilTag 跟随 + 自动抓取
参考 yjk 的 tag_grab.cpp 逻辑，用 Python 实现

跟随阶段：订阅图像，画面对中 + 前进
停车条件：TF base_link → tag_1 的 x 距离 <= 0.35m
抓取阶段：读 arm_base_link → tag_1 坐标，limit夹紧，连抓3次
"""

import rospy
import cv2
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge, CvBridgeError
import apriltag
import tf2_ros
from upros_message.srv import ArmPosition, ArmPositionRequest
from std_srvs.srv import Empty, EmptyRequest

def limit(val, lo, hi):
    return max(lo, min(hi, val))

class TagFollowGrab:

    def __init__(self):
        rospy.init_node("tag_follow_grab_node", anonymous=True)
        self.bridge = CvBridge()
        self.tag_detector = apriltag.Detector(apriltag.DetectorOptions(families="tag36h11"))
        self.follow_tag_id = 1
        self.state = "following"   # following / grabbing / done

        # TF：跟随用 base_link，抓取坐标用 arm_base_link
        self.tf_buffer   = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.image_sub = rospy.Subscriber("/camera/color/image_raw", Image, self.image_callback)
        self.image_pub = rospy.Publisher("/image_result", Image, queue_size=10)
        self.vel_pub   = rospy.Publisher("/cmd_vel", Twist, queue_size=10)

        rospy.loginfo("Waiting for arm services...")
        for srv in ["/upros_arm_control/arm_pos_service_open",
                    "/upros_arm_control/zero_service",
                    "/upros_arm_control/grab_service",
                    "/upros_arm_control/release_service"]:
            rospy.wait_for_service(srv, timeout=10.0)

        self.arm_move    = rospy.ServiceProxy("/upros_arm_control/arm_pos_service_open", ArmPosition)
        self.arm_zero    = rospy.ServiceProxy("/upros_arm_control/zero_service", Empty)
        self.arm_grab    = rospy.ServiceProxy("/upros_arm_control/grab_service", Empty)
        self.arm_release = rospy.ServiceProxy("/upros_arm_control/release_service", Empty)

        # 先归零
        rospy.loginfo("Arm zero...")
        self.arm_zero(EmptyRequest())
        rospy.sleep(2.0)

        rospy.loginfo("Ready! Place tag in front of robot. Will follow and grab.")

    def image_callback(self, msg):
        """只做图像跟随（对中+前进），不做TF查询，保持回调轻量"""
        if self.state != "following":
            return
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            frame = cv_image.copy()
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape[:2]
            tags = self.tag_detector.detect(gray)
            twist = Twist()
            tag_found = False

            for tag in tags:
                if tag.tag_id != self.follow_tag_id:
                    continue
                tag_found = True
                top_left, _, bottom_right, _ = tag.corners
                cx = int((top_left[0] + bottom_right[0]) / 2)
                cy = int((top_left[1] + bottom_right[1]) / 2)

                cv2.line(frame, (cx-20, cy), (cx+20, cy), (0,0,255), 2)
                cv2.line(frame, (cx, cy-20), (cx, cy+20), (0,0,255), 2)
                cv2.putText(frame, f"state:{self.state}", (10, 35),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                cv2.putText(frame, "stop at base_link->tag <= 0.35m", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,200,255), 2)

                # 左右对中
                if cx > w / 2 + 20:
                    twist.angular.z = -0.5
                elif cx < w / 2 - 20:
                    twist.angular.z = 0.5
                else:
                    twist.angular.z = 0.0
                # 持续前进
                twist.linear.x = 0.15

            if tag_found:
                self.vel_pub.publish(twist)
            else:
                self.vel_pub.publish(Twist())  # 没看到标签就停

            self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame, "bgr8"))
        except CvBridgeError as e:
            rospy.logerr(e)

    def run(self):
        """
        主循环：
        - following 阶段：用 base_link→tag TF 判断是否到位（dx <= 0.35m）
        - 到位后切换到 grabbing，执行抓取序列
        """
        rate = rospy.Rate(20)  # 20Hz 查询TF

        while not rospy.is_shutdown():
            if self.state == "done":
                break

            if self.state == "following":
                try:
                    # 用 base_link 判断实际到位距离（与 yjk 一致）
                    tfs_base = self.tf_buffer.lookup_transform(
                        "base_link", "tag_1", rospy.Time(0), rospy.Duration(0.05))
                    dx = tfs_base.transform.translation.x
                    dy = tfs_base.transform.translation.y

                    rospy.loginfo_throttle(1.0, f"base_link->tag: dx={dx:.3f}m  dy={dy:.3f}m")

                    if dx <= 0.35:
                        rospy.loginfo(f"In range! dx={dx:.3f}m <= 0.35m, stopping...")
                        self.state = "grabbing"
                        self.vel_pub.publish(Twist())  # 停车
                        rospy.sleep(1.0)
                        self._do_grab()

                except Exception:
                    pass  # TF暂时不可用，继续等待

            rate.sleep()

    def _do_grab(self):
        """
        抓取序列（参考 yjk tag_grab.cpp）：
        release → arm_pos_service_open（夹紧坐标）→ 连抓3次 → zero+继续夹紧
        """
        try:
            rospy.loginfo("=== Grab sequence start ===")

            # 获取 arm_base_link → tag_1 精确坐标
            tfs_arm = self.tf_buffer.lookup_transform(
                "arm_base_link", "tag_1", rospy.Time(0), rospy.Duration(3.0))

            xr = tfs_arm.transform.translation.x
            yr = tfs_arm.transform.translation.y
            zr = tfs_arm.transform.translation.z

            # 坐标转换（同官方 apriltag_grab.cpp）
            x_raw = -int(yr * 1000)
            y_raw =  int(xr * 1000)
            z_raw =  int(zr * 1000) + 10

            # 夹紧到可达范围（参考 yjk limit 逻辑）
            x = limit(x_raw, -130, 130)
            y = limit(y_raw,   30, 190)
            z = limit(z_raw,   40, 230)

            rospy.loginfo(f"TF raw: x={xr:.3f}m y={yr:.3f}m z={zr:.3f}m")
            rospy.loginfo(f"Arm raw:    X={x_raw}  Y={y_raw}  Z={z_raw} mm")
            rospy.loginfo(f"Arm clamped: X={x}  Y={y}  Z={z} mm")

            empty = EmptyRequest()
            req = ArmPositionRequest()
            req.x = float(x)
            req.y = float(y)
            req.z = float(z)

            # Step1: 松开爪子
            rospy.loginfo("Step1: release...")
            self.arm_release(empty)
            rospy.sleep(2.0)

            # Step2: 移动到目标位置
            rospy.loginfo(f"Step2: arm_pos_service_open({x},{y},{z})...")
            resp = self.arm_move(req)
            rospy.loginfo(f"  status={resp.status}")
            rospy.sleep(3.5)

            # Step3: 连抓3次（参考 yjk，保证夹紧）
            rospy.loginfo("Step3: grab x3...")
            self.arm_grab(empty); rospy.sleep(1.0)
            self.arm_grab(empty); rospy.sleep(1.0)
            self.arm_grab(empty); rospy.sleep(3.0)

            # Step4: 归零 + 继续夹紧（拿着东西归位）
            rospy.loginfo("Step4: zero (keep grabbing)...")
            self.arm_zero(empty)
            self.arm_grab(empty)
            self.arm_grab(empty)
            rospy.sleep(5.0)

            # Step5: 松开放下
            rospy.loginfo("Step5: release...")
            self.arm_release(empty)
            rospy.sleep(1.0)

            self.state = "done"
            rospy.loginfo("=== Grab complete! ===")

        except Exception as e:
            rospy.logerr(f"Grab failed: {e}")
            self.state = "following"

if __name__ == "__main__":
    try:
        node = TagFollowGrab()
        node.run()   # 主循环在 run() 里，image_callback 只做轻量跟随
    except rospy.ROSInterruptException:
        pass
