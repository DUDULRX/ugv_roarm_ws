# Vision

Camera demos for **UGV Rover + RoArm-M2** use **`ugv_vision`** ([ugv_ws](https://github.com/waveshareteam/ugv_ws)) for **chassis** tracking and **`roarm_vision`** ([roarm_ws](https://github.com/waveshareteam/roarm_ws)) for **arm** pick-place.

Full references: [ugv_ws vision](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/vision.md) · [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md).

This page covers **USB camera** demos only (no OAK-D) and **combined-robot** launch differences.

| Demo | Package | Drives chassis (`/cmd_vel`) | Arm |
|------|---------|----------------------------|-----|
| WebRTC preview | `ugv_vision` | No | No |
| Color calibration | `ugv_vision` / `roarm_vision` | No | No |
| Color ball track | `ugv_vision` | **Yes** | No |
| Color line follow | `ugv_vision` | **Yes** | No |
| Face track | `ugv_vision` | **Yes** | No |
| AprilTag track | `ugv_vision` | **Yes** | No |
| Gesture control | `ugv_vision` | **Yes** | No |
| Line follow + pick | `ugv_vision` + `roarm_vision` | **Yes** | Yes — **`/pick_place_cmd`**; **one camera** — see [Advanced](#line-follow-pick) |
| Color block pick | `roarm_vision` | No | Yes — **`/pick_place_cmd`** |

---

## ugv_ws vs this workspace

**ugv_ws** (standalone UGV) — one launch includes bringup + camera + vision:

```bash
ros2 launch ugv_vision demo.launch.py exe:=<name> use_rviz:=true
```

**UGV + RoArm** — start the combined driver first, then vision **without** `ugv_bringup`:

| Terminal | Command |
|----------|---------|
| **T0** | `ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true rviz_config:=bringup` |
| **T1** | `ros2 launch ugv_vision demo.launch.py exe:=<name> use_bringup:=false` |

`demo.launch.py` argument **`use_bringup`** (default **`true`**) controls whether **`ugv_bringup`** / **`ugv_gazebo`** is included. Camera + vision `exe` still start when **`use_bringup:=false`**.

Demos marked **Drives chassis** need **T0** so **`/cmd_vel`** reaches **`ugv_roarm_bringup`**. With **`use_bringup:=false`**, set **`use_rviz`** on **T0** — it does not open RViz on the vision launch.

!!! note "RViz empty on T0 (real robot, `rviz_config:=bringup`)?"
    **`view_bringup.rviz`** uses Fixed Frame **`odom`**, which may not exist at startup on **hardware**. Set **Global Options → Fixed Frame** to **`base_footprint`** or **`base_link`**. See [Hardware Driver — RViz Fixed Frame](bringup.md#rviz-bringup-fixed-frame).

Only **one** **`/cmd_vel`** source — see [UGV Teleoperation — One motion source](teleoperation.md#one-motion-source-at-a-time).

!!! warning "Safety"
    Lift the robot before chassis-tracking nodes. Stop with zero **`/cmd_vel`** when done:

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist --once
```

---

## Prerequisites

1. **Build and source** **`ugv_roarm_ws`** ([Installation](installation.md)).
2. Sibling packages **`ugv_vision`** and **`roarm_vision`** available (factory image or `/home/ws/ugv_ws`, `/home/ws/roarm_ws`).
3. USB camera connected.
4. Env vars: **`ugv_rover`**, **`roarm_m2`**, **`angular_direct`**.

### Before you start

| Do | Do not |
|----|--------|
| **`Ctrl+C`** before switching `exe` | Run **`demo.launch.py`** with default **`use_bringup:=true`** while **`ugv_roarm_bringup`** is up |
| Use **`use_bringup:=false`** on combined robot | Forget **T0** for chassis-tracking demos |
| Pick **one** motion publisher for chassis | Mix teleop and tracking demos |

---

## Quick start

Three typical paths on the combined robot. All use **T0** bringup unless noted.

### 1. WebRTC preview (`cam_webrtc`)

Browser: **`http://<robot-ip>:8889/cam/`**

```bash
# T0
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=false
# T1
ros2 launch ugv_vision demo.launch.py exe:=cam_webrtc use_bringup:=false
```

Verify: `ros2 topic hz /image_raw`

### 2. Color ball track (`color_ball_track`) — drives chassis {#color-ball-track}

Calibrate first with **`ugv_vision`** **`color_select`** — saves to **`ugv_vision/config/lab_tool_colors.json`**. Standalone UGV steps: [ugv_ws vision — color calibration](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/vision.md#usb-camera).

```bash
# T0
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true rviz_config:=bringup
# T1
ros2 launch ugv_vision demo.launch.py exe:=color_ball_track use_bringup:=false
```

Default color **`green`**. Runtime: `ros2 param set /color_track_pid color green`

### 3. Color block pick (`color_block_detect`) — arm only {#color-block-pick}

Calibrate in **`roarm_vision`** first — saves to **`roarm_vision/config/lab_tool_colors.json`**. Details: [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md).

```bash
# T0 — add_camera:=true puts camera_link in TF (required for pick-place)
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=false add_camera:=true
# T1 — includes camera.launch.py (v4l2 → /image_raw) + pick_place_cmd
ros2 launch roarm_vision demo.launch.py \
  exe:=color_block_detect \
  base_frame:=ugv_roarm_base_link \
  color:=green
```

#### Manual pick / place {#manual-pick-place}

When **`object_1`** appears in TF, trigger pick / place manually (**T2**, any terminal):

```bash
# Check target frame (Ctrl+C to stop)
ros2 run tf2_ros tf2_echo ugv_roarm_base_link object_1

# Pick object_1 (gripper close value in radians)
ros2 service call /pick_place_cmd roarm_msgs/srv/PickPlaceCmd "{cmd: 1, target: 1, gripper: 0.5}"

# Place at built-in place pose (target ignored for place)
ros2 service call /pick_place_cmd roarm_msgs/srv/PickPlaceCmd "{cmd: 2, target: 0, gripper: 0.0}"
```

**`/pick_place_cmd`** (`roarm_msgs/srv/PickPlaceCmd`) fields:

| Field | Type | Used when | Meaning |
|-------|------|-----------|---------|
| **`cmd`** | `int32` | Always | **`0`** = approach / align (move to target, gripper opens, no grasp) · **`1`** = pick · **`2`** = place |
| **`target`** | `int32` | **`cmd` 0 or 1** | Object index → TF child frame **`object_<target>`** (e.g. **`1`** → **`object_1`**). Color block demo defaults to **`object_1`**. AprilTag: usually matches tag ID. **Ignored for `cmd: 2`** (place uses a fixed pose in `pick_place_cmd`). |
| **`gripper`** | `float32` | **`cmd: 1`** (pick) | Gripper joint command in **radians**, sent on **`/gripper_cmd`** when closing. **`1.5`** ≈ fully open, **`0.0`** ≈ fully closed; **`0.5`** is a typical pick close value on **`angular_direct`**. Approach/pick sequences open the gripper to **`1.5`** first; only the final close uses this value. **Ignored for `cmd: 0` and `cmd: 2`** (place opens then releases with fixed values). |

Response: **`success`** (`bool`), **`message`** (`string`).

---

## Other chassis demos (`ugv_vision`)

Same **T0 + T1** pattern as [color ball track](#color-ball-track). Standalone UGV commands: [ugv_ws vision — USB camera](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/vision.md#usb-camera).

| `exe` | Drives chassis | Notes |
|-------|----------------|-------|
| `color_select` | No | Calibrate before color tracking; GUI needs display |
| `color_line_follow` | **Yes** | Calibrate line color first |
| `face_track` | **Yes** | |
| `apriltag_track` | **Yes** | |
| `gesture_ctrl` | **Yes** | |

**T1** (pick one):

```bash
ros2 launch ugv_vision demo.launch.py exe:=<exe> use_bringup:=false
```

---

## Arm vision (`roarm_vision`)

Does **not** drive the chassis. Full API and extra demos: [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md).

**Data path:**

```text
USB camera → perception → TF object_* → /pick_place_cmd
    → hand_controller + /gripper_cmd → setgrippercmd → gripper_controller
    → /joint_states → ugv_roarm_bringup → ESP32
```

| Item | Value |
|------|-------|
| Pick launch | `roarm_vision demo.launch.py exe:=color_block_detect base_frame:=ugv_roarm_base_link color:=<name>` |
| Arm color file | **`roarm_vision/config/lab_tool_colors.json`** — calibrate with `exe:=color_select` |
| Chassis color file | **`ugv_vision/config/lab_tool_colors.json`** — calibrate with `ugv_vision` `exe:=color_select` |

Use default bringup (**`use_moveit_servo:=false`**) for pick-place so **`display.launch.py`** / bringup provides **`ros2_control`** and **`setgrippercmd`** (bridges **`/gripper_cmd`** → **`gripper_controller`**).

**USB camera on pick-place:** **T0** needs **`add_camera:=true`** so **`camera_link`** is in the URDF/TF. **T1** **`roarm_vision demo.launch.py`** always includes **`camera.launch.py`** (`v4l2_camera` → **`/image_raw`**). Device path: **`roarm_vision/config/params.yaml`** (`video_device`, default **`/dev/video0`**).

!!! note "Gripper stays closed?"
    **`pick_place_cmd`** publishes gripper targets on **`/gripper_cmd`**. **`setgrippercmd`** (from **`roarm_moveit_cmd`**) must be running to drive **`gripper_controller`** — it starts automatically with **T0** **`bringup_lidar`** (via **`display.launch.py`**). Without it, the arm may move but the claw stays at **`initial_positions.yaml`** (closed). Quick check: `ros2 node list | grep setgrippercmd`. Manual bridge: `ros2 run roarm_moveit_cmd setgrippercmd`.

---

## Advanced

### Line follow + pick (`roarm_color_line_follow`) {#line-follow-pick}

Drives chassis and arm. Uses **one USB camera** — opened by **T1** only.

!!! warning "Do not use `ugv_vision demo.launch.py` for T2"
    **`demo.launch.py`** always includes **`camera.launch.py`**. If **T1** already runs **`roarm_vision demo.launch.py`**, launching **`ugv_vision demo.launch.py`** in **T2** opens the camera **twice** (`/dev/video0` busy, black image, or unstable tracking).  
    **T2** must be **`ros2 run ugv_vision roarm_color_line_follow`** — it subscribes to existing **`/image_raw`** and calls **`/pick_place_cmd`** from **T1**.

Calibrate **line** color **`yellow`** in **`ugv_vision/config/lab_tool_colors.json`** (`color_select`). Calibrate **block** color in **`roarm_vision/config/lab_tool_colors.json`** for **`color_block_detect`**.

**T0** — driver, **`ros2_control`**, and **`camera_link`** in TF:

```bash
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=false add_camera:=true
```

**T1** — USB camera + **`pick_place_cmd`** + block perception (publishes TF **`object_1`**):

```bash
ros2 launch roarm_vision demo.launch.py \
  exe:=color_block_detect \
  base_frame:=ugv_roarm_base_link \
  color:=yellow
```

**T2** — line follow + pick state machine (**no** second camera):

```bash
ros2 run ugv_vision roarm_color_line_follow
```

Confirm: `ros2 service list | grep pick_place` · `ros2 topic hz /image_raw` (one publisher)

### AprilTag pick

**T0:** same as above — **`add_camera:=true`**.

**T1:**

```bash
ros2 launch roarm_vision demo.launch.py \
  exe:=apriltag_detect \
  base_frame:=ugv_roarm_base_link
```

See [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md) for tag setup. When **`object_1`** / **`object_2`** appear in TF, use the [pick / place commands](#manual-pick-place) from [§3](#color-block-pick).

---

## Launch arguments

### `ugv_vision demo.launch.py`

| Argument | Default | Description |
|----------|---------|-------------|
| **`exe`** | *(required)* | See tables above |
| `use_bringup` | `true` | **`false`** on UGV + RoArm when **T0** is **`ugv_roarm_bringup`** |
| `use_rviz` | `false` | RViz on ugv_ws bringup (only when **`use_bringup:=true`**) |
| `use_sim_time` | `false` | Gazebo clock |

More args: [ugv_ws vision](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/vision.md).

### `ugv_roarm_bringup bringup_lidar.launch.py` (pick-place T0)

| Argument | Default | Notes |
|----------|---------|-------|
| `add_camera` | `false` | Set **`true`** for arm pick-place — adds **`camera_link`** to URDF/TF |
| `use_moveit_servo` | `false` | Keep **`false`** for pick-place (**`display.launch.py`** + **`ros2_control`**) |

### `roarm_vision demo.launch.py`

| Argument | Default | Notes |
|----------|---------|-------|
| `exe` | *(required)* | `color_block_detect`, `apriltag_detect`, … |
| `base_frame` | `ugv_roarm_base_link` | Arm base for object pose |
| `cam_frame` | `camera_link` | Must match **T0** **`add_camera:=true`** |
| `color` | `green` | **`roarm_vision/config/lab_tool_colors.json`** |
| `use_rect` | `true` | Passed to **`camera.launch.py`** — rectified **`/image_rect`** |

USB device / resolution: **`roarm_vision/config/params.yaml`** (`video_device`, `image_width`, `image_height`).

More args: [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md).

---

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Serial port busy | **`use_bringup:=false`**; do not run default **`demo.launch.py`** with **`ugv_roarm_bringup`** up |
| Chassis does not move | Use a **Drives chassis** `exe`; **T0** must be **`ugv_roarm_bringup`** |
| Black USB image | Check cable; `ros2 topic hz /image_raw`; **one** camera launch only — for **`roarm_color_line_follow`**, T2 is **`ros2 run`**, not **`ugv_vision demo.launch.py`** |
| No WebRTC at `:8889` | Use **`exe:=cam_webrtc`** |
| Track misses color | Run **`color_select`**; click **Save** |
| Arm does not pick | **T0** **`add_camera:=true`** + **`ros2_control`**; **`pick_place_cmd`** running; check **`base_frame:=ugv_roarm_base_link`** |
| Gripper does not open / close | **`setgrippercmd`** must run (included in **T0** **`display.launch.py`**); check `ros2 node list \| grep setgrippercmd` |
| No **`camera_link`** in TF | **T0** must use **`add_camera:=true`** (not just **T1** camera driver) |
| Multiple motion sources | Stop teleop / other **`/cmd_vel`** publishers |

---

## Next

- [MoveIt2](moveit2.md) — Plan & Execute without camera
- [Command Control](command_control.md) — *(optional)* CLI pose services
- [MTC Demo](mtc_demo.md) — *(optional)* task-constructor demos
- [ugv_ws vision](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/vision.md) — full USB demo list
- [roarm_ws vision](https://github.com/waveshareteam/roarm_ws/blob/ros2-humble-develop-251125/docs/vision.md) — arm perception details
