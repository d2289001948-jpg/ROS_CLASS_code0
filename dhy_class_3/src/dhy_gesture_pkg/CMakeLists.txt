cmake_minimum_required(VERSION 3.0.2)
project(dhy_gesture_pkg)

add_compile_options(-std=c++11)

find_package(catkin REQUIRED COMPONENTS
  cv_bridge
  geometry_msgs
  roscpp
  rospy
  sensor_msgs
  std_msgs
  std_srvs
  tf2_ros
  tf2_geometry_msgs
  upros_message
)

catkin_package(
  CATKIN_DEPENDS cv_bridge geometry_msgs roscpp rospy sensor_msgs std_msgs std_srvs tf2_ros tf2_geometry_msgs upros_message
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

add_executable(tag_grab_node src/tag_grab.cpp)
target_link_libraries(tag_grab_node ${catkin_LIBRARIES})
