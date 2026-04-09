#include "tf2_ros/transform_listener.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.h"
#include "geometry_msgs/TransformStamped.h"
#include "upros_message/ArmPosition.h"
#include "std_srvs/Empty.h"
#include <ros/ros.h>
#include <algorithm>

int clamp(int val, int lo, int hi) {
    return std::max(lo, std::min(hi, val));
}

void sleep(double second) { ros::Duration(second).sleep(); }

int main(int argc, char **argv)
{
    ros::init(argc, argv, "mgrab_test");
    ros::AsyncSpinner spinner(1);
    spinner.start();
    ros::NodeHandle nh;

    ros::ServiceClient arm_move_open_client = nh.serviceClient<upros_message::ArmPosition>("/upros_arm_control/arm_pos_service_open");
    ros::ServiceClient arm_zero_client      = nh.serviceClient<std_srvs::Empty>("/upros_arm_control/zero_service");
    ros::ServiceClient arm_grab_client      = nh.serviceClient<std_srvs::Empty>("/upros_arm_control/grab_service");
    ros::ServiceClient arm_release_client   = nh.serviceClient<std_srvs::Empty>("/upros_arm_control/release_service");

    // 先归零
    std_srvs::Empty empty_srv;
    arm_zero_client.call(empty_srv);
    sleep(2.0);

    tf2_ros::Buffer buffer;
    tf2_ros::TransformListener listener(buffer);
    ROS_INFO("Waiting for TF transform (arm_base_link -> tag_1)...");

    geometry_msgs::TransformStamped tfs;
    tfs = buffer.lookupTransform("arm_base_link", "tag_1", ros::Time(0), ros::Duration(100));

    double xr = tfs.transform.translation.x;
    double yr = tfs.transform.translation.y;
    double zr = tfs.transform.translation.z;

    // 坐标转换（ROS -> 机械臂，mm）
    int x_raw = -int(yr * 1000);
    int y_raw =  int(xr * 1000);
    int z_raw =  int(zr * 1000) + 10;

    // 夹紧到可达范围（参考 yjk 代码）
    int x = clamp(x_raw, -130, 130);
    int y = clamp(y_raw,   30, 190);
    int z = clamp(z_raw,   40, 230);

    ROS_INFO("TF raw: x=%.3f m, y=%.3f m, z=%.3f m", xr, yr, zr);
    ROS_INFO("Arm raw:     X=%d  Y=%d  Z=%d mm", x_raw, y_raw, z_raw);
    ROS_INFO("Arm clamped: X=%d  Y=%d  Z=%d mm", x, y, z);

    upros_message::ArmPosition move_srv;
    move_srv.request.x = x;
    move_srv.request.y = y;
    move_srv.request.z = z;

    // Step1: 松开爪子
    arm_release_client.call(empty_srv);
    ROS_INFO("Step1 release: OK");
    sleep(2.0);

    // Step2: 移动到目标位置（爪子张开）
    arm_move_open_client.call(move_srv);
    ROS_INFO("Step2 arm_pos_service_open: OK (status=%d)", (int)move_srv.response.status);
    sleep(3.5);

    // Step3: 连抓3次（参考 yjk，保证夹紧）
    arm_grab_client.call(empty_srv); sleep(1.0);
    arm_grab_client.call(empty_srv); sleep(1.0);
    arm_grab_client.call(empty_srv);
    ROS_INFO("Step3 grab x3: OK");
    sleep(3.0);

    // Step4: 归零（夹住物体回到直立位）
    // go_home() 内部把爪子设为-400（半开），0.2s后用grab_service覆盖回-700
    ROS_INFO("Step4: returning to zero (holding object)...");
    arm_zero_client.call(empty_srv);   // 发送归零指令（手臂各关节+爪子-400）
    sleep(0.2);                        // 等0.2s让归零指令完全发出
    arm_grab_client.call(empty_srv);   // 覆盖爪子→-700（夹紧），手臂继续归位
    arm_grab_client.call(empty_srv);
    sleep(5.0);                        // 等5s让手臂完全归位
    ROS_INFO("Step4 zero+hold: OK");

    ROS_INFO("Done!");
    ros::shutdown();
    return 0;
}
