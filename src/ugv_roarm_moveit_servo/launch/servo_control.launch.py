import os
import sys
import yaml
import xacro

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from moveit_configs_utils import MoveItConfigsBuilder

def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return file.read()
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None

def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None

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
    
# Function to set up and launch ROS 2 nodes based on the given context
def launch_setup(context, *args, **kwargs):
    add_camera = context.launch_configurations['add_camera']
    print("add_camera flag",add_camera)
    add_depth_camera = context.launch_configurations['add_depth_camera']

    share_dir = get_package_share_directory('ugv_roarm_moveit')    
    UGV_MODEL = os.environ['UGV_MODEL']
    ROARM_MODEL = os.environ['ROARM_MODEL']
    
    xacro_file = os.path.join(
        share_dir,
        'config', 
        'ugv_roarm.urdf.xacro')      

    mappings = {
               "use_gazebo": "false",
               "ugv_model": UGV_MODEL,
               "roarm_model": ROARM_MODEL,
               "add_depth_camera": add_depth_camera,
               "add_camera": add_camera,
               } 
               
    robot_description_config = xacro.process_file(xacro_file, mappings=mappings)
    robot_description = robot_description_config.toxml()
    
    moveit_config = get_moveit_config(ROARM_MODEL)

    ugv_roarm_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_roarm_moveit'), 'launch', 'ugv_roarm_moveit.launch.py')
        ),
        launch_arguments={
            'rviz_config': 'moveit_servo',
            'use_rviz': LaunchConfiguration('use_rviz'),
        }.items()
    )
        
    # Get parameters for the Servo node
    servo_yaml = load_yaml("ugv_roarm_moveit_servo", "config/ugv_roarm_config.yaml")
    servo_yaml['move_group_name'] = "hand"
    roarm_controller = 'hand_controller'
    servo_yaml['command_out_topic'] = '/{}/joint_trajectory'.format(roarm_controller)

    servo_params = {"moveit_servo": servo_yaml}
    acceleration_filter_update_period = {"update_period": 0.01}
    planning_group_name = {"planning_group_name": "hand"}
    ugv_roarm_moveit_servo_container = ComposableNodeContainer(
        name="ugv_roarm_moveit_servo_container",
        namespace="/",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=[
            ComposableNode(
                package='moveit_servo',
                plugin='moveit_servo::ServoNode',
                name='servo_node',
                parameters=[
                    servo_params,
                    acceleration_filter_update_period,
                    planning_group_name,
                    {'robot_description': robot_description},
                    moveit_config.moveit_config.robot_description_semantic,
                    moveit_config.moveit_config.robot_description_kinematics,
                    moveit_config.moveit_config.joint_limits,
                ],
            ),
            ComposableNode(
                package="ugv_roarm_moveit_servo",
                plugin="ugv_roarm_moveit_servo::JoyToServoPub",
                name="controller_to_servo_node",
            ),
        ],
        output="screen",
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
    )

    set_gripper_cmd_node = Node(
        package='roarm_moveit_cmd',
        executable='setgrippercmd',
    )
    
    return [
        ugv_roarm_moveit_launch,
        ugv_roarm_moveit_servo_container,
        joy_node,
        set_gripper_cmd_node,
    ]

# Function to generate the launch description with configurable arguments
def generate_launch_description():
    return LaunchDescription([
        # Argument to specify whether to use RViz
        DeclareLaunchArgument('use_rviz', default_value='false', description='Whether to launch RViz2'),
        DeclareLaunchArgument('add_camera', default_value='false', description='Choose whether to add camera'),      
        DeclareLaunchArgument('add_depth_camera', default_value='false', description='Choose whether to add depth camera'),      
        # Opaque function to execute the setup
        OpaqueFunction(function=launch_setup)
    ])

# Main entry point for launching the description
if __name__ == '__main__':
    generate_launch_description()
    