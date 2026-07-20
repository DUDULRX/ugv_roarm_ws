# ROS2 Basics

Even if you are not familiar with ROS2, you can follow the UGV tutorial step by step.
This page lists **ROS2 concepts you will meet in `ugv_roarm_ws`**. For SLAM, Nav2, LiDAR, and vision topics, see [ugv_ws](https://github.com/waveshareteam/ugv_ws).

Already comfortable with ROS2? Skip to [UGV Basics](ugv_basics.md). Already know ROS2 and UGV frames? Skip to [Installation](installation.md).

---

## ROS2 Introduction

**ROS2** is a second-generation robot operating system designed and developed based on ROS. It is a software library and toolset that can help us simplify robot development tasks and accelerate the deployment of robots.

---

## ROS2 workspace & package

| Term | Meaning |
|------|---------|
| **ROS2 workspace** | The **`ugv_roarm_ws`** folder you build with `colcon` (packages, `install/`, `build/`) |
| **Package** | One module inside the workspace, e.g. `ugv_roarm_bringup`, `ugv_roarm_moveit` |
| **Node** | One running program, e.g. `ugv_roarm_bringup`, `keyboard_ctrl` |
| **Launch file** | Starts several nodes with one command, e.g. `bringup_lidar.launch.py` |
| **Clearance around the robot** | The physical floor space — keep it clear before driving (safety) |

After every **new** terminal, source **`ugv_roarm_ws`**:

```bash
source /opt/ros/humble/setup.bash
source /home/ws/ugv_roarm_ws/install/setup.bash
```

(`build_first.sh` can add these lines to `~/.bashrc` so new shells pick them up automatically. Factory Docker images often do this for you.)

First-time build and env vars: [Installation](installation.md). After code changes, run `./build_common.sh` in the **`ugv_roarm_ws`** root (interactive package picker) — it sources **`install/setup.bash`** in **that shell** when finished; **other already-open terminals** still need the `source` commands above (or open a fresh terminal). See [Installation — incremental rebuild](installation.md#incremental-rebuild).

---

## Nodes

A **node** is a fundamental ROS2 element that serves a single, modular purpose in a robotics system (e.g. the base driver, LiDAR driver, RViz).

Start a node:

```bash
ros2 run <package_name> <executable_name> [args]
```

Example:

```bash
ros2 run ugv_tools keyboard_ctrl
```

List active nodes:

```bash
ros2 node list
```

View node information:

```bash
ros2 node info <node_name>
```

Examples you will see in tutorials:

| Node | Package | Role |
|------|---------|------|
| `ugv_roarm_bringup` | `ugv_roarm_bringup` | Serial link to ESP32 — base + arm |
| `odom_publisher` | `ugv_bringup` | Wheel odometry publisher |
| `robot_state_publisher` | ROS2 standard | URDF + joint states → TF |
| `move_group` | `ugv_roarm_moveit` | Arm motion planning |
| `rviz2` | RViz | 3D visualization |

---

## Launch files

**Launch files** allow you to start up and configure a number of executables containing ROS2 nodes simultaneously.

Running a single launch file with `ros2 launch` will start up your entire system — all nodes and their configurations — at once.

```bash
ros2 launch <package> <launch_file> [launch_arguments]
```

Examples:

```bash
ros2 launch ugv_roarm_bringup bringup_lidar.launch.py use_rviz:=true
ros2 launch ugv_roarm_moveit ugv_roarm_moveit.launch.py use_rviz:=true
```

Launch arguments (`use_rviz:=true`) configure behavior without editing code.

---

## Communication method

A full robotic system is comprised of many nodes working in concert. In ROS2, a single executable (C++ program, Python program, etc.) can contain one or more nodes. Each node can send and receive data from other nodes via topics, services, actions, or parameters.

**Click an image for full-screen view** — click outside, press **Esc**, or **×** to close.

<img class="img-zoom" alt="Communication" src="https://github.com/user-attachments/assets/c3f90e68-331d-44e7-83f7-d406e742838d" />

### Topics

**Topics** are one of the most commonly used communication methods in ROS2, and topic communication adopts a publish-subscribe model.

**Click an image for full-screen view** — click outside, press **Esc**, or **×** to close.

<img class="img-zoom" alt="Topics" src="https://github.com/user-attachments/assets/f5029848-90b8-4f73-b673-21cbc2f22c1c" />

List active topics:

```bash
ros2 topic list
```

View topic information:

```bash
ros2 topic info <topic_name> --verbose
```

Publish once:

```bash
ros2 topic pub <topic_name> <msg_type> '<args>' --once
```

The **args** argument is the actual data you’ll pass to the topic.

Topics used in **`ugv_roarm_ws`** tutorials:

| Topic | Message type | Direction | Used for |
|-------|--------------|-----------|----------|
| `/cmd_vel` | `geometry_msgs/Twist` | teleop → base | Linear and angular velocity |
| `/joint_states` | `sensor_msgs/JointState` | ros2_control → driver | Arm joint targets |
| `/odom` | `nav_msgs/Odometry` | odom publisher → RViz | Wheel odometry |
| `/ugv/voltage` | `sensor_msgs/BatteryState` | base → you | Battery voltage |
| `/tf` | `tf2_msgs/TFMessage` | publishers → RViz | Link positions (frames) |

Check rate:

```bash
ros2 topic hz /joint_states
```

---

### Services

**Services** are based on a call-and-response model versus the publisher-subscriber model of topics. While topics allow nodes to subscribe to data streams and get continual updates, services only provide data when they are specifically called by a client.

A service is divided into a **client** and a **server**. The client sends a request to the server, the server processes the request, and then returns the result to the client.

**Click an image for full-screen view** — click outside, press **Esc**, or **×** to close.

<img class="img-zoom" alt="Services" src="https://github.com/user-attachments/assets/7db35241-45b6-4d2d-8b9a-a6183fc3acee" />

List active services:

```bash
ros2 service list
```

View type of a service:

```bash
ros2 service type <service_name>
```

Call a service:

```bash
ros2 service call <service_name> <service_type> <arguments>
```

Custom service types from the RoArm stack live in **`roarm_msgs`**. See [Command Control](command_control.md) and [roarm_ws](https://github.com/waveshareteam/roarm_ws).

---

### Actions

**Actions** are for **long-running tasks** with optional **feedback** and a **result** — unlike topics (continuous stream) or services (one-shot request/response). The client sends a **goal**; the server executes it, may publish **feedback** while running, then returns a **result**. Goals can be **cancelled** mid-flight.

**Click an image for full-screen view** — click outside, press **Esc**, or **×** to close.

<img class="img-zoom" alt="Actions"  src="https://github.com/user-attachments/assets/577a84e7-9eb4-4703-ae54-44e7a2c66e03" />

List active actions:

```bash
ros2 action list
```

View action information:

```bash
ros2 action info /behavior
```

Send a goal from the terminal:

```bash
ros2 action send_goal /behavior ugv_msgs/action/Behavior \
  "{command: '[{\"T\": 1, \"type\": \"drive_on_heading\", \"data\": 0.1}]'}"
```

Action definitions use **`.action`** files (goal / result / feedback sections). In **`ugv_ws`**, custom types live in **`ugv_msgs`**.

Actions you will meet in tutorials:

| Action | Type | Server | Used for |
|--------|------|--------|----------|
| `/behavior` | `ugv_msgs/action/Behavior` | `behavior_ctrl` | Open-loop motion by odometry — [ugv_ws Experimental](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/experimental.md) |

For Nav2 actions (`/navigate_to_pose`, …), see [ugv_ws navigation](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/navigation.md).

**`/behavior`** goal: JSON string in the `command` field. Each entry has `type` and `data`:

| `type` | `data` | Effect |
|--------|--------|--------|
| `drive_on_heading` | distance (m) | Drive forward |
| `back_up` | distance (m) | Drive backward |
| `spin` | angle (deg, sign = direction) | Rotate in place |
| `stop` | `0` | Stop |

Start the server before sending goals:

```bash
ros2 run ugv_tools behavior_ctrl
```

Or use [ugv_ws Experimental Web AI](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/experimental.md) — it calls `/behavior` via the LLM.

---

## Parameters

Nodes have **parameters** to define their default configuration values.

List parameters:

```bash
ros2 param list
```

View a parameter:

```bash
ros2 param get <node_name> <parameter_name>
```

Set a parameter:

```bash
ros2 param set <node_name> <parameter_name> <value>
```

| Mechanism | Set where | Examples in UGV |
|-----------|-----------|-----------------|
| **Launch argument** | `ros2 launch …` | `use_rviz:=true`, `use_moveit_servo:=true` |
| **Node parameter** | `ros2 run … --ros-args -p` | Servo tuning on `servo_node` |
| **Environment variable** | `~/.bashrc` / `build_first.sh` | `UGV_MODEL`, `ROARM_MODEL`, `GRIPPER_TYPE`, `GZ_VERSION` (Gazebo only) — [environment variables](index.md#product-names-vs-environment-variables) |

---

## Tools

### TF2

Every link on the robot has a **frame** (coordinate system). **TF** tracks how frames relate as the robot moves.

For UGV frame names and the combined arm tree, see [UGV + RoArm Basics](ugv_roarm_basics.md) and [Robot Description](description.md#tf-tree).

| Frame | Meaning |
|-------|---------|
| `odom` | Wheel odometry frame |
| `base_footprint` | Ground projection of robot center |
| `base_link` | Robot body; arm mount |
| `ugv_roarm_base_link` | RoArm-M2 base on chassis |
| `hand_tcp` | MoveIt end-effector frame |

Debug TF — check transform between **base_link** and **hand_tcp**:

```bash
ros2 run tf2_ros tf2_echo base_link hand_tcp
```

Get a graphical representation:

```bash
ros2 run tf2_tools view_frames
```

Open the generated `frames.pdf` in the current directory to inspect the TF tree.

---

### URDF

**URDF** (Unified Robot Description Format) is a file format for specifying the geometry and organization of robots in ROS2.

- **`URDF`** = robot description (links + joints). Built from **xacro** in `ugv_roarm_description` (selected by **`UGV_MODEL`** + **`ROARM_MODEL`**).
- **`joint_states`** = current angle of each movable joint (base wheels, RoArm arm joints).
- **`robot_state_publisher`** = combines URDF + `joint_states` → TF for RViz.

Full UGV-specific explanation: [Robot Description](description.md).

---

### RViz

**RViz** is a 3D visualizer for the ROS2 framework. RViz shows the robot model, odometry, and MoveIt planning scenes.

You do not “program” in RViz — you **watch** state and use MoveIt panels to plan arm motion.

Common fixes:

- Empty view on **real hardware** with **`rviz_config:=bringup`** → Fixed Frame **`odom`** may not exist yet; set **`base_footprint`** or **`base_link`** ([Hardware Driver — RViz Fixed Frame](bringup.md#rviz-bringup-fixed-frame)). **Simulation** publishes **`odom`** — not applicable.
- Empty view with MoveIt → set **Fixed Frame** to **`world`** or **`base_link`**
- No robot → check `robot_state_publisher` is running (included in bringup)
- MoveIt marker missing → add **MotionPlanning** display; confirm `move_group` is running

---

## Related Tutorials

| Chapter | What it adds |
|---------|----------------|
| [ROS2 Basics](ros2_basics.md) | ROS2 words, topics, services, **actions**, TF tools (this page) |
| [UGV Basics](ugv_basics.md) | Dual-controller layout, kit types, frames |
| [Installation](installation.md) | Install & build |
| [Robot Description](description.md) | Model, sensors, TF |
| [Hardware Driver](bringup.md) | Serial ports, bringup launch |
| Further tutorials | MoveIt, Servo, teleop, Gazebo — see [index](index.md#suggested-reading-order) |

---

## Learn more (official)

General ROS2 references (not required for the UGV tutorials):

- [ROS2 Humble tutorials](https://docs.ros.org/en/humble/Tutorials.html)

This repo targets **ROS2 Humble** on **Ubuntu 22.04** (RViz, real robot or Gazebo, topics, services, actions, and launch files).

**Next:** [UGV Basics](ugv_basics.md) — dual-controller layout, kit types, and coordinate frames.
