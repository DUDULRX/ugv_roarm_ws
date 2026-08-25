# Package Reference

Packages **built in this workspace** (`src/`). Dependencies from [ugv_ws](https://github.com/waveshareteam/ugv_ws) and [roarm_ws](https://github.com/waveshareteam/roarm_ws) are listed in [UGV + RoArm Basics — External packages](ugv_roarm_basics.md#external-packages-from-ugv_ws--roarm_ws).

| Package | Role |
|---------|------|
| **`ugv_roarm_description`** | Combined URDF/xacro (`ugv_roarm.xacro`), base+arm mounts, Gazebo snippets, `display.launch.py` |
| **`ugv_roarm_bringup`** | Python driver `ugv_roarm_bringup` — UART bridge for base + arm; `bringup_lidar.launch.py` (name historical — no LiDAR/EKF in current launch) |
| **`ugv_roarm_moveit`** | MoveIt2 config (SRDF, kinematics, controllers) per `ROARM_MODEL`; `ugv_roarm_moveit.launch.py` |
| **`ugv_roarm_moveit_ikfast_plugins`** | IKFast plugin for RoArm-M2 `hand` group |
| **`ugv_roarm_moveit_servo`** | MoveIt Servo — keyboard/gamepad jogging; `servo_control.launch.py` |
| **`ugv_roarm_moveit_mtc_demo`** | *(Optional)* MTC demos — pick/place, Cartesian; see [MTC Demo](mtc_demo.md) |
| **`ugv_roarm_cmd`** | Optional helpers — `navigatetoposecmd` (advanced mobile manipulation; see [Command Control](command_control.md)) |
| **`ugv_roarm_gazebo`** | Gazebo spawn + `ros2_control` for combined model; `bringup_gazebo.launch.py`, `moveit_gazebo.launch.py` |

---

## Build order

`build_first.sh` builds in two groups:

1. `ugv_roarm_cmd`, `ugv_roarm_moveit_ikfast_plugins`, `ugv_roarm_moveit_mtc_demo`, `ugv_roarm_moveit_servo`
2. `ugv_roarm_description`, `ugv_roarm_bringup`, `ugv_roarm_moveit`, `ugv_roarm_gazebo`

Use `build_common.sh` to rebuild individual packages.

---

## Launch file index

| Launch file | Package |
|-------------|---------|
| `display.launch.py` | `ugv_roarm_description` |
| `bringup_lidar.launch.py` | `ugv_roarm_bringup` |
| `ugv_roarm_moveit.launch.py` | `ugv_roarm_moveit` |
| `servo_control.launch.py` | `ugv_roarm_moveit_servo` |
| `demo.launch.py`, `run.launch.py` | `ugv_roarm_moveit_mtc_demo` |
| `command_control.launch.py` | **`roarm_moveit_cmd`** (roarm_ws) — *(optional)* CLI services; see [Command Control](command_control.md) |
| `bringup_gazebo.launch.py`, `moveit_gazebo.launch.py` | `ugv_roarm_gazebo` |

**External (roarm_ws):** `roarm_moveit_cmd`, `roarm_msgs`, `roarm_vision`, … — see [UGV + RoArm Basics — External packages](ugv_roarm_basics.md#external-packages-from-ugv_ws--roarm_ws).

RViz **`rviz_config`** keys: on **`display` / default bringup** — `description`, `bringup`, `slam_*`, `nav_*`. On **MoveIt / Servo** (`use_moveit_servo:=true` or `ugv_roarm_moveit`) — also `moveit`, `moveit_servo`, `moveit_mtc`.
