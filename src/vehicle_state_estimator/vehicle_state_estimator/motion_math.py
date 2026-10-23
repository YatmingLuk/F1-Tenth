"""Pure motion-estimation math used by the ROS 2 node."""

import math


def quaternion_to_yaw(x, y, z, w):
    """Return yaw in radians from a quaternion."""
    sin_yaw = 2.0 * (w * z + x * y)
    cos_yaw = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(sin_yaw, cos_yaw)


def estimate_planar_motion(old_x, old_y, x, y, dt, deadband):
    """Return speed, vx, vy, and movement direction for two poses."""
    if dt <= 0.0:
        raise ValueError('dt must be positive')
    if deadband < 0.0:
        raise ValueError('deadband must be non-negative')

    vx = (x - old_x) / dt
    vy = (y - old_y) / dt
    speed = math.hypot(vx, vy)
    if speed < deadband:
        return 0.0, 0.0, 0.0, 0.0

    direction_deg = math.degrees(math.atan2(vy, vx))
    return speed, vx, vy, direction_deg


def project_forward_speed(vx, vy, heading):
    """Project map-frame velocity onto the vehicle's forward body axis."""
    return vx * math.cos(heading) + vy * math.sin(heading)


def wrapped_angle_difference_degrees(direction, heading):
    """Return direction minus heading, wrapped to [-180, 180) degrees."""
    return (direction - heading + 180.0) % 360.0 - 180.0
