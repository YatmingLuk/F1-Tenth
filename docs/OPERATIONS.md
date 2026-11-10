# F1Tenth Vehicle Operations

This runbook consolidates the current team commands for connecting to the Jetson, launching
the ROS 2 stack, validating LiDAR-IMU localization, saving a map, and running pure pursuit.

> Keep the vehicle raised or in a clear test area while bringing up motor control. Be ready to
> stop the control node. Confirm that steering and speed limits match the vehicle configuration.

## 1. Connect to the Jetson

Connect the laptop and Jetson to the same network. On the Jetson, find its address:

```bash
hostname -I
```

From the laptop, connect with the correct Jetson account and IP address:

```bash
ssh <jetson-user>@<jetson-ip>
```

Use the same ROS domain on the Jetson and any ROS 2 laptop/WSL session:

```bash
echo "export ROS_DOMAIN_ID=0" >> ~/.bashrc
source ~/.bashrc
```

## 2. Build and source the workspace

```bash
cd ~/newf1_ws
colcon build
source install/setup.bash
```

Run the `source` command in every new terminal.

## 3. Launch the vehicle stack

### Terminal 1: VESC driver, LiDAR, and sensor TF

```bash
cd ~/newf1_ws
source install/setup.bash
VESC_PORT='/dev/serial/by-id/<confirmed-vesc-device>'
ros2 launch my_robot_bringup robot.launch.py vesc_port:="$VESC_PORT"
```

For a separately launched VESC driver, set `start_vesc:=false` on robot bringup. Do not
start a second driver on the same USB device. Keep the drive bridge stopped for the debug
procedure below; the reported Pure Pursuit test did not actuate the vehicle.

`Streaming data` in the driver output indicates that the LiDAR is running. Do not start a
second `urg_node` manually; only one driver process should access the Hokuyo sensor.

### Terminal 4: Cartographer

```bash
cd ~/newf1_ws
source install/setup.bash
ros2 launch my_cartographer_config cartographer.launch.py
```

Confirm that localization is active:

```bash
ros2 run tf2_ros tf2_echo map base_link
```

### Terminal 5: Cartographer-derived motion estimate

```bash
cd ~/newf1_ws
source install/setup.bash
ros2 launch vehicle_state_estimator cartographer_velocity.launch.py
```

The launch file uses the real-car validated settings: a `1.0 s` history window and a
`0.005 m/s` deadband. Confirm all six outputs:

```bash
ros2 topic echo /cartographer_velocity/speed
ros2 topic echo /cartographer_velocity/vx
ros2 topic echo /cartographer_velocity/vy
ros2 topic echo /cartographer_velocity/movement_direction
ros2 topic echo /cartographer_velocity/heading
ros2 topic echo /cartographer_velocity/forward_speed
```

`speed` is always non-negative. `forward_speed` is the map-frame velocity projected onto the
vehicle heading; its sign distinguishes forward and reverse motion. The node log also reports
the wrapped movement-direction-minus-heading difference used in the powered test.

If the estimator stops publishing, first check `map -> base_link`, `/scan`, and
`/sensors/imu/raw`. The estimator intentionally waits when Cartographer has no current TF.

### Terminal 6: Teleoperation

```bash
cd ~/newf1_ws
source install/setup.bash
python3 src/joy_to_vesc.py
```

## 4. Validate the sensor and SLAM pipeline

```bash
ros2 run tf2_ros tf2_echo base_link imu
ros2 topic hz /scan
ros2 topic hz /sensors/imu/raw
ros2 topic info /scan --verbose
ros2 node info /urg_node
ps aux | grep -E "urg_node|urg_node_driver"
ros2 node info /cartographer_node
ros2 run tf2_ros tf2_echo map base_link
ros2 topic list | grep map
ros2 topic hz /map
```

Open RViz 2:

```bash
rviz2
```

Set:

- Fixed Frame: `map`
- Map topic: `/map`
- LaserScan topic: `/scan`
- TF display: enabled

## 5. Save a same-session map

After mapping a closed track and obtaining a stable map, finish the active trajectory and
save the state. The reported trajectory ID was `0`; check the active ID on the running system.
Finishing a trajectory stops it from accepting new data.

```bash
ros2 service call /finish_trajectory cartographer_ros_msgs/srv/FinishTrajectory "{trajectory_id: 0}"
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState "{filename: '$HOME/track_20261105.pbstream', include_unfinished_submaps: true}"
ros2 run cartographer_ros cartographer_pbstream_to_ros_map \
  -pbstream_filename="$HOME/track_20261105.pbstream" \
  -map_filestem="$HOME/track_20261105" -resolution=0.05
```

The `.pbstream`, PGM/YAML and centerline must all come from the same mapping session.
For localization, load that matching saved state using a suitable Cartographer localization
configuration. The current `my_cartographer_config` launch does not yet provide a saved-state
localization option; loading and validating one is a next-stage task. Simply reusing the frame
name `map` does not align different session origins.
The laboratory save and conversion succeeded; closed-track mapping and localization remain pending.

## 6. Generate and inspect the centerline

```bash
PYTHONNOUSERSITE=1 ros2 run map_to_centerline generate_centerline --ros-args \
  -p yaml_path:="$HOME/track_20261105.yaml" \
  -p png_path:="$HOME/track_20261105.pgm" \
  -p output_csv:="$HOME/track_20261105_waypoints.csv"
```

Check that the waypoint file contains data:

```bash
head "$HOME/track_20261105_waypoints.csv"
tail "$HOME/track_20261105_waypoints.csv"
wc -l "$HOME/track_20261105_waypoints.csv"
```

The `PYTHONNOUSERSITE=1` workaround uses the compatible system NumPy/OpenCV pair for this
command only. The tested old-map result had 500 numeric waypoints plus one header line; it is
not suitable for a different session. A laboratory map without a closed loop did not yield a
centerline, consistent with this generator's geometry requirements.

## 7. Debug pure pursuit

Keep motor actuation disabled and stop teleoperation. Use a centerline generated from the
same saved state used for localization. Redirect the controller output to a debug-only topic:

```bash
cd ~/newf1_ws
source install/setup.bash
ros2 run car_control pure_pursuit_tf --ros-args \
  -p waypoint_csv:="$HOME/track_20261105_waypoints.csv" \
  -r /ackermann_cmd:=/debug_ackermann_cmd
```

Inspect `/debug_ackermann_cmd`, the vehicle pose, waypoint markers, target location, and
steering around the full loop. In the reported mismatch the vehicle was near `(0.09, -0.01)` m,
but the target was `(3.13, 8.71)` m and steering reached `0.450` rad. Those results demonstrate
the mismatch, not successful path following. Confirm near targets and non-saturated steering
before a supervised low-speed test; that closed-track test remains pending.

## Troubleshooting quick reference

| Symptom | Check | Likely action |
| --- | --- | --- |
| `/scan` is far below 10 Hz | Publisher count and `urg_node_driver` processes | Stop the duplicate LiDAR driver |
| `/sensors/imu/raw` has no publisher | `ros2 topic info /sensors/imu/raw --verbose` and VESC launch | Start the VESC driver once and confirm the USB path |
| `import cv2` fails with NumPy ABI errors | Check system and user-site NumPy/OpenCV versions | Use `PYTHONNOUSERSITE=1` for centerline generation; avoid global package changes |
| Pure Pursuit target is far away or steering saturates | Compare waypoint bounds to active map and pose | Regenerate from the same PBStream; keep output on the debug topic |
| `base_link` or `imu` frame is missing | `tf2_echo base_link imu` | Rebuild and launch `my_robot_bringup` |
| Cartographer has no IMU subscription | `ros2 node info /cartographer_node` | Confirm the IMU remap and `use_imu_data = true` |
| No `/map` output | Cartographer logs and sensor rates | Restore `/scan`, IMU, and required TF inputs |
| No Cartographer velocity topics | `tf2_echo map base_link` and sensor publishers | Restore Cartographer TF, then restart the estimator |
| Vehicle does not respond | VESC driver, bridge, and topic remap | Confirm both control nodes are active |

## Weekly follow-up: USB, low-speed odometry, and TF

The [October 10 Research Journal](research/2026-10-10-research-journal.md) contains
the architecture, code locations, reasons, full code diffs, historical measurements,
and the next Cartographer-only velocity experiment.

Before starting VESC, identify its USB device rather than assuming `ttyACM1`:

```bash
lsusb
ls -l /dev/serial/by-id/ /dev/serial/by-path/
readlink -f /dev/sensors/hokuyo
udevadm info --query=property --name=/dev/ttyACM1
```

Match the identity and physical device to VESC, then use its confirmed stable path:

```bash
VESC_PORT='/dev/serial/by-id/<confirmed-vesc-device>'
ros2 launch my_robot_bringup robot.launch.py vesc_port:="$VESC_PORT"
```

Omitting `vesc_port` preserves the port in the driver YAML. For a custom driver configuration,
launch the driver separately with `config:=...` and use `start_vesc:=false` for robot bringup.
Do not run `vesc_full_bridge.py` or VESC Tool against the same USB device while the C++
driver is active. The repository udev helper/rules require installation and a verified
device identity before use.

For VESC speed comparison, use a file containing measured `speed_to_erpm_gain` and
`speed_to_erpm_offset`, publish odometry on its own topic, and disable its TF:

```bash
ros2 run vesc_ackermann vesc_to_odom_node --ros-args \
  --params-file vesc_odom_calibrated.yaml \
  -p speed_deadband:=0.05 -p publish_tf:=false \
  -p use_servo_cmd_to_calc_angular_velocity:=false \
  -r odom:=/vesc/odom
```

This speed-only mode avoids waiting for a servo command; it does not estimate steering
angular velocity. Compare a second run with `speed_deadband:=0.0` after stopping the first
node. The default remains 0.05 m/s. The existing XML launch uses placeholder calibration
and enables TF, so use the explicit command above for this experiment.

Cartographer currently owns `map -> odom -> base_link` with `use_odometry = false`.
Confirm both links independently:

```bash
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
```

The implemented velocity node differentiates timestamped `map -> base_link` poses over a
1.0 s window. Global map corrections can affect the estimate. The October 23 powered test
verified all six outputs and identified an opposite forward sign between VESC odometry and
Cartographer. Before fusion, record ERPM, VESC speed, Cartographer speed, and an independent
distance/time reference with ROS timestamps; then align sign, estimate delay, and calibrate the
provisional `speed_to_erpm_gain` value `4614.0`.
