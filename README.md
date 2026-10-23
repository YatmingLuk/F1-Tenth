# F1Tenth Autonomous Racing Platform

This repository contains our ROS 2 F1Tenth vehicle stack for localization, mapping,
trajectory generation, vehicle control, and autonomous-racing experiments. The current
milestone integrates the VESC IMU and Hokuyo LiDAR into Cartographer and publishes a
real-time vehicle pose and occupancy grid for RViz 2.

## Current milestone: LiDAR-IMU localization

- VESC IMU published as `sensor_msgs/msg/Imu` on `/sensors/imu/raw` at approximately 50 Hz.
- Hokuyo LiDAR published as `sensor_msgs/msg/LaserScan` on `/scan` at approximately 10 Hz.
- Static transforms connect `base_link` to the `imu` and `laser` sensor frames.
- Cartographer consumes both sensor streams and publishes `map -> odom -> base_link` TF (the composed transform gives vehicle pose).
- The occupancy grid is published on `/map` at 1 Hz for real-time RViz 2 visualization.
- VESC acceleration and angular velocity are converted to ROS-standard units: m/s^2 and rad/s.
- VESC odometry applies a configurable `speed_deadband` of `0.05 m/s`; set it to `0.0` for low-speed comparison runs.
- The VESC launch file accepts a `port` override so the vehicle can use a stable `/dev/serial/by-id/...` device path.

The implementation details and validation results are documented in
[LiDAR-IMU Cartographer integration](docs/IMU_LIDAR_CARTOGRAPHER.md).

## Expected system architecture

![Expected ROS 2 architecture for the F1Tenth vehicle](docs/assets/f1tenth-architecture.png)

The diagram shows the intended end-to-end architecture, from LiDAR-based mapping and
waypoint generation to pure pursuit, overtaking decisions, VESC control, and the physical car.
The current sensor, localization, low-speed odometry, USB-identification, and
Cartographer-derived motion-estimation changes were validated on the physical vehicle under
Linux. The current estimator also projects map-frame velocity onto the vehicle body axis to
publish signed forward speed. Higher-level autonomous behavior and synchronized VESC
calibration/fusion remain the next stage.

### Localization data flow

```mermaid
flowchart LR
    USB[VESC USB device] --> DRIVER[vesc_driver_node]
    DRIVER -->|/sensors/imu/raw| CARTO[Cartographer]
    DRIVER -->|/sensors/core| ODOM[Optional vesc_to_odom_node]
    HOKUYO[One urg_node_driver] -->|/scan| CARTO
    TF[Static TF: base_link to imu/laser] --> CARTO
    ODOM -->|/vesc/odom, publish_tf=false| COMPARE[Velocity comparison]
    CARTO -->|map to base_link pose| STATE[vehicle_state_estimator]
    STATE -->|speed, vx, vy, direction, heading, forward speed| MOTION[Motion topics]
    CARTO -->|/map| RVIZ[RViz 2]
    CARTO -->|map to odom to base_link TF| RVIZ
```

### Runtime ownership and configuration

| Component | Current responsibility |
| --- | --- |
| `vesc_driver_node` | Opens the configured VESC USB device and publishes `/sensors/core` and ROS-unit IMU data on `/sensors/imu/raw` |
| `urg_node_driver` | Runs once through `robot.launch.py` and publishes `/scan` at approximately 10 Hz |
| Static TF publishers | Publish `base_link -> imu` and `base_link -> laser` |
| Cartographer | Consumes `/scan` and `/sensors/imu/raw` and owns the dynamic `map -> odom -> base_link` transform |
| `cartographer_velocity` | Differentiates `map -> base_link` over a 1.0 s window and publishes speed, map-frame velocity components, movement direction, heading, and signed forward speed |
| `vesc_to_odom_node` | Optional comparison source; uses configurable `speed_deadband` and must run with `publish_tf:=false` beside Cartographer |

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/vesc` | VESC driver, messages, and Ackermann bridge |
| `src/my_robot_bringup` | Hokuyo launch and static sensor transforms |
| `src/my_cartographer_config` | Cartographer launch and 2D SLAM configuration |
| `src/vehicle_state_estimator` | Cartographer pose-derived speed, velocity components, movement direction, heading, and signed forward speed |
| `src/car_control` | Drive bridge, waypoint logging, and pure pursuit |
| `src/map_to_centerline` | Centerline extraction from a saved map |
| `docs/OPERATIONS.md` | Build, launch, validation, mapping, and driving commands |
| `docs/IMU_LIDAR_CARTOGRAPHER.md` | Sensor-fusion changes, rationale, results, and limits |
| `docs/research/2026-10-10-weekly-improvements.md` | Weekly architecture, change locations, code excerpts, and velocity plan |
| `docs/research/2026-10-10-code-diff.patch` | Exact new code/config changes against the reviewed base |
| `docs/research/2026-10-15-weekly-improvements.md` | This week's implementation, real-car results, code locations, and next comparison plan |
| `docs/research/2026-10-15-personal-research-journal.pdf` | Original weekly Personal Research Journal by Yiming Lu |
| `docs/research/2026-10-15-code-diff.patch` | Exact estimator and documentation changes against the previous `main` revision |
| `docs/research/2026-10-23-weekly-improvements.md` | Powered field-test results, signed forward-speed implementation, code locations, and next calibration plan |
| `docs/research/2026-10-23-personal-research-journal.pdf` | Original October 23 Personal Research Journal by Yiming Lu |
| `docs/research/2026-10-23-code-diff.patch` | Exact October 23 code and documentation changes against the previous `main` revision |

## Requirements

- Ubuntu with ROS 2 Humble
- Cartographer ROS
- Hokuyo `urg_node`
- `tf2_ros`, `sensor_msgs`, `nav2_map_server`, and RViz 2
- A configured VESC and Hokuyo LiDAR connected to the F1Tenth vehicle

## Build

```bash
cd ~/newf1_ws
colcon build
source install/setup.bash
```

## Quick start

Use separate terminals for the main processes:

```bash
# Terminal 1: VESC and IMU
VESC_PORT='/dev/serial/by-id/<verified-vesc-id>'
ros2 launch vesc_driver vesc_driver_node.launch.py port:="$VESC_PORT"

# Terminal 2: drive-command bridge
ros2 run car_control drive_to_vesc_bridge --ros-args -r /drive:=/ackermann_cmd

# Terminal 3: LiDAR and static transforms
ros2 launch my_robot_bringup robot.launch.py

# Terminal 4: LiDAR-IMU Cartographer
ros2 launch my_cartographer_config cartographer.launch.py

# Terminal 5: Cartographer-derived vehicle motion
ros2 launch vehicle_state_estimator cartographer_velocity.launch.py
```

The estimator publishes `/cartographer_velocity/speed`, `/vx`, `/vy`,
`/movement_direction`, `/heading`, and `/forward_speed`. Its validated defaults are a
`1.0 s` pose-history window and a `0.005 m/s` deadband. `forward_speed` is the map-frame
velocity projected onto the vehicle heading, so forward and reverse motion have opposite signs.

If `port` is omitted or empty, the driver keeps the YAML-configured port (currently
`/dev/ttyACM1`). Find the stable device name with `ls -l /dev/serial/by-id/` and verify it
before launch.

For a wheel-speed odometry comparison beside Cartographer, run:

```bash
ros2 run vesc_ackermann vesc_to_odom_node --ros-args \
  --params-file vesc_odom_calibrated.yaml \
  -p speed_deadband:=0.05 \
  -p publish_tf:=false \
  -p use_servo_cmd_to_calc_angular_velocity:=false \
  -r odom:=/vesc/odom
```

The parameter file must contain the measured `speed_to_erpm_gain` and
`speed_to_erpm_offset`. Use `speed_deadband:=0.0` only for the low-speed comparison run. Keeping
`publish_tf:=false` prevents the comparison node from competing with Cartographer for the
`odom -> base_link` transform.

Before each command, run `source ~/newf1_ws/install/setup.bash`. Do not start a second
`urg_node` manually while `robot.launch.py` is running; duplicate drivers caused the LiDAR
rate to fall from approximately 10 Hz to an intermittent 0.06-0.17 Hz during testing.

See [Vehicle operations](docs/OPERATIONS.md) for SSH setup, ROS domain configuration,
RViz checks, map saving, centerline generation, teleoperation, and pure pursuit.

## Validation snapshot

| Signal | Observed rate | Status |
| --- | ---: | --- |
| VESC IMU | 49.993-50.001 Hz | Stable |
| Hokuyo LiDAR | 10.002-10.005 Hz | Stable after duplicate driver removal |
| Occupancy grid `/map` | 1.000 Hz | Stable |
| Cartographer-derived speed | 0.426-0.726 m/s for the reported moving samples in the powered test | Responsive during remote-controlled driving |
| Direction-heading agreement | Within +/-10 degrees for 13 of 15 displayed powered-test samples | Internally consistent; no external ground truth |
| Signed forward speed | Approximately +0.29 and -0.33 m/s during manual forward/reverse checks | Forward and reverse signs verified |
| VESC comparison | VESC about -0.158 to -0.295 m/s while Cartographer forward speed was positive | Sign mismatch identified; comparison not synchronized |

Cartographer was observed subscribing to both `/scan` and `/sensors/imu/raw`, while the
`map -> base_link` transform updated continuously. The documented sensor, TF, frequency,
deadband, USB-port, and pose-derived motion changes were validated on the vehicle under Linux.
The powered test establishes functional, real-time consistency, not absolute accuracy: no
independent ground truth was recorded. Synchronized comparison, forward-sign alignment, and
calibration of the provisional VESC gain `4614.0` remain next-stage work.

## Research record

[Weekly improvements (October 5-10, 2026)](docs/research/2026-10-10-weekly-improvements.md)
consolidates existing sensor integration with configurable low-speed odometry, USB identification,
and the next Cartographer-only velocity experiment. The recorded code and architecture changes
were validated on the physical vehicle under Linux; the velocity estimator is a planned follow-up.


The detailed October 1, 2026 experiment log is available as a
[Personal Research Journal PDF](docs/research/2026-10-01-personal-research-journal.pdf).

The detailed October 10, 2026 experiment log is available as a
[Personal Research Journal](docs/research/2026-10-10-weekly-improvements.md).

[Weekly improvements (October 11-15, 2026)](docs/research/2026-10-15-weekly-improvements.md)
documents the implemented Cartographer motion estimator, filter tuning, real-car results,
USB recovery, and the boundary between completed work and the next synchronized comparison.
The original report is preserved as a
[Personal Research Journal PDF](docs/research/2026-10-15-personal-research-journal.pdf).

[Weekly improvements (October 16-23, 2026)](docs/research/2026-10-23-weekly-improvements.md)
records the powered indoor test, the six-topic motion interface, signed forward-speed
projection, representative field measurements, the preliminary VESC sign comparison, and the
timestamp-aligned calibration plan. The source report is preserved as the
[October 23 Personal Research Journal PDF](docs/research/2026-10-23-personal-research-journal.pdf).
## Contributors

Developed by the F1Tenth project team. LiDAR-IMU integration, Cartographer configuration,
validation, and repository documentation were prepared by Yiming Lu.
