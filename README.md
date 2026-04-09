# ROS Class Code - dhy

本仓库包含 ROS 课程实验代码（dhy 工作空间），对应 dhy_ros_class_ws。

## 实验一：里程计方形运动（odom_square）

包名：clas_pkg
文件：src/odom_square.cpp
功能：使用里程计反馈控制小车走正方形轨迹（前进+转向×4次）。
关键话题：
- 订阅 /odom (nav_msgs/Odometry)
- 发布 /cmd_vel (geometry_msgs/Twist)

## 实验二：图像巡线（follow_line）

包名：dhy_class_pkg
文件：scripts/follow_line.py
功能：订阅摄像头图像，使用 OpenCV 识别地面线条，控制小车沿线行驶。
关键话题：
- 订阅 /camera/color/image_raw (sensor_msgs/Image)
- 发布 /cmd_vel (geometry_msgs/Twist)

## 实验三：手势识别控制（gesture_movement）

包名：dhy_gesture_pkg
文件：scripts/gesture_movement.py, scripts/upros_gesture.py
功能：通过摄像头识别手势，控制机械臂或小车动作。

## 实验四：AprilTag 跟随（apriltag_follow）

包名：dhy_gesture_pkg
文件：scripts/apriltag_follow.py
功能：检测 tag36h11 标签，控制小车跟随目标标签。
关键话题：
- 订阅 /camera/color/image_raw
- 发布 /cmd_vel, /image_result

## 实验五：AprilTag 抓取（tag_follow_grab）

包名：dhy_gesture_pkg
文件：scripts/tag_follow_grab.py, src/tag_grab.cpp
功能：
1. 小车跟随 AprilTag(tag_1)，base_link->tag_1 前向距离<=0.35m 停车
2. 读取 arm_base_link->tag_1 坐标转换为机械臂坐标(mm)并夹紧范围
3. 抓取序列：松开->移动->连抓3次->归零(保持夹紧)

坐标映射(ROS -> 机械臂 mm):
  arm_x = clamp(-yr*1000, -130, 130)
  arm_y = clamp( xr*1000,   30, 190)
  arm_z = clamp( zr*1000+10, 40, 230)

关键服务：
  /upros_arm_control/arm_pos_service_open (ArmPosition)
  /upros_arm_control/zero_service, grab_service, release_service (Empty)

## 运行说明

  # 启动机器人基础环境
  roslaunch upros_bringup bringup_w2a.launch

  # 启动 AprilTag 识别（实验四、五）
  roslaunch upros_bringup recognize_apriltag.launch

  # 实验五：跟随+抓取（Python版）
  rosrun dhy_gesture_pkg tag_follow_grab.py

  # 实验五：手动抓取（C++版）
  rosrun dhy_gesture_pkg tag_grab_node
