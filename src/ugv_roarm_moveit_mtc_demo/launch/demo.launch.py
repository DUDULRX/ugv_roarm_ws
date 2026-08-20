import sys
import os
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    roarm_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_roarm_moveit'), 'launch', 'ugv_roarm_moveit.launch.py')
        ),
        launch_arguments={
            'rviz_config': 'moveit_mtc',
            'capabilities': 'move_group/ExecuteTaskSolutionCapability',
            'use_rviz': LaunchConfiguration('use_rviz'),
            'add_camera': LaunchConfiguration('add_camera'),
            'add_depth_camera': LaunchConfiguration('add_depth_camera'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items()
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument('use_rviz', default_value='false', description='Whether to launch RViz2'),
            DeclareLaunchArgument('add_camera', default_value='false', description='Whether to add hand camera'),
            DeclareLaunchArgument('add_depth_camera', default_value='false', description='Whether to add depth camera'),
            DeclareLaunchArgument('use_sim_time', default_value='false', description='Use /clock (Gazebo)'),
            roarm_moveit_launch,
        ]
    )
