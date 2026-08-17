import os
import xacro
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
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

# Function to get the appropriate RViz configuration file based on the input parameter
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

def launch_setup(context, *args, **kwargs):
    rviz_config = context.launch_configurations['rviz_config']
    add_camera = context.launch_configurations['add_camera']
    add_depth_camera = context.launch_configurations['add_depth_camera']
    load_controller = LaunchConfiguration('load_controller', default=True)
  
    share_dir = get_package_share_directory('ugv_roarm_moveit')
    ugv_roarm_gazebo_dir = get_package_share_directory('ugv_roarm_gazebo')
    ugv_gazebo_dir = get_package_share_directory('ugv_gazebo')
    UGV_MODEL = os.environ['UGV_MODEL']
    ROARM_MODEL = os.environ['ROARM_MODEL']
    GZ_VERSION = os.environ['GZ_VERSION']
    GRIPPER_TYPE = os.environ['GRIPPER_TYPE']

    moveit_config = get_moveit_config(ROARM_MODEL)
    
    xacro_file = os.path.join(
        share_dir,
        'config', 
        'ugv_roarm.urdf.xacro')    

    mappings = {
                "use_gazebo": "true",
                "GZ_VERSION": GZ_VERSION,
                "ugv_model": UGV_MODEL,
                "roarm_model": ROARM_MODEL,
                "gripper_type": GRIPPER_TYPE,
                "add_camera": add_camera,
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
        
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        parameters=[{"use_sim_time": True}],
    )

    controller_nodes = []           
    controller_names = moveit_config.moveit_config.trajectory_execution.get(
        "moveit_simple_controller_manager", {}
    ).get("controller_names", [])
             
    if load_controller.perform(context) in ('True', 'true'):
        for controller in controller_names:
            controller_nodes.append(Node(
                package='controller_manager',
                executable='spawner',
                output='screen',
                arguments=[
                    controller,
                    '--controller-manager', '/controller_manager'
                ],
                parameters=[{'use_sim_time': True}],
            ))

    # Get the appropriate RViz configuration file
    rviz_config_file = get_rviz_config_file(context)

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
        arguments=["-d", rviz_config_file],
        parameters=rviz_parameters,
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
        ],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    world = os.path.join(ugv_gazebo_dir,'worlds','ugv.world')
    models_path = os.path.join(ugv_gazebo_dir, 'models')

    gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH',
        value=models_path + ':' + os.environ.get('GAZEBO_MODEL_PATH', '')
    )

    ign_model_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=models_path + ':' + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    )

    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzserver.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world,
        }.items()
    )

    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gzclient.launch.py'
            ])
        ])
    )

    urdf_spawn_node = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'ugv_roarm',
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    gzserver_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"), 
                "launch", 
                "gz_sim.launch.py"
            ]),
        ]),
        launch_arguments={
            'gz_args': ['-r -v4 ', world], 
            'on_exit_shutdown': 'true'
        }.items(),
    )

    ign_gazebo_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{
            'config_file': os.path.join(ugv_roarm_gazebo_dir, 'config', 'ros_gz_bridge.yaml'),
            'qos_overrides./tf_static.publisher.durability': 'transient_local',
        }],
    )

    spawn_robot_node = Node(
        package="ros_gz_sim",
        executable="create",
        name='create',
        arguments=[
            "-topic", "robot_description",
            "-name", 'ugv_roarm',
            "-robot_namespace", '',
            "-x", '0.0',
            "-y", '0.0',
            "-z", '0.0',
            '-allow_renaming', 'true'
        ],
        output="screen"
    )

    nodes = [        
        robot_state_publisher_node,
    ]

    if GZ_VERSION == 'classic':
        nodes.extend([        
            gazebo_model_path,
            gazebo_server,
            gazebo_client,
            urdf_spawn_node,
        ])

    elif GZ_VERSION == 'harmonic':
        nodes.extend([        
            ign_model_path,
            gzserver_node,
            ign_gazebo_bridge,
            spawn_robot_node,
        ])

    nodes.extend([        
        joint_state_broadcaster_spawner,
        *controller_nodes,
        rviz2_node,
    ])

    return nodes

def generate_launch_description():
    return LaunchDescription([
        # Argument to specify whether to use RViz
        DeclareLaunchArgument('use_rviz', default_value='false', description='Whether to launch RViz2'),
        # Argument to specify which RViz configuration to use
        DeclareLaunchArgument('rviz_config', default_value='description', description='Choose which rviz configuration to use: description, bringup, slam_2d, slam_3d, nav_2d, nav_3d'),
        DeclareLaunchArgument('add_depth_camera', default_value='false', description='Choose whether to add depth camera'),      
        DeclareLaunchArgument('add_camera', default_value='false', description='Choose whether to add camera'),      
        # Opaque function to execute the setup
        OpaqueFunction(function=launch_setup)
    ])
