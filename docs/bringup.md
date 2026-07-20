# Hardware Driver

**`ugv_roarm_bringup`** is the ROS2 bridge to the ESP32 base board for **both** the mobile base and the RoArm. It replaces separate `ugv_bringup` + `roarm_driver` when using the combined kit.

---

## Node: `ugv_roarm_bringup`

| Direction | Topic / interface | Notes |
|-----------|-------------------|-------|
| Subscribe | `/cmd_vel` | Differential drive commands |
| Subscribe | `/joint_states` | Arm joint targets → forwarded to ESP32 |
| Subscribe | `/ugv/led_ctrl` | LED patterns |
| Publish | `/imu/raw`, `/imu/mag` | IMU data |
| Publish | `/odom/odom_raw` | Wheel odometry (raw) |
| Publish | `/ugv/voltage` | Battery |

**Serial:** default **`/dev/ttyAMA0`**, baud **115200** (Pi UART to ESP32).

Parameters:

```bash
ros2 run ugv_roarm_bringup ugv_roarm_bringup --ros-args \
  -p serial_port:=/dev/ttyAMA0
```

Reads **`ROARM_MODEL`** from the environment for arm-specific command formatting.

---

## Launch: `bringup_lidar.launch.py`

Main entry point for the real robot:

```bash
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true rviz_config:=bringup
```

### RViz Fixed Frame (real hardware) {#rviz-bringup-fixed-frame}

On the **real robot**, `rviz_config:=bringup` loads **`view_bringup.rviz`**, which sets **Fixed Frame** to **`odom`**. At startup the **`odom`** frame is often **not in TF yet**, so RViz may report *Fixed Frame [odom] does not exist* or show a blank view.

**Workaround:** In RViz **Global Options → Fixed Frame**, choose **`base_footprint`** or **`base_link`**. The combined model appears from **`robot_state_publisher`** immediately. Switch back to **`odom`** later if you need to view motion in the odometry frame (once wheel odometry TF is publishing).

**Simulation** ([Gazebo](gazebo.md)) publishes **`odom`** from the simulator — this workaround is **not** needed there.

Includes:

1. **`ugv_roarm_description/display.launch.py`** — `robot_state_publisher` + optional RViz + `ros2_control` + **`setgrippercmd`** (unless `use_moveit_servo:=true`)
2. **`ugv_roarm_bringup`** node
3. **`ugv_bringup/odom_publisher`** — wheel odometry from **`/odom/odom_raw`** (when `use_ekf:=true`)

Launch arguments:

| Argument | Default | Purpose |
|----------|---------|---------|
| `use_rviz` | `false` | Open RViz |
| `rviz_config` | `bringup` | RViz preset (`view_bringup.rviz` — Fixed Frame **`odom`**) |
| `use_ekf` | `true` | Start **`odom_publisher`** (wheel odom node) |
| `use_moveit_servo` | `false` | Include MoveIt Servo stack instead of plain `display` |
| `add_camera` | `false` | Include USB camera links in URDF — set **`true`** for [Vision pick-place](vision.md) (**`camera_link`** TF) |

---

## Data flow

```text
/cmd_vel ──► ugv_roarm_bringup ──► UART ──► ESP32 (wheels)
/joint_states ──► ugv_roarm_bringup ──► UART ──► ESP32 (arm servos)
ESP32 ──► UART ──► ugv_roarm_bringup ──► /imu/raw, /odom/odom_raw, …
```

MoveIt / Servo publish arm trajectories through **`ros2_control`** → **`/joint_states`** → driver.

---

## Prerequisites

- **`UGV_MODEL=ugv_rover`**, **`ROARM_MODEL=roarm_m2`**, **`GRIPPER_TYPE=angular_direct`**
- Robot powered; UART connected
- No other node using `/dev/ttyAMA0`

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| RViz empty / *Fixed Frame [odom] does not exist* | Set **Fixed Frame** → **`base_footprint`** or **`base_link`** — see [RViz Fixed Frame](#rviz-bringup-fixed-frame) |
| No serial / no `/odom/odom_raw` | Power robot; check **`/dev/ttyAMA0`**; only one driver node |

---

## Next

- [UGV Teleoperation](teleoperation.md) — drive the base with adjustable speed (`keyboard_ctrl` / gamepad)
- [MoveIt2](moveit2.md) — arm planning on real hardware or simulation
- [MoveIt Servo](moveit_servo.md) — real-time arm jog
