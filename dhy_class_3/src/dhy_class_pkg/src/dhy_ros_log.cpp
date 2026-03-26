#include <ros/ros.h>
#include <ros/console.h>

int main(int argc, char** argv)
{
    ros::init(argc, argv, "ros_logging_example");
    ros::NodeHandle nh;

    // Enable DEBUG level so ROS_DEBUG messages appear in rqt_console
    if (ros::console::set_logger_level(ROSCONSOLE_DEFAULT_NAME,
                                        ros::console::levels::Debug))
        ros::console::notifyLoggerLevelsChanged();

    ROS_INFO("LOG node started. Publishing all 5 log levels at 1 Hz.");

    ros::Rate rate(1);
    int count = 0;

    while (ros::ok())
    {
        ROS_DEBUG("This is a DEBUG message. [count=%d]", count);
        ROS_INFO("This is an INFO message. [count=%d]", count);
        ROS_WARN("This is a WARNING message. [count=%d]", count);
        ROS_ERROR("This is an ERROR message. [count=%d]", count);
        ROS_FATAL("This is a FATAL message. [count=%d]", count);
        count++;
        ros::spinOnce();
        rate.sleep();
    }
    return 0;
}
