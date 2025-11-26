#!/usr/bin/env python3
# Software License Agreement (BSD License)
#
# Copyright (c) 2021, UFACTORY, Inc.
# All rights reserved.
#
# Author: Vinman <vinman.wen@ufactory.cc> <vinman.cub@gmail.com>

import os
import xacro
import sys
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.actions import OpaqueFunction


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
      
    add_oak_d_lite = LaunchConfiguration('add_oak_d_lite', default=False)
    
    load_controller = LaunchConfiguration('load_controller', default=True)
    use_rviz = LaunchConfiguration('use_rviz', default=False)

    ros_namespace = LaunchConfiguration('ros_namespace', default='').perform(context)
    
    UGV_MODEL = os.environ['UGV_MODEL']
    ROARM_MODEL = os.environ['ROARM_MODEL'] 
  
    moveit_config = get_moveit_config(ROARM_MODEL)
    rviz_config = LaunchConfiguration('rviz_config', default=str(moveit_config.moveit_config.package_path / "rviz/interact.rviz"))
            
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    xacro_file_name = ROARM_MODEL + '.urdf.xacro'
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    xacro_file = os.path.join(
        share_dir,
        'config', 
        'ugv_roarm.urdf.xacro')    

    add_depth_camera = "false"
    for arg in sys.argv:
        if 'add_depth_camera' in arg:
            add_depth_camera = arg.split(':=')[1]

    mappings = {
                "ros2_control_plugin": "GazeboSystem",
                "use_gazebo": "true",
                "ugv_model": UGV_MODEL,
                "roarm_model": ROARM_MODEL,
                "add_depth_camera": add_depth_camera,
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
    )

    rviz_parameters = [
        moveit_config.moveit_config.planning_pipelines,
        moveit_config.moveit_config.robot_description_kinematics,
        moveit_config.moveit_config.joint_limits,
        {'use_sim_time': True},
    ]
    
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=["-d", rviz_config],
        parameters=rviz_parameters,
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
        ],
        condition=IfCondition(use_rviz)
    )
        
    joint_state_broadcaster_spawner_node = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '{}/controller_manager'.format(ros_namespace)],
        output='screen',
    )
               
    # gazebo launch
    # gazebo_ros/launch/gazebo.launch.py
    gazebo_world = PathJoinSubstitution([FindPackageShare('ugv_roarm_gazebo'), 'worlds', 'room.world'])
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'])),
        launch_arguments={
            'world': gazebo_world,
            'server_required': 'true',
            'gui_required': 'true',
        }.items(),
    )

    # gazebo spawn entity node
    gazebo_spawn_entity_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', "ugv_roarm",
            '-x', '0.0',
            '-y', '0',
            '-z', '0',
            '-Y', '0',
        ],
        parameters=[{'use_sim_time': True}],
    )
        
    controller_nodes = []           
    controller_names = moveit_config.moveit_config.trajectory_execution.get(
        "moveit_simple_controller_manager", {}
    ).get("controller_names", [])
             
    controllers = [
        '',
    ] + [controller for controller in controller_names]

    if load_controller.perform(context) in ('True', 'true'):
        for controller in controller_names:
            controller_nodes.append(Node(
                package='controller_manager',
                executable='spawner',
                output='screen',
                arguments=[
                    controller,
                    '--controller-manager', '{}/controller_manager'.format(ros_namespace)
                ],
                parameters=[{'use_sim_time': True}],
            ))

                    
    return [
        #controller_nodes,
        robot_state_publisher_node,
        joint_state_broadcaster_spawner_node,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner_node,
                on_exit=controller_nodes,
            )
        ),
        gazebo_launch,
        gazebo_spawn_entity_node,
        rviz2_node,
    ]

def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=launch_setup)
    ])
