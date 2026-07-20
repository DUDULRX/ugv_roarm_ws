# Gazebo

**`ugv_roarm_gazebo`** simulates the combined UGV + RoArm in **Gazebo Classic** or **GZ Harmonic** (`GZ_VERSION=classic` or `harmonic`).

**VM or desktop only** — do not run Gazebo on the Pi/Jetson on the physical robot.

---

## Environment

```bash
export GZ_VERSION=classic   # or harmonic
export UGV_MODEL=ugv_rover
export ROARM_MODEL=roarm_m2
export GRIPPER_TYPE=angular_direct
```

---

## Bringup simulation

Spawn world + robot + `ros2_control`:

```bash
ros2 launch ugv_roarm_gazebo bringup_gazebo.launch.py use_rviz:=true rviz_config:=bringup
```

No **`ugv_roarm_bringup`** — simulated joints only. Gazebo publishes **`odom`** TF, so **`view_bringup.rviz`** (Fixed Frame **`odom`**) works without the [real-hardware RViz workaround](bringup.md#rviz-bringup-fixed-frame).

---

## MoveIt in simulation

```bash
ros2 launch ugv_roarm_gazebo moveit_gazebo.launch.py use_rviz:=true rviz_config:=moveit
```

Drag-and-plan like [MoveIt2](moveit2.md) on hardware.

For SLAM, Nav2, or other UGV-only simulation workflows, see [ugv_ws gazebo](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/gazebo.md).

---

## Do not mix

- Do **not** run **`ugv_roarm_bringup`** and Gazebo bringup together
- Do **not** run Gazebo on the same machine as real-hardware UART bringup

---

## Next

- [MoveIt2](moveit2.md) — same RViz workflow on hardware after sim tests
