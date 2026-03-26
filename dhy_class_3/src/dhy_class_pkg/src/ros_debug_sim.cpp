#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <tf2_ros/transform_broadcaster.h>
#include <geometry_msgs/TransformStamped.h>

int main(int argc, char** argv)
{
    ros::init(argc, argv, "ros_debug_sim");
    ros::NodeHandle nh;

    // Publish fake camera image to simulate /camera/color/image_raw
    ros::Publisher img_pub =
        nh.advertise<sensor_msgs::Image>("/camera/color/image_raw", 10);

    // TF broadcaster to simulate robot coordinate frames
    tf2_ros::TransformBroadcaster tf_broadcaster;

    ROS_INFO("ros_debug_sim started.");
    ROS_INFO("  /camera/color/image_raw  -> view with rqt_image_view");
    ROS_INFO("  TF: world->base_link->camera_link -> view with rqt_tf_tree");

    ros::Rate rate(10);

    while (ros::ok())
    {
        ros::Time now = ros::Time::now();

        // ---------- Fake camera image (320x240 RGB gradient) ----------
        sensor_msgs::Image img;
        img.header.stamp    = now;
        img.header.frame_id = "camera_link";
        img.height   = 240;
        img.width    = 320;
        img.encoding = "rgb8";
        img.step     = img.width * 3;
        img.data.resize(img.height * img.step);

        for (int r = 0; r < (int)img.height; ++r)
            for (int c = 0; c < (int)img.width; ++c) {
                int i = r * img.step + c * 3;
                img.data[i]   = (uint8_t)(c * 255 / img.width);   // R gradient (left→right)
                img.data[i+1] = (uint8_t)(r * 255 / img.height);  // G gradient (top→bottom)
                img.data[i+2] = 100;                               // B constant
            }
        img_pub.publish(img);

        // ---------- TF tree: world -> base_link -> camera_link ----------
        geometry_msgs::TransformStamped tf;

        // world -> base_link
        tf.header.stamp    = now;
        tf.header.frame_id = "world";
        tf.child_frame_id  = "base_link";
        tf.transform.translation.x = 0.0;
        tf.transform.translation.y = 0.0;
        tf.transform.translation.z = 0.0;
        tf.transform.rotation.w    = 1.0;
        tf_broadcaster.sendTransform(tf);

        // base_link -> camera_link (camera mounted 15 cm front, 10 cm up)
        tf.header.frame_id = "base_link";
        tf.child_frame_id  = "camera_link";
        tf.transform.translation.x = 0.15;
        tf.transform.translation.y = 0.0;
        tf.transform.translation.z = 0.10;
        tf.transform.rotation.x    = 0.0;
        tf.transform.rotation.y    = 0.0;
        tf.transform.rotation.z    = 0.0;
        tf.transform.rotation.w    = 1.0;
        tf_broadcaster.sendTransform(tf);

        ros::spinOnce();
        rate.sleep();
    }
    return 0;
}
