from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Start the existing configurable VESC driver once as part of sensor bringup.
    vesc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('vesc_driver'), 'launch', 'vesc_driver_node.launch.py'
        ])),
        launch_arguments={'port': LaunchConfiguration('vesc_port')}.items(),
        condition=IfCondition(LaunchConfiguration('start_vesc')),
    )
    # Hokuyo LiDAR driver.
    urg_node = Node(
        package='urg_node',
        executable='urg_node_driver',
        name='urg_node',
        parameters=[{
            'serial_port': '/dev/sensors/hokuyo', 
            # Keep the driver's native "laser" frame.
        }],
        remappings=[
            ('scan', '/scan'), 
        ]
    )
    # Static transform: base_link -> laser.
    static_tf_base_to_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_laser',
        arguments=['0.11', '0', '0.12', '0', '0', '0', 'base_link', 'laser']
    )
    
    # Static transform: base_link -> imu. The translation matches the current
    # vehicle installation; verify the rotation against the physical mounting.
    static_tf_base_to_imu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_imu',
        arguments=['-0.1', '0', '0.12', '0', '0', '0', 'base_link', 'imu']
    )

    return LaunchDescription([
        DeclareLaunchArgument('start_vesc', default_value='true',
                              description='Start VESC with sensor bringup.'),
        DeclareLaunchArgument('vesc_port', default_value='',
                              description='Verified VESC USB path; empty uses driver YAML.'),
        vesc,
        urg_node,
        static_tf_base_to_laser,
        static_tf_base_to_imu,
    ])
