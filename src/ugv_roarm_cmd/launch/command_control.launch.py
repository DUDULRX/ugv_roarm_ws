from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration

def generate_launch_description():
    ld = LaunchDescription()

    set_gripper_cmd_node = Node(
        package='roarm_moveit_cmd',
        executable='setgrippercmd',
    )

    yolov8_detect_oak_node = Node(
        package='roarm_vision',
        executable='yolov8_detect_oak',
    )
            
    pick_place_cmd_node = Node(
        package='ugv_roarm_cmd',
        executable='pickplacecmd',
    )
    
    navigate_to_pose_cmd_node = Node(
        package='ugv_roarm_cmd',
        executable='navigatetoposecmd',
    )   
    
    ld.add_action(set_gripper_cmd_node) 
    ld.add_action(yolov8_detect_oak_node) 
    ld.add_action(pick_place_cmd_node) 
    #ld.add_action(navigate_to_pose_cmd_node)    
    
    return ld