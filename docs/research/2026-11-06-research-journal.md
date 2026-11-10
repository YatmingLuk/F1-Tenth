# F1TENTH Weekly Research Journal - November 6, 2026

**Author:** Yiming Lu

**Platform:** F1TENTH, ROS 2 Humble, Linux

The [original report](2026-11-06-research-journal.pdf) records vehicle-side testing of
centerline generation, localization recovery, Pure Pursuit debugging, and the map-save
procedure. Motor actuation was disabled during the reported controller check. This repository
update adapts the reported VESC launch recovery to the existing configurable launch file; the
full vehicle-side source snapshot was not supplied, so this adaptation is not a verbatim copy.

## Findings and status

| Investigation | Reported evidence | Interpretation |
| --- | --- | --- |
| Centerline Python environment | User-site NumPy 2.2.6 failed to import system OpenCV; `PYTHONNOUSERSITE=1` selected NumPy 1.21.5 and OpenCV 4.5.4 | Scoped workaround; no global package downgrade |
| Old-map centerline | 500 numeric waypoints, 501 CSV lines; Pure Pursuit loaded all 500 | Generator and CSV path worked, but map compatibility was not established |
| Sensor recovery | VESC node enabled in the vehicle launch; IMU about 49.99 Hz, LiDAR about 9.97 Hz, `map -> base_link` restored | Sensor-to-localization pipeline recovered |
| Control debug | Vehicle `(0.09, -0.01)` m, target `(3.13, 8.71)` m, steering `0.450` rad, command speed `0.70` m/s | Distant target and steering saturation; output was remapped to `/debug_ackermann_cmd`, not actuated |
| Map compatibility | Live map approximately x `[-1.75, 3.85]`, y `[-4.55, 4.75]` m; old centerline started near `(2.95, 9.01)` m | Old centerline and live pose had different map origins |
| State persistence | Finished trajectory 0, wrote `track_20261105.pbstream`, converted that state to PGM/YAML at 0.05 m | Same-session save and conversion were demonstrated on a laboratory map |

The laboratory map was not a closed track, so its centerline extraction failed as expected for
the current algorithm. A same-session closed-track map and centerline, matching saved-state
localization, debug checks over a full loop, and supervised real-car Pure Pursuit remain pending.

## Repository changes

- `src/my_robot_bringup/launch/robot.launch.py` includes the existing configurable VESC driver
  by default, forwards `vesc_port`, and supports `start_vesc:=false` when the driver runs
  separately. This reconciles the report's restored VESC publisher with this repository's prior
  separate-driver architecture. The reported vehicle test predates this repository adaptation;
  rerun the launch and sensor checks on the vehicle.
- `src/my_robot_bringup/package.xml` declares the runtime launch and driver dependencies.
- `docs/OPERATIONS.md` records the scoped OpenCV workaround, same-state map conversion,
  explicit centerline paths, and debug-only output remap. The existing Cartographer launch
  has no saved-state localization option; a suitable launch/configuration remains future work.
- `README.md` and `docs/research/README.md` update the architecture, status, and research index.
  The original PDF and [repository code diff](2026-11-06-code-diff.patch) are archived here.

No new waypoints, PBStream, PGM, or YAML map from the closed track were supplied with the
report. The existing `map_to_centerline` and Pure Pursuit source is retained rather than
claiming that a new algorithm, matching map, or closed-loop test already exists.

## Next experiment

1. Confirm `/scan`, `/sensors/imu/raw`, and `map -> base_link`.
2. Map a closed track and derive PBStream, PGM/YAML, and waypoints from one session.
3. Load the matching state for localization and inspect pose/waypoint alignment in RViz.
4. Keep output on `/debug_ackermann_cmd`; verify near targets and unsaturated steering around
   the full loop before supervised low-speed actuation.
