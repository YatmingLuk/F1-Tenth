import math
import unittest

from vehicle_state_estimator.motion_math import (
    estimate_planar_motion,
    quaternion_to_yaw,
)


class MotionMathTest(unittest.TestCase):

    def test_estimates_planar_speed_and_direction(self):
        speed, vx, vy, direction = estimate_planar_motion(
            0.0, 0.0, 0.3, 0.4, 1.0, 0.005)
        self.assertAlmostEqual(speed, 0.5)
        self.assertAlmostEqual(vx, 0.3)
        self.assertAlmostEqual(vy, 0.4)
        self.assertAlmostEqual(direction, 53.130102, places=6)


    def test_deadband_zeros_stationary_jitter(self):
        self.assertEqual(
            estimate_planar_motion(0.0, 0.0, 0.003, 0.0, 1.0, 0.005),
            (0.0, 0.0, 0.0, 0.0))


    def test_quaternion_to_yaw(self):
        yaw = math.radians(-16.0)
        value = math.degrees(quaternion_to_yaw(
            0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)))
        self.assertAlmostEqual(value, -16.0)


if __name__ == '__main__':
    unittest.main()
