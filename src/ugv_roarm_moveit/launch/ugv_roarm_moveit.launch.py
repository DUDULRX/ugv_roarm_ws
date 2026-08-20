import os
import xacro
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from moveit_configs_utils.launch_utils import (
    DeclareBooleanLaunchArg,
)

from ament_index_python.packages import get_package_share_directory 
from moveit_configs_utils import MoveItConfigsBuilder
from launch.conditions import IfCondition

def get_rviz_config_file(context):
    rviz_config = context.launch_configurations['rviz_config']

    # Get the package directories for the UGV project
    ugv_roarm_description_dir = get_package_share_directory('ugv_roarm_description')
    ugv_roarm_bringup_dir = get_package_share_directory('ugv_roarm_bringup')
    ugv_roarm_moveit_dir = get_package_share_directory('ugv_roarm_moveit')
    ugv_roarm_moveit_servo_dir = get_package_share_directory('ugv_roarm_moveit_servo')
    ugv_roarm_moveit_mtc_dir = get_package_share_directory('ugv_roarm_moveit_mtc_demo')
    ugv_slam_dir = get_package_share_directory('ugv_slam')
    ugv_nav_dir = get_package_share_directory('ugv_nav')

    # Define paths for different RViz configuration files
    rviz_description_config = os.path.join(ugv_roarm_description_dir, 'rviz', 'view_description.rviz')
    rviz_bringup_config = os.path.join(ugv_roarm_bringup_dir, 'rviz', 'view_bringup.rviz')
    rviz_moveit_config = os.path.join(ugv_roarm_moveit_dir, 'rviz', 'interact.rviz')
    rviz_moveit_servo_config = os.path.join(ugv_roarm_moveit_servo_dir, 'rviz', 'servo_control.rviz')
    rviz_moveit_mtc_config = os.path.join(ugv_roarm_moveit_mtc_dir, 'rviz', 'mtc.rviz')
    rviz_slam_2d_config = os.path.join(ugv_slam_dir, 'rviz', 'view_slam_2d.rviz')
    rviz_slam_3d_config = os.path.join(ugv_slam_dir, 'rviz', 'view_slam_3d.rviz')
    rviz_nav_2d_config = os.path.join(ugv_nav_dir, 'rviz', 'view_nav_2d.rviz')
    rviz_nav_3d_config = os.path.join(ugv_nav_dir, 'rviz', 'view_nav_3d.rviz')

    # Map configuration options to corresponding RViz files
    config_map = {
        'description': rviz_description_config,
        'bringup': rviz_bringup_config,
        'moveit': rviz_moveit_config,
        'moveit_servo': rviz_moveit_servo_config,
        'moveit_mtc': rviz_moveit_mtc_config,
        'slam_2d': rviz_slam_2d_config,
        'slam_3d': rviz_slam_3d_config,
        'nav_2d': rviz_nav_2d_config,
        'nav_3d': rviz_nav_3d_config
    }

    # Return the corresponding RViz configuration file, defaulting to 'description'
    return config_map.get(rviz_config, rviz_description_config)
    
class RoarmMoveItConfig:
    def __init__(self, moveit_config, ros2_controllers):
        self.moveit_config = moveit_config
        self.ros2_controllers = ros2_controllers
        
def get_moveit_config(robot_name: str):
    base_path = f"config/{robot_name}"

    moveit_config = (
        MoveItConfigsBuilder(robot_name, package_name="ugv_roarm_moveit")
        #.robot_description(file_path=f"config/ugv_roarm.urdf.xacro")
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
    add_depth_camera = context.launch_configurations['add_depth_camera']
    use_sim_time = context.launch_configurations.get('use_sim_time', 'false').lower() in ('true', '1')
    sim_time_param = {'use_sim_time': use_sim_time}
    
    share_dir = get_package_share_directory('ugv_roarm_moveit')    
    UGV_MODEL = os.environ['UGV_MODEL']
    ROARM_MODEL = os.environ['ROARM_MODEL']
    GRIPPER_TYPE = os.environ['GRIPPER_TYPE']
    
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
               "gripper_type": GRIPPER_TYPE,
               } 
               
    robot_description_config = xacro.process_file(xacro_file, mappings=mappings)
    robot_description = robot_description_config.toxml()
    
    moveit_config = get_moveit_config(ROARM_MODEL)
            
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'robot_description': robot_description},
            sim_time_param,
        ]
    )

    move_group_configuration = {
        "publish_robot_description_semantic": True,
        "allow_trajectory_execution": LaunchConfiguration("allow_trajectory_execution"),
        # Note: Wrapping the following values is necessary so that the parameter value can be the empty string
        "capabilities": ParameterValue(LaunchConfiguration("capabilities"), value_type=str),
        "disable_capabilities": ParameterValue(LaunchConfiguration("disable_capabilities"), value_type=str),
        # Publish the planning scene of the physical robot so that rviz plugin can know actual robot
        "publish_planning_scene": LaunchConfiguration("publish_monitored_planning_scene"),
        "publish_geometry_updates": LaunchConfiguration("publish_monitored_planning_scene"),
        "publish_state_updates": LaunchConfiguration("publish_monitored_planning_scene"),
        "publish_transforms_updates": LaunchConfiguration("publish_monitored_planning_scene"),
        "monitor_dynamics": False,
    }
        
    move_group_params = [
        moveit_config.moveit_config.to_dict(),
        move_group_configuration,
        {'robot_description': robot_description},
        sim_time_param,
    ]    

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=move_group_params,
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            moveit_config.ros2_controllers,
            sim_time_param,
        ],
        remappings=[
            ("/controller_manager/robot_description", "/robot_description"),
        ],
    )
    
    controller_nodes = []           
    controller_names = moveit_config.moveit_config.trajectory_execution.get(
        "moveit_simple_controller_manager", {}
    ).get("controller_names", [])
             
    for controller in controller_names + ["joint_state_broadcaster"]:
        controller_nodes.append(Node(
            package='controller_manager',
            executable='spawner',
            arguments=[controller],
            parameters=[sim_time_param],
        ))

    # Get the appropriate RViz configuration file
    rviz_config_file = get_rviz_config_file(context)

    rviz_parameters = [
        moveit_config.moveit_config.planning_pipelines,
        moveit_config.moveit_config.robot_description_kinematics,
        moveit_config.moveit_config.joint_limits,
        sim_time_param,
    ]
    
    # Define the RViz2 node to launch RViz if enabled
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        parameters=rviz_parameters,
    )
             
    # Return a list of nodes to launch
    return [
        robot_state_publisher_node,
        move_group_node,
        ros2_control_node,
        *controller_nodes,
        rviz2_node,
    ]

# Function to generate the launch description with configurable arguments
def generate_launch_description():
    return LaunchDescription([
        # Argument to specify whether to use RViz
        DeclareLaunchArgument('use_rviz', default_value='false', description='Whether to launch RViz2'),
        # Argument to specify which RViz configuration to use
        DeclareLaunchArgument('rviz_config', default_value='moveit', description='Choose which rviz configuration to use: description, bringup, moveit, moveit_servo, moveit_mtc, slam_2d, slam_3d, nav_2d, nav_3d'),
        DeclareLaunchArgument('add_camera', default_value='false', description='Choose whether to add camera'),   
        DeclareLaunchArgument('add_depth_camera', default_value='false', description='Choose whether to add depth camera'),
        DeclareLaunchArgument('use_sim_time', default_value='false', description='Use /clock (Gazebo)'),
        DeclareBooleanLaunchArg("allow_trajectory_execution", default_value=True),
        DeclareBooleanLaunchArg("publish_monitored_planning_scene", default_value=True),
        DeclareLaunchArgument("capabilities",default_value=""),
        DeclareLaunchArgument("disable_capabilities",default_value=""),
        DeclareBooleanLaunchArg("monitor_dynamics", default_value=False),
           
        # Opaque function to execute the setup
        OpaqueFunction(function=launch_setup)
    ])