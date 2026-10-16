# Weekly F1TENTH Improvements - October 11-15, 2026

**Author:** Yiming Lu

**Platform:** F1TENTH, ROS 2 Humble, Linux

**Validation status:** The implementation and results marked complete below were validated on
the physical vehicle. Synchronized VESC comparison and sensor fusion remain planned work.

## Outcome

This week added real-time vehicle motion estimation from Cartographer's `map -> base_link`
pose. The new `vehicle_state_estimator` package publishes planar speed, map-frame X/Y velocity,
movement direction, and heading without using VESC motor speed.

The final real-car configuration uses a 1.0 s pose-history window and a 0.005 m/s deadband.
After a clean sensor and Cartographer restart, the output remained at 0.0 m/s while stationary
and responded continuously during manual translation, with representative samples from about
0.10 to 0.13 m/s and a peak near 0.186 m/s.

## Current architecture

```mermaid
flowchart LR
    LIDAR[Hokuyo /scan ~10 Hz] --> CARTO[Cartographer]
    IMU[VESC IMU /sensors/imu/raw ~50 Hz] --> CARTO
    TF[Static base_link to laser and imu TF] --> CARTO
    CARTO -->|map to base_link| EST[cartographer_velocity]
    EST --> SPEED[/cartographer_velocity/speed]
    EST --> VX[/cartographer_velocity/vx]
    EST --> VY[/cartographer_velocity/vy]
    EST --> DIR[/cartographer_velocity/movement_direction]
    EST --> HEAD[/cartographer_velocity/heading]
```

Cartographer remains the owner of the dynamic `map -> odom -> base_link` TF chain. The new
node only reads TF and publishes scalar diagnostic topics; it does not publish another TF.

## Code and change locations

| Location | Change | Reason |
| --- | --- | --- |
| `src/vehicle_state_estimator/vehicle_state_estimator/cartographer_velocity.py` | Added TF lookup, timestamped pose history, filtering, and five publishers | Convert Cartographer pose changes into live planar motion signals |
| `src/vehicle_state_estimator/vehicle_state_estimator/motion_math.py` | Isolated quaternion/yaw and pose-difference calculations | Keep the numerical behavior testable without a running ROS graph |
| `src/vehicle_state_estimator/launch/cartographer_velocity.launch.py` | Added launch configuration with the validated defaults | Make the real-car settings repeatable |
| `src/vehicle_state_estimator/package.xml`, `setup.py`, `setup.cfg` | Added the ROS 2 Python package metadata and executable entry point | Allow `colcon` to build and `ros2 run/launch` to discover the node |
| `README.md` and `docs/OPERATIONS.md` | Updated architecture, launch sequence, topics, validation, and recovery steps | Keep repository instructions aligned with the current vehicle stack |

## Implemented calculation

For two Cartographer poses separated by `dt`, the node calculates:

```python
vx = (x - old_x) / dt
vy = (y - old_y) / dt
speed = math.hypot(vx, vy)
movement_direction_deg = math.degrees(math.atan2(vy, vx))
heading_deg = math.degrees(quaternion_to_yaw(qx, qy, qz, qw))
```

If `speed < deadband`, speed, `vx`, `vy`, and movement direction are published as zero.
Heading still comes directly from the latest Cartographer orientation.

The node rejects duplicate TF timestamps, requires a positive time interval, and waits without
publishing when `map -> base_link` is unavailable. Its main parameters are:

| Parameter | Validated default | Purpose |
| --- | ---: | --- |
| `target_frame` | `map` | Frame in which translation and direction are measured |
| `source_frame` | `base_link` | Vehicle body frame |
| `window_time` | `1.0 s` | Pose-difference interval used to reduce jitter |
| `deadband` | `0.005 m/s` | Stationary-noise suppression threshold |
| `publish_rate` | `20.0 Hz` | TF polling rate; output only advances with a new TF timestamp |

## Why the filter changed

The initial 0.5 s window and 0.010 m/s deadband allowed stationary spikes near
0.010-0.020 m/s. Raising the deadband to 0.025 m/s removed those spikes but also suppressed
a deliberately slow push averaging about 0.0184 m/s. The final 1.0 s window with a
0.005 m/s deadband suppressed stationary jitter while preserving slow translation.

The longer window trades faster response for stability. The result is a pose-derived estimate,
not ground-truth speed, and can still be affected by localization jitter and scan-matching
corrections.

## Real-car validation

| Measurement or condition | Observed result |
| --- | --- |
| VESC IMU | Approximately 49.99-50.00 Hz |
| Hokuyo LiDAR | Approximately 9.96-10.00 Hz |
| Cartographer pose | Continuously updating `map -> base_link` |
| Stationary speed after final restart/tuning | 0.0 m/s |
| Manual translation | Approximately 0.10-0.13 m/s; peak near 0.186 m/s |
| Velocity components | `vx` dominant and `vy` smaller during the recorded map-axis motion |
| Movement direction and heading | Both updated in real time |

Representative recorded speed values were `0.0734`, `0.1158`, `0.1264`, `0.1275`,
`0.1682`, and `0.1859 m/s`. A recorded movement direction was near -72.55 degrees, while
a separate heading sequence changed from about -13 to -16 degrees. Those angle sequences were
not captured synchronously and therefore are not treated as a valid angular-error measurement.

## Build and run

```bash
cd ~/newf1_ws
colcon build --packages-select vehicle_state_estimator --symlink-install
source install/setup.bash
ros2 launch vehicle_state_estimator cartographer_velocity.launch.py
```

Confirm the Cartographer input and output topics:

```bash
ros2 run tf2_ros tf2_echo map base_link
ros2 topic echo /cartographer_velocity/speed
ros2 topic echo /cartographer_velocity/vx
ros2 topic echo /cartographer_velocity/vy
ros2 topic echo /cartographer_velocity/movement_direction
ros2 topic echo /cartographer_velocity/heading
```

## USB/IMU interruption and recovery

During testing, `/sensors/imu/raw` temporarily lost its publisher after the VESC serial device
disappeared. Without IMU input, Cartographer no longer produced the map frame, so the motion
estimator correctly stopped publishing. Linux still saw the STMicroelectronics/ChibiOS USB
device, and kernel logs later showed `ttyACM1` rebinding through `cdc_acm`.

Useful checks are:

```bash
ros2 node list | grep vesc
ros2 topic info /sensors/imu/raw --verbose
ls -l /dev/serial/by-id/
lsusb | grep -i -E "STMicro|ChibiOS"
sudo dmesg | tail -n 40
```

Restart the VESC driver first and confirm the approximately 50 Hz IMU stream, then restart
Cartographer and the motion estimator cleanly.

## Work intentionally left for the next stage

- Complete and validate one synchronized logger for speed, `vx`, `vy`, movement direction,
  heading, and their angular difference. An initial edit placed a variable outside its scope;
  that output is not represented here as completed.
- Run one controlled sequence without repositioning the vehicle: stationary, straight
  translation, then in-place rotation.
- Calibrate VESC ERPM-to-m/s conversion and record VESC and Cartographer speed simultaneously.
- Measure stationary drift, response delay, and the effect of other windows/deadbands.
- Evaluate an EKF or `robot_localization` only after both independent estimates are synchronized
  and individually characterized.

The uploaded Personal Research Journal PDF is preserved beside this file as the original weekly
record. This Markdown version ties its results to the exact repository locations and separates
validated implementation from planned experiments.
