import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory,get_package_share_path
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    # Declare launch arguments
    pub_odom_tf_arg = DeclareLaunchArgument(
        'pub_odom_tf', default_value='false',
        description='Whether to publish the tf from the original odom to the base_footprint'
    )

    use_ekf_arg = DeclareLaunchArgument(
        'use_ekf', default_value='true',
        description='Whether to use ekf'
    )

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='false',
        description='Whether to launch RViz2'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='bringup', 
        description='Choose which rviz configuration to use: description, bringup, moveit, moveit_servo, moveit_mtc, slam_2d, slam_3d, nav_2d, nav_3d'
    )
    
    moveit_config_arg = DeclareLaunchArgument(
        'use_moveit_servo', default_value='false', 
        description='Whether to launch moveit'
    )

    add_camera_arg = DeclareLaunchArgument(
        'add_camera', default_value='false',
        description='Include USB camera links in URDF (camera_link TF for vision pick-place)',
    )

    add_depth_camera_arg = DeclareLaunchArgument(
        'add_depth_camera', default_value='false',
        description='Include depth camera in URDF (roarm_m3 hand OAK / chassis OAK policy)',
    )

    ekf_config = os.path.join(              
        get_package_share_directory('ugv_bringup'),
        'config',
        'ekf.yaml'
    )
    
    #Include the robot state launch from the ugv_description package
    robot_state_launch = IncludeLaunchDescription(
         PythonLaunchDescriptionSource(
             os.path.join(get_package_share_directory('ugv_roarm_description'), 'launch', 'display.launch.py')
         ),
         launch_arguments={
             'use_rviz': LaunchConfiguration('use_rviz'),
             'rviz_config': LaunchConfiguration('rviz_config'),
             'add_camera': LaunchConfiguration('add_camera'),
             'add_depth_camera': LaunchConfiguration('add_depth_camera'),
         }.items(),
         condition=UnlessCondition(LaunchConfiguration('use_moveit_servo')),
     )

    robot_state_moveit_servo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_roarm_moveit_servo'), 'launch', 'servo_control.launch.py')
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
            'add_camera': LaunchConfiguration('add_camera'),
            'add_depth_camera': LaunchConfiguration('add_depth_camera'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_moveit_servo')),
    )

    # Include laser lidar launch file
    laser_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ldlidar'), 'launch', 'ldlidar.launch.py')
        ),
        launch_arguments={
            'use_rviz': "false",
            'port_name': "/dev/ttyACM0",
        }.items(),
    )

    # Include laser odometry launch file
    rf2o_laser_odometry_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rf2o_laser_odometry'), 'launch', 'rf2o_laser_odometry.launch.py')
        )
    )

    # Define the nodes to be launched
    bringup_node = Node(
        package='ugv_roarm_bringup',
        executable='ugv_roarm_bringup',        
        parameters=[{
            'serial_port': '/dev/ttyAMA0',
            'baud_rate': 115200
        }]
    )

    # Define the nodes to be launched
    base_node = Node(
        package='ugv_bringup',
        executable='odom_publisher',
        parameters=[{
            'odom_frame': 'odom',
            'base_footprint_frame': 'base_footprint',
            'pub_odom_tf': LaunchConfiguration('pub_odom_tf'),
        }],
        condition=IfCondition(LaunchConfiguration('use_ekf'))
    )

    # Define the nodes to be launched
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config],
        remappings=[('/odometry/filtered', '/odom')],
        condition=IfCondition(LaunchConfiguration('use_ekf'))
    )  

    # Return the launch description with all defined actions
    return LaunchDescription([
        pub_odom_tf_arg,
        use_ekf_arg,
        use_rviz_arg,
        moveit_config_arg,
        rviz_config_arg,
        add_camera_arg,
        add_depth_camera_arg,
        robot_state_launch,
        robot_state_moveit_servo_launch,
        bringup_node,
        # laser_bringup_launch,
        # rf2o_laser_odometry_launch,
        base_node,
        # ekf_node,     
    ])
