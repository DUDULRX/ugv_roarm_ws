#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2021, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

import os
import xacro
import yaml
from ament_index_python import get_package_share_directory
from launch.launch_description_sources import load_python_launch_file_as_module
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.actions import OpaqueFunction

from launch_ros.parameter_descriptions import ParameterValue

from srdfdom.srdf import SRDF

from moveit_configs_utils.launch_utils import (
    add_debuggable_node,
    DeclareBooleanLaunchArg,
)

from moveit_configs_utils import MoveItConfigsBuilder

class RoarmMoveItConfig:
    def __init__(self, moveit_config, ros2_controllers):
        self.moveit_config = moveit_config
        self.ros2_controllers = ros2_controllers
        
def get_moveit_config(robot_name: str):
    base_path = f"config/{robot_name}"

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="ugv_roarm_moveit")
        #.robot_description(file_path=f"{base_path}/{robot_name}.urdf.xacro")
        .robot_description_semantic(file_path=f"{base_path}/{robot_name}.srdf")
        .robot_description_kinematics(file_path=f"{base_path}/kinematics.yaml")
        .trajectory_execution(file_path=f"{base_path}/moveit_controllers.yaml")
        .sensors_3d(file_path=f"{base_path}/sensors_3d.yaml")
        .joint_limits(file_path=f"{base_path}/joint_limits.yaml")
        .pilz_cartesian_limits(file_path=f"{base_path}/pilz_cartesian_limits.yaml")
        .to_moveit_configs()
    )
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    ros2_controllers = os.path.join(share_dir, f"{base_path}/ros2_controllers.yaml")  
    moveit_config = RoarmMoveItConfig(moveit_config, ros2_controllers)

    return moveit_config
        
def launch_setup(context, *args, **kwargs):

    ros_namespace = LaunchConfiguration('ros_namespace', default='').perform(context)
    
    UGV_MODEL = os.environ['UGV_MODEL']
    ROARM_MODEL = os.environ['ROARM_MODEL'] 
  
    moveit_config = get_moveit_config(ROARM_MODEL)
    
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    xacro_file_name = ROARM_MODEL + '.urdf.xacro'
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    xacro_file = os.path.join(
        share_dir,
        'config', 
        'ugv_roarm.urdf.xacro')    
    mappings = {
               "use_gazebo": "false",
               "ugv_model": UGV_MODEL,
               "roarm_model": ROARM_MODEL
               } 
                
    mappings = {
               "ros2_control_plugin": "GazeboSystem",
                "use_gazebo": "true",
               "ugv_model": UGV_MODEL,
               "roarm_model": ROARM_MODEL
               } 

    robot_description_config = xacro.process_file(xacro_file, mappings=mappings)
    robot_description = robot_description_config.toxml()
                
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
                   {'use_sim_time': True}, 
                   {'robot_description': robot_description},
        ],
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
        ]
    )
       
    # gazebo launch
    # gazebo_ros/launch/gazebo.launch.py
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('ugv_roarm_gazebo'), 'launch', 'bringup.launch.py'])),
    )

    move_group_configuration = {
        "publish_robot_description_semantic": True,
        "allow_trajectory_execution": True,
        # Note: Wrapping the following values is necessary so that the parameter value can be the empty string
        "capabilities": ParameterValue("", value_type=str),
        "disable_capabilities": ParameterValue("", value_type=str),
        # Publish the planning scene of the physical robot so that rviz plugin can know actual robot
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "monitor_dynamics": False,
    }

    move_group_params = [
        moveit_config.moveit_config.to_dict(),
        move_group_configuration,
        {'use_sim_time': True},
    ]

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=move_group_params,
    )
            
    return [
        move_group_node,
        gazebo_launch,
    ]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])
