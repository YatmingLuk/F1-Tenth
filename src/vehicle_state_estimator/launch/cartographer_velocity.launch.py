from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='vehicle_state_estimator',
            executable='cartographer_velocity',
            name='cartographer_velocity',
            output='screen',
            parameters=[{
                'target_frame': 'map',
                'source_frame': 'base_link',
                'window_time': 1.0,
                'deadband': 0.005,
                'publish_rate': 20.0,
            }],
        ),
    ])
