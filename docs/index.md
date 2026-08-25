# ugv_roarm_ws Documentation

**ugv_roarm_ws** is a **ROS2 Humble** colcon workspace for the **WaveShare UGV Rover + RoArm-M2** mobile manipulator.
It connects the mobile base (**RViz2**, teleop) and the arm (**MoveIt2**, Servo) through a **single serial bridge** to the ESP32 base board, with optional Gazebo simulation.

!!! note "Supported hardware (this branch)"
    This repository currently documents and tests **UGV Rover + RoArm-M2** with **`GRIPPER_TYPE=angular_direct`** (direct gripper) only.
    Other UGV or RoArm variants may exist in source for future use; see [ugv_ws](https://github.com/waveshareteam/ugv_ws) and [roarm_ws](https://github.com/waveshareteam/roarm_ws) for standalone stacks.

This workspace merges the roles of [ugv_ws](https://github.com/waveshareteam/ugv_ws) and [roarm_ws](https://github.com/waveshareteam/roarm_ws) into one combined robot model and driver stack.

### Product names vs environment variables

| Your hardware (WaveShare) | `UGV_MODEL` | `ROARM_MODEL` | `GRIPPER_TYPE` |
|---------------------------|-------------|---------------|----------------|
| UGV Rover + RoArm-M2 (direct gripper) | `ugv_rover` | `roarm_m2` | **`angular_direct`** |

**Getting started** — read in this order ([details below](#suggested-reading-order)):

1. **[ROS2 Basics](ros2_basics.md)** — if you are new to ROS2. Skip if you already know ROS2.
2. **[UGV Basics](ugv_basics.md)** — dual-controller layout, kit types, mobile-base frames.
3. **[RoArm Basics](roarm_basics.md)** — arm frames, `hand_tcp`, real TCP.
4. **[UGV + RoArm Basics](ugv_roarm_basics.md)** — combined TF tree, one driver, typical terminals.
5. **[Installation](installation.md)** — `build_first.sh`, set env vars.

Before use, set environment variables (pre-set by `build_first.sh` or in `~/.bashrc`):

| Variable | Value (this repo) | When | Role |
|----------|-------------------|------|------|
| `UGV_MODEL` | **`ugv_rover`** | **Always** | UGV Rover URDF, Gazebo world |
| `ROARM_MODEL` | **`roarm_m2`** | **Always** | RoArm-M2 URDF, MoveIt config |
| `GRIPPER_TYPE` | **`angular_direct`** | **Always** | Direct M2 gripper (this branch) |
| `GZ_VERSION` | `classic`, `harmonic` | Gazebo only | Simulator backend |

After install or editing `~/.bashrc`, verify:

```bash
echo $UGV_MODEL $ROARM_MODEL $GRIPPER_TYPE $GZ_VERSION
# Expected: ugv_rover roarm_m2 angular_direct
```

`GZ_VERSION` may print empty when you do not use simulation — that is normal.

---

## Overview

Short map of what each chapter covers. Step-by-step guides are in the sidebar.

Combined workflows use **T0** for the robot stack (bringup, MoveIt) and **T1** for teleop or Servo keyboard. Only **one** **`/cmd_vel`** source at a time — see [UGV Teleoperation](teleoperation.md).

### [1. Robot Description](description.md)

Combined URDF/xacro: **UGV Rover** base + **RoArm-M2** mount + optional sensors.

- **`ugv_roarm_description`** — mounts RoArm-M2 on UGV Rover via `ugv_roarm.xacro`.
- **`display.launch.py`** — joint sliders or `ros2_control`; RViz configs for description, bringup, MoveIt.

### [2. Hardware Driver](bringup.md)

**`ugv_roarm_bringup`** — single UART bridge for **both** base motion and arm joints.

- Subscribes **`/cmd_vel`**, **`/joint_states`**, LED topics; publishes IMU, odometry raw, battery.
- **`bringup_lidar.launch.py`** — default real-robot entry (driver + `display` / optional MoveIt Servo). Name is historical: **LiDAR / rf2o / EKF are not started** in the current launch — see [Hardware Driver](bringup.md).

Unlike standalone [roarm_ws](https://github.com/waveshareteam/roarm_ws), there is **no separate `roarm_driver`** — arm commands go through the same serial link as the UGV.

### [3. UGV Teleoperation](teleoperation.md)

Chassis-only **`/cmd_vel`** via **`ugv_tools`** — **adjustable speed** (gears / key scales / launch limits).

- Servo D-Pad and arrow keys also drive the base, but at **fixed** speed — see [MoveIt Servo](moveit_servo.md).

### [4. MoveIt2](moveit2.md)

Drag-and-plan for RoArm-M2 on the UGV Rover.

- **`ugv_roarm_moveit`** + **`ugv_roarm_moveit_ikfast_plugins`** — M2 SRDF, IKFast; group **`hand`**, frame **`hand_tcp`**.
- Real hardware: **`bringup_lidar.launch.py`** with **`use_moveit_servo:=true`** and **`rviz_config:=moveit`** (driver + `move_group` + Motion Planning RViz).

### [5. MoveIt Servo](moveit_servo.md)

Real-time **arm** jogging (keyboard / gamepad). Optional fixed-speed chassis (D-Pad / arrows).

- Same bringup as MoveIt (**`use_moveit_servo:=true`**), then **`keyboardcontrol`** or gamepad.
- **`servo_control.launch.py`** is included by that bringup path (do not launch it on top of default bringup).
- Adjustable chassis speed → [UGV Teleoperation](teleoperation.md).

### [6. Vision](vision.md)

USB camera, color tracking, and arm pick-place via **`ugv_vision`** + **`roarm_vision`**.

- Web preview at **`http://<robot-ip>:8889/cam/`**
- Color ball track, line-follow pick, **`/pick_place_cmd`**

### [7. Gazebo](gazebo.md)

**`ugv_roarm_gazebo`** — simulated UGV Rover + RoArm-M2; VM or desktop only.

### Optional

Not required for bringup, teleop, MoveIt, Servo, or vision pick:

- **[Command Control](command_control.md)** — CLI motion services (`/move_joint_cmd`, …) from **`roarm_moveit_cmd`**
- **[MTC Demo](mtc_demo.md)** — multi-stage Task Constructor demos

Developer package lookup: [Package Reference](packages.md).

---

## Typical paths

Use separate terminals. Env vars: **`ugv_rover`** + **`roarm_m2`** + **`angular_direct`**. Only **one** **`/cmd_vel`** source at a time.

!!! note "Arm stacks on real hardware"
    For **MoveIt / Servo**, use **`use_moveit_servo:=true`** on `bringup_lidar.launch.py` — one launch with driver + MoveIt + a **single** `ros2_control` stack. Do **not** stack default bringup and a separate **`ugv_roarm_moveit`** / **`servo_control`** launch.

!!! note "RViz empty at startup (real robot, `rviz_config:=bringup`)?"
    On **hardware**, **`view_bringup.rviz`** uses Fixed Frame **`odom`**, which may not exist yet. Set **Global Options → Fixed Frame** to **`base_footprint`** or **`base_link`**. **Simulation** publishes **`odom`** — no change needed. See [Hardware Driver — RViz Fixed Frame](bringup.md#rviz-bringup-fixed-frame).

| Goal | Commands |
|------|----------|
| View combined URDF (sliders) | **T0:** `ros2 launch ugv_roarm_description display.launch.py use_rviz:=true rviz_config:=description use_joint_state_publisher_gui:=true` |
| Boot real robot | **T0:** `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true rviz_config:=bringup` |
| Teleop base (adjustable speed) | **T0:** `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true rviz_config:=bringup` · **T1:** `ros2 run ugv_tools keyboard_ctrl` — see [UGV Teleoperation](teleoperation.md) |
| MoveIt (real arm) | **T0:** `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true use_moveit_servo:=true rviz_config:=moveit` |
| MoveIt Servo | **T0:** `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true use_moveit_servo:=true rviz_config:=moveit_servo` · **T1:** `ros2 run ugv_roarm_moveit_servo keyboardcontrol` |
| Vision — Web camera | **T0:** bringup · **T1:** `ros2 launch ugv_vision demo.launch.py exe:=cam_webrtc use_bringup:=false` · `http://<ip>:8889/cam/` |
| Vision — color ball track | **T0:** bringup · **T1:** `ros2 launch ugv_vision demo.launch.py exe:=color_ball_track use_bringup:=false` — see [Vision](vision.md) |
| Vision — pick color block | **T0:** bringup **`add_camera:=true`** · **T1:** `roarm_vision demo.launch.py exe:=color_block_detect base_frame:=ugv_roarm_base_link` — see [Vision](vision.md) |
| Simulation only | **T0:** `ros2 launch ugv_roarm_gazebo bringup_gazebo.launch.py use_rviz:=true rviz_config:=bringup` |
| *(optional)* Command Control | See [Command Control](command_control.md) — CLI services; not needed above |
| *(optional)* MTC demo | See [MTC Demo](mtc_demo.md) — advanced; not needed above |

---

## Suggested reading order

| Step | Page | You learn |
|------|------|-----------|
| 1 | [ROS2 Basics](ros2_basics.md) | ROS2 vocabulary (skip if you know ROS2) |
| 2 | [UGV Basics](ugv_basics.md) | UGV Rover layout and frames |
| 3 | [RoArm Basics](roarm_basics.md) | RoArm-M2 frames, `hand_tcp`, `angular_direct` |
| 4 | [UGV + RoArm Basics](ugv_roarm_basics.md) | Combined system, one driver |
| 5 | [Installation](installation.md) | Build workspace, set env vars |
| 6 | [Robot Description](description.md) | Combined model and TF |
| 7 | [Hardware Driver](bringup.md) | Serial bridge, `/odom` |
| 8 | [UGV Teleoperation](teleoperation.md) | Drive chassis with adjustable speed |
| 9 | [MoveIt2](moveit2.md) | Plan & Execute on hardware |
| 10+ | Servo, Vision, Gazebo | See sidebar |
| Optional | [Command Control](command_control.md), [MTC Demo](mtc_demo.md) | CLI services / stage demos |
