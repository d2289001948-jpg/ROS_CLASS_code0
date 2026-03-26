#include <ros/ros.h>
#include <dynamic_reconfigure/server.h>
#include <dhy_class_pkg/TutorialsConfig.h>
#include <geometry_msgs/Twist.h>

// 当前速度（由动态参数回调更新）
double robot_speed = 0.0;

// 动态参数回调：每次在 rqt_reconfigure 中调整参数时触发
void callback(dhy_class_pkg::TutorialsConfig &config, uint32_t level)
{
    ROS_INFO("Dynamic param updated: int=%d  double=%.3f  str=%s  bool=%s  size=%d",
             config.int_param,
             config.double_param,
             config.str_param.c_str(),
             config.bool_param ? "True" : "False",
             config.size);

    // 将 double_param 作为机器人线速度（范围 -0.25 ~ 0.25 m/s）
    robot_speed = config.double_param;
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "dynamic_speed_node");
    ros::NodeHandle nh;

    // 发布速度指令到机器人话题（5.5 对应真实机器人，话题为 /cmd_vel）
    ros::Publisher cmd_pub = nh.advertise<geometry_msgs::Twist>("/cmd_vel", 10);

    // 注册动态参数服务端
    dynamic_reconfigure::Server<dhy_class_pkg::TutorialsConfig> server;
    dynamic_reconfigure::Server<dhy_class_pkg::TutorialsConfig>::CallbackType f;
    f = boost::bind(&callback, _1, _2);
    server.setCallback(f);

    ROS_INFO("dynamic_speed_node started. Use rqt_reconfigure to adjust speed.");

    ros::Rate rate(10);  // 10 Hz
    while (ros::ok())
    {
        geometry_msgs::Twist cmd_vel;
        cmd_vel.linear.x  = robot_speed;  // 前进/后退速度
        cmd_vel.angular.z = 0.0;          // 不旋转
        cmd_pub.publish(cmd_vel);

        ros::spinOnce();
        rate.sleep();
    }

    return 0;
}
