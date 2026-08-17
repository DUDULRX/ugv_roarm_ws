import os
import xacro
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import OpaqueFunction

from launch_ros.parameter_descriptions import ParameterValue

from moveit_configs_utils import MoveItConfigsBuilder

class RoarmMoveItConfig:
    def __init__(self, moveit_config, ros2_controllers):
        self.moveit_config = moveit_config
        self.ros2_controllers = ros2_controllers
        
def get_moveit_config(robot_name: str):
    base_path = f"config/{robot_name}"

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="ugv_roarm_moveit")
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

    ROARM_MODEL = os.environ['ROARM_MODEL']
    UGV_MODEL = os.environ['UGV_MODEL']
    GZ_VERSION = os.environ['GZ_VERSION']
    GRIPPER_TYPE = os.environ['GRIPPER_TYPE']
    add_camera = context.launch_configurations['add_camera']
    add_depth_camera = context.launch_configurations['add_depth_camera']

    moveit_config = get_moveit_config(ROARM_MODEL)

    share_dir = get_package_share_directory('ugv_roarm_moveit')
    xacro_file = os.path.join(share_dir, 'config', 'ugv_roarm.urdf.xacro')
    mappings = {
        'use_gazebo': 'true',
        'GZ_VERSION': GZ_VERSION,
        'ugv_model': UGV_MODEL,
        'roarm_model': ROARM_MODEL,
        'gripper_type': GRIPPER_TYPE,
        'add_camera': add_camera,
        'add_depth_camera': add_depth_camera,
    }
    robot_description = xacro.process_file(xacro_file, mappings=mappings).toxml()
       
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ugv_roarm_gazebo'), 
                'launch', 
                'bringup_gazebo.launch.py'
            ])
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
            'add_camera': LaunchConfiguration('add_camera'),
            'add_depth_camera': LaunchConfiguration('add_depth_camera'),
        }.items(),
    )

    move_group_configuration = {
        "publish_robot_description_semantic": True,
        "allow_trajectory_execution": True,
        "capabilities": ParameterValue("", value_type=str),
        "disable_capabilities": ParameterValue("", value_type=str),
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "monitor_dynamics": False,
    }

    move_group_params = [
        moveit_config.moveit_config.to_dict(),
        {'robot_description': robot_description},
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
        DeclareLaunchArgument('use_rviz', default_value='true', description='Whether to launch RViz2'),
        DeclareLaunchArgument('rviz_config', default_value='moveit', description='RViz config name for bringup_gazebo'),
        DeclareLaunchArgument('add_camera', default_value='false', description='Add RoArm hand camera in simulation'),
        DeclareLaunchArgument('add_depth_camera', default_value='false', description='Add RoArm depth camera in simulation'),
        OpaqueFunction(function=launch_setup)
    ])
