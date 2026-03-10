cmake_minimum_required(VERSION 3.22)
project(ugv_roarm_cmd)

# Common cmake code applied to all moveit packages
find_package(moveit_common REQUIRED)

find_package(Eigen3 REQUIRED)
find_package(Boost REQUIRED system filesystem date_time thread)
find_package(ament_cmake REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(roarm_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(roarm_moveit_cmd REQUIRED)
find_package(ugv_msgs REQUIRED)

set(THIS_PACKAGE_INCLUDE_DEPENDS
  ament_cmake
  sensor_msgs
  rclcpp
  rclcpp_action
  tf2_geometry_msgs
  tf2_ros
  moveit_ros_planning_interface
  Eigen3
  Boost
  geometry_msgs
  control_msgs
  roarm_msgs
  roarm_moveit_cmd
  nav2_msgs
  trajectory_msgs
  ugv_msgs
)

# Include directories
include_directories(
  include
  ${ament_INCLUDE_DIRS}
  ${THIS_PACKAGE_INCLUDE_DIRS}
)

# Declare dependencies
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_export_include_directories(include)

#add_executable(pointsave 
#    src/pointsave.cpp)
#target_include_directories(pointsave 
#    PUBLIC include)
#ament_target_dependencies(pointsave 
#    ${THIS_PACKAGE_INCLUDE_DEPENDS} Boost)

add_executable(navigatetoposecmd 
   src/navigatetoposecmd.cpp)
target_include_directories(navigatetoposecmd 
   PUBLIC include)
ament_target_dependencies(navigatetoposecmd 
   ${THIS_PACKAGE_INCLUDE_DEPENDS} Boost)

# Install targets
#install(TARGETS pointsave navigatetoposecmd DESTINATION lib/${PROJECT_NAME})
install(TARGETS navigatetoposecmd DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch rviz DESTINATION share/${PROJECT_NAME})
  
ament_package()


