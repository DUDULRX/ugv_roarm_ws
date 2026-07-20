# Installation

Build **`ugv_roarm_ws`** on **Ubuntu 22.04** with **ROS2 Humble** for **UGV Rover + RoArm-M2**.

The workspace expects UGV and RoArm dependency packages from [ugv_ws](https://github.com/waveshareteam/ugv_ws) and [roarm_ws](https://github.com/waveshareteam/roarm_ws) (or a WaveShare factory image that already includes them).

---

## Prerequisites

- Ubuntu 22.04 (x86_64 or Raspberry Pi / Jetson)
- ROS2 Humble (`/opt/ros/humble`)
- Colcon, rosdep
- UGV stack packages: `ugv_description`, `ugv_bringup`, `ugv_tools`, etc.
- RoArm stack packages: `roarm_moveit_cmd`, `roarm_msgs`, `moveit_task_constructor`, etc.

On a **factory image**, these are usually pre-installed under `/home/ws/`.

---

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

`build_first.sh` **fixes** the robot variant and only prompts for LiDAR (use the **same** `LDLIDAR_MODEL` as ugv_ws):

| Variable | Set by script |
|----------|----------------|
| **`UGV_MODEL`** | Always **`ugv_rover`** |
| **`ROARM_MODEL`** | Always **`roarm_m2`** |
| **`GRIPPER_TYPE`** | Always **`angular_direct`** |
| **`LDLIDAR_MODEL`** | You choose: `ld19`, `ld06`, `stl27l` |

It runs `colcon build` in two stages, optionally saves exports to `~/.bashrc`, and sources `install/setup.bash`.

---

## After build

Source **all three** workspaces in each new shell (or add these lines to `~/.bashrc` after each `build_first.sh`):

```bash
source /home/ws/ugv_ws/install/setup.bash
source /home/ws/roarm_ws/install/setup.bash
source /home/ws/ugv_roarm_ws/install/setup.bash   # or your clone path
echo $UGV_MODEL $LDLIDAR_MODEL $ROARM_MODEL $GRIPPER_TYPE
# ugv_rover  ld19  roarm_m2  angular_direct
```

If `build_first.sh` saved env vars to `~/.bashrc`, you can also run:

```bash
source ~/.bashrc
```

---

## Incremental rebuild {#incremental-rebuild}

```bash
cd /home/ws/ugv_roarm_ws
./build_common.sh
```

Select package numbers to rebuild (see [Package Reference](packages.md)).

---

## Change LiDAR later {#change-lidar-or-gripper}

Edit `~/.bashrc` — keep **`UGV_MODEL=ugv_rover`**, **`ROARM_MODEL=roarm_m2`**, and **`GRIPPER_TYPE=angular_direct`**:

```bash
export UGV_MODEL=ugv_rover
export ROARM_MODEL=roarm_m2
export GRIPPER_TYPE=angular_direct
export LDLIDAR_MODEL=ld19
source ~/.bashrc
```

You usually **do not** need a full re-run of `build_first.sh`.

---

## Factory image (recommended)

Most kits ship a **pre-built Docker container** with `UGV_MODEL`, `LDLIDAR_MODEL`, `ROARM_MODEL`, `GRIPPER_TYPE`, and ROS2 already configured. How you enter the container differs between a **physical robot** and a **VM**.

UGV and RoArm dependency packages (`roarm_moveit_cmd`, …) are pre-installed under `/home/ws/` on factory images — you usually only need to `source ~/.bashrc` inside the container before running tutorials.

### Robot (Raspberry Pi / Jetson)

On the robot, `ros2.sh` **starts** the container on the host; you then **SSH into the container** from your PC (port **23**).

**1. SSH to the robot host** (port **22**):

| Host board | Host name | SSH user | Password |
|------------|-----------|----------|----------|
| Raspberry Pi 4B / 5 | *(IP or mDNS)* | `ws` | `ws` |
| Jetson Orin Nano | **`jetson`** | `jetson` | `jetson` |

**2. On the host**, start the container:

```bash
cd /home/ws/ugv_roarm_ws && bash ros2.sh
```

Choose **Enter container** — on ARM, the script starts Docker and exits; connect via SSH next.

**3. SSH into the ROS2 container** from your PC:

| Field | Value |
|-------|-------|
| Host | Robot IP address |
| Port | **23** |
| User | `root` |
| Password | `ws` |

**4. Inside the container:**

```bash
cd /home/ws/ugv_roarm_ws
source ~/.bashrc
echo $UGV_MODEL $LDLIDAR_MODEL $ROARM_MODEL $GRIPPER_TYPE
# ugv_rover  ld19  roarm_m2  angular_direct
```

More host/container steps: [UGV Basics — Factory Docker image](ugv_basics.md#factory-docker-image).

---

### VM (VirtualBox, x86) {#vm-virtualbox-x86}

On the factory **VM**, open **two terminal windows** on the VM desktop (host setup — not tutorial **T0**/**T1**, which start after you are inside the container):

**First window — allow GUI apps (RViz / Gazebo) to display:**

```bash
xhost +
```

Leave this window open while using GUI tools.

**Second window — enter the container:**

```bash
cd /home/ws/ugv_ws && bash ros2.sh
```

Choose **Enter container** — on x86, `ros2.sh` runs **`docker exec`** and drops you into a shell **inside** the container (no port 23).

Then inside the container:

```bash
cd /home/ws/ugv_roarm_ws
source ~/.bashrc
echo $UGV_MODEL $LDLIDAR_MODEL $ROARM_MODEL $GRIPPER_TYPE
```

Install ROS2 Humble + Gazebo only if you are **not** using the factory VM image. Skip Gazebo on Raspberry Pi images with limited resources — see [Gazebo](gazebo.md).

---

### `ros2.sh` by platform {#ros2sh-by-platform}

| Platform | Container | How you enter |
|----------|-----------|---------------|
| x86 / VM | `ros_humble` | `docker exec` via `ros2.sh` (local terminal) |
| Raspberry Pi | `ugv_rpi_ros_humble` | SSH port **23** after `ros2.sh` on host |
| Jetson | `ugv_jetson_ros_humble` | SSH port **23** after `ros2.sh` on host |

On ARM, `ros2.sh` stops `ugv-app`, `ugv-jupyter`, and `roarm_web_app` host services before you SSH into the container.

`UGV_MODEL` (**`ugv_rover`**), `ROARM_MODEL` (**`roarm_m2`**), and `GRIPPER_TYPE` (**`angular_direct`**) are fixed on this branch; `LDLIDAR_MODEL` is pre-set to match your kit.

### Factory downloads

- [VM_ROS2 VirtualBox image](https://drive.google.com/file/d/1BUiWwmoEM_r46liVtBiZyStXq5lhEM2j/view?usp=sharing)
- [UGV Rover PI ROS2 Wiki](https://www.waveshare.com/wiki/UGV_Rover_PI_ROS2)

VM images include Gazebo Classic and Harmonic; `GZ_VERSION` in `~/.bashrc` selects which simulator backend to use.

Run tutorials from [index — Typical paths](index.md#typical-paths).

**Next (factory image):** [Hardware Driver](bringup.md) or [Robot Description](description.md).

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `KeyError: 'UGV_MODEL'` | `source ~/.bashrc`; exports must include `ugv_rover` and `roarm_m2` |
| MoveIt fails to load URDF | Confirm **`GRIPPER_TYPE=angular_direct`** |
| Serial permission | User in `dialout`; device `/dev/ttyAMA0` on Pi |

---

## Next

- [Hardware Driver](bringup.md) — first launch on real hardware
- [Robot Description](description.md) — verify UGV Rover + M2 in RViz
