cmake_minimum_required(VERSION 3.22)
project(ugv_roarm_moveit_servo)

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
find_package(sensor_msgs REQUIRED)
find_package(roarm_msgs REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sdl2_vendor REQUIRED)
find_package(SDL2 REQUIRED)

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
  control_msgs
  geometry_msgs
  pluginlib
  roarm_msgs
  rclcpp_components
  sdl2_vendor
  SDL2
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

# Define executables
add_executable(keyboardcontrol
    src/keyboardcontrol.cpp)
target_include_directories(keyboardcontrol
    PUBLIC include)
ament_target_dependencies(keyboardcontrol 
    ${THIS_PACKAGE_INCLUDE_DEPENDS} Boost)

set(SERVO_CONTROLLER_INPUT servo_controller_input)

# Add executable for using a controller
add_library(${SERVO_CONTROLLER_INPUT} SHARED src/joystickcontrol.cpp)
ament_target_dependencies(${SERVO_CONTROLLER_INPUT} ${THIS_PACKAGE_INCLUDE_DEPENDS})
target_link_libraries(${SERVO_CONTROLLER_INPUT} SDL2::SDL2)
rclcpp_components_register_nodes(${SERVO_CONTROLLER_INPUT} "ugv_roarm_moveit_servo::JoyToServoPub")

# Install Libraries
install(
TARGETS
  ${SERVO_CONTROLLER_INPUT}
  EXPORT export_${PROJECT_NAME}
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include
)

# Install targets
install(TARGETS keyboardcontrol DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch config rviz DESTINATION share/${PROJECT_NAME})
  
ament_package()


