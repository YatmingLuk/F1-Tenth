# Master-Map Preparation and Field Mapping Validation

**Author:** Yiming Lu

**Report date:** November 20, 2026

The [original Research Journal](2026-11-20-research-journal.pdf) records the Linux
physical-vehicle checks for the mapping pipeline and the procedure planned for producing
the shared master map in the field.

## Verified on the vehicle

| Check | Reported result |
| --- | --- |
| USB and bringup | Hokuyo at `/dev/ttyACM0` and VESC at `/dev/ttyACM1` in this test. LiDAR, VESC and both static transform nodes started. |
| Sensor streams | `/scan` at approximately 10 Hz and `/sensors/imu/raw` at approximately 50 Hz. Cartographer subscribed to both. |
| Static transforms | `base_link -> laser` at `[0.110, 0.000, 0.120]` m and `base_link -> imu` at `[-0.100, 0.000, 0.120]` m, both with rotation approximately identity. |
| Mapping state | Trajectory 0 active, submap 0 updating and observed at version 41 with `is_frozen: false`. Finish and write services were available. |
| Live pose | `map -> base_link` available. At rest, x ranged from roughly 0.084 to 0.092 m, y from -0.010 to -0.003 m and yaw remained near 0°. |
| Occupancy grid | Laboratory test map at 0.05 m/cell, 95 × 181 cells, origin near `(-1.40, -4.30)` m. The map and scan overlay were inspected in RViz. |

The stationary samples confirm pose availability. Accuracy against an external reference
was outside the test scope. Use the stable USB device paths described in
[Vehicle Operations](../OPERATIONS.md#3-launch-the-vehicle-stack) for subsequent runs.

## Shared master map

One vehicle will map the site. The final `lab_master.pbstream` defines the shared `map`
frame for both vehicles. The PGM/YAML pair comes from that exact PBStream, and any
centerline comes from that map export. Each vehicle will localize independently against
the same saved state. `VehicleState` is a future interface for sharing x, y, yaw, velocity,
timestamp and uncertainty in the common frame. Both vehicles can use their own internal
speed estimator.

The [field mapping procedure](../OPERATIONS.md#prepare-the-field-master-map) records the
terminal checks, checkpoint settings and final save sequence. Checkpoints include unfinished
submaps and use separate paths. The final field save follows trajectory completion, excludes
unfinished submaps and is converted to `lab_master.pgm` and `lab_master.yaml` at 0.05 m/cell.

## Pending field acceptance

1. Start a fresh field session. Verify sensor rates, pose continuity and submap updates
   across the route.
2. Finish the trajectory and convert its final PBStream to PGM/YAML. Check coverage and
   inspect for duplicated walls, discontinuities, distortion and incorrect loop closure.
3. Restart in localization-only mode and verify consistent pose recovery in the saved map.
4. Deploy the accepted package to the second vehicle and validate both localizers. Then
   implement and test the shared `VehicleState` interface.

The laboratory test established that the pipeline can produce a map. The field master-map
artifacts and localization-only restart are pending. This update documents the existing
launch and mapping behavior and the field procedure described in the report.
