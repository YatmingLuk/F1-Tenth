"""Publish planar motion estimated from the Cartographer TF pose."""

from collections import deque
import math

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import Float64
from tf2_ros import Buffer, TransformException, TransformListener

from .motion_math import estimate_planar_motion, quaternion_to_yaw


class CartographerVelocity(Node):
    """Differentiate map-to-base_link poses over a configurable window."""

    def __init__(self):
        super().__init__('cartographer_velocity')

        self.target_frame = self.declare_parameter('target_frame', 'map').value
        self.source_frame = self.declare_parameter('source_frame', 'base_link').value
        self.window_time = float(self.declare_parameter('window_time', 1.0).value)
        self.deadband = float(self.declare_parameter('deadband', 0.005).value)
        self.publish_rate = float(self.declare_parameter('publish_rate', 20.0).value)

        if not math.isfinite(self.window_time) or self.window_time <= 0.0:
            raise ValueError('window_time must be finite and positive')
        if not math.isfinite(self.deadband) or self.deadband < 0.0:
            raise ValueError('deadband must be finite and non-negative')
        if not math.isfinite(self.publish_rate) or self.publish_rate <= 0.0:
            raise ValueError('publish_rate must be finite and positive')

        self.tf_buffer = Buffer(cache_time=Duration(seconds=max(10.0, 2.0 * self.window_time)))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.samples = deque()
        self.last_tf_stamp = None
        self.warned_missing_tf = False

        prefix = '/cartographer_velocity'
        self.publishers = {
            'speed': self.create_publisher(Float64, f'{prefix}/speed', 10),
            'vx': self.create_publisher(Float64, f'{prefix}/vx', 10),
            'vy': self.create_publisher(Float64, f'{prefix}/vy', 10),
            'movement_direction': self.create_publisher(
                Float64, f'{prefix}/movement_direction', 10),
            'heading': self.create_publisher(Float64, f'{prefix}/heading', 10),
        }
        self.timer = self.create_timer(1.0 / self.publish_rate, self.update)

        self.get_logger().info(
            f'Estimating {self.target_frame} -> {self.source_frame} motion with '
            f'window_time={self.window_time:.3f}s and deadband={self.deadband:.3f}m/s')

    @staticmethod
    def _stamp_seconds(stamp):
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    def update(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                self.target_frame, self.source_frame, Time())
        except TransformException as exc:
            if not self.warned_missing_tf:
                self.get_logger().warning(
                    f'Waiting for {self.target_frame} -> {self.source_frame}: {exc}')
                self.warned_missing_tf = True
            return

        stamp = self._stamp_seconds(transform.header.stamp)
        if stamp == self.last_tf_stamp:
            return
        self.last_tf_stamp = stamp
        self.warned_missing_tf = False

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        heading_deg = math.degrees(quaternion_to_yaw(
            rotation.x, rotation.y, rotation.z, rotation.w))
        self.samples.append((stamp, translation.x, translation.y))

        while (
                len(self.samples) > 1 and
                stamp - self.samples[1][0] >= self.window_time):
            self.samples.popleft()

        old_stamp, old_x, old_y = self.samples[0]
        dt = stamp - old_stamp
        if dt < self.window_time:
            return

        speed, vx, vy, direction_deg = estimate_planar_motion(
            old_x, old_y, translation.x, translation.y, dt, self.deadband)
        values = {
            'speed': speed,
            'vx': vx,
            'vy': vy,
            'movement_direction': direction_deg,
            'heading': heading_deg,
        }
        for name, value in values.items():
            self.publishers[name].publish(Float64(data=value))


def main(args=None):
    rclpy.init(args=args)
    node = CartographerVelocity()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
