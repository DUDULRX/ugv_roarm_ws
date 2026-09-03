# ROS2 + MoveIt2 for UGV Rover + RoArm-M2

**ugv_roarm_ws** is a ROS2 Humble colcon workspace for the **WaveShare UGV Rover + RoArm-M2** mobile manipulator. It connects the mobile base (RViz2, teleop) and the arm (MoveIt2, Servo) through a **single serial bridge**, with optional Gazebo simulation.

> **Scope:** This branch targets **UGV Rover (`ugv_rover`) + RoArm-M2 (`roarm_m2`)** with **`GRIPPER_TYPE=angular_direct`** (direct gripper).

Related workspaces:

- [ugv_ws](https://github.com/waveshareteam/ugv_ws) — UGV-only stack (SLAM, Nav2, vision, web app)
- [roarm_ws](https://github.com/waveshareteam/roarm_ws) — RoArm-only stack (MoveIt2, MTC, vision)

## Documentation

Tutorials live in [`docs/`](docs/). On GitHub, open any `.md` file to read the rendered preview — no Wiki required.

| Browse on GitHub | [`docs/`](docs/) — start with [`index.md`](docs/index.md) |
| --- | --- |
| Optional local site | `pip install -r docs/requirements.txt` then `mkdocs serve -a 0.0.0.0:8000` (sidebar nav + copy buttons; same source files) |

### Getting Started

| Section | Page |
| --- | --- |
| Overview | [docs/index.md](docs/index.md) |
| ROS2 Basics | [docs/ros2_basics.md](docs/ros2_basics.md) |
| UGV Basics | [docs/ugv_basics.md](docs/ugv_basics.md) |
| RoArm Basics | [docs/roarm_basics.md](docs/roarm_basics.md) |
| UGV + RoArm Basics | [docs/ugv_roarm_basics.md](docs/ugv_roarm_basics.md) |
| Installation | [docs/installation.md](docs/installation.md) |

### Tutorials

| Section | Page |
| --- | --- |
| Robot Description | [docs/description.md](docs/description.md) |
| Hardware Driver | [docs/bringup.md](docs/bringup.md) |
| UGV Teleoperation | [docs/teleoperation.md](docs/teleoperation.md) |
| MoveIt2 | [docs/moveit2.md](docs/moveit2.md) |
| MoveIt Servo | [docs/moveit_servo.md](docs/moveit_servo.md) |
| Vision | [docs/vision.md](docs/vision.md) |
| Gazebo | [docs/gazebo.md](docs/gazebo.md) |
| Command Control *(optional)* | [docs/command_control.md](docs/command_control.md) |
| MTC Demo *(optional)* | [docs/mtc_demo.md](docs/mtc_demo.md) |

Package layout: [docs/packages.md](docs/packages.md)

Suggested order: [docs/index.md](docs/index.md) — Suggested reading order.

## Quick start

**Ubuntu 22.04** + **ROS2 Humble**.

This workspace **depends on sibling workspaces** [ugv_ws](https://github.com/waveshareteam/ugv_ws) and [roarm_ws](https://github.com/waveshareteam/roarm_ws) — teleop, vision, MoveIt Cmd, and other tutorials need packages built there (`ugv_tools`, `ugv_vision`, `roarm_vision`, `roarm_moveit_cmd`, …). On a **WaveShare factory image**, both are usually pre-installed under `/home/ws/` — skip to step 3.

### 1. Build ugv_ws

```bash
git clone -b ros2-humble-develop-251125 https://github.com/waveshareteam/ugv_ws.git
cd ugv_ws
sudo bash build_first.sh
```

When prompted, choose **`ugv_rover`** and the LiDAR model that matches your kit (`ld06` / `ld19` / `stl27l`). Details: [ugv_ws Installation](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/installation.md).

### 2. Build roarm_ws

```bash
git clone -b ros2-humble-develop-251125 https://github.com/waveshareteam/roarm_ws.git
cd roarm_ws
sudo chmod +x build_first.sh
./build_first.sh
```

When prompted, choose **`roarm_m2`** and **`angular_direct`** (direct gripper). Details: [roarm_ws Installation](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/installation.md).

### 3. Build ugv_roarm_ws

Clone next to the other workspaces (factory layout: `/home/ws/ugv_ws`, `/home/ws/roarm_ws`, `/home/ws/ugv_roarm_ws`):

```bash
git clone -b ros2-humble-develop-251125 https://github.com/waveshareteam/ugv_roarm_ws.git
cd ugv_roarm_ws
chmod +x build_first.sh
./build_first.sh
```

`build_first.sh` fixes **`UGV_MODEL=ugv_rover`**, **`ROARM_MODEL=roarm_m2`**, and **`GRIPPER_TYPE=angular_direct`**, prompts for **`LDLIDAR_MODEL`** (same choice as ugv_ws), then runs `colcon build`. **`ugv_roarm_gazebo` is skipped if Gazebo is not installed.** Details: [Installation — After build](docs/installation.md#after-build).

Source all three workspaces in each new shell (or add to `~/.bashrc` after each `build_first.sh`):

```bash
source /home/ws/ugv_ws/install/setup.bash
source /home/ws/roarm_ws/install/setup.bash
source /home/ws/ugv_roarm_ws/install/setup.bash
```

### Model settings

| Setting | Value |
| --- | --- |
| UGV | **`UGV_MODEL=ugv_rover`** (UGV Rover) |
| Arm | **`ROARM_MODEL=roarm_m2`** (RoArm-M2) |
| Gripper | **`GRIPPER_TYPE=angular_direct`** |
| LiDAR | **`LDLIDAR_MODEL=ld06`** / **`ld19`** / **`stl27l`** |

### Typical real-robot workflow

1. **T0** — robot stack: `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true`
2. **T1** — arm (MoveIt / Servo) or base teleop (`keyboard_ctrl`) — see [Typical paths](docs/index.md#typical-paths)

Example — MoveIt: **T0** `bringup_lidar use_moveit_servo:=true` (integrated). Example — base teleop: **T0** bringup · **T1** `keyboard_ctrl`. See [Typical paths](docs/index.md#typical-paths).

Simulation: VM or desktop only — see [Gazebo](docs/gazebo.md).

## License

See repository license.
