# Mapping

2D/3D SLAM for the **mobile base** uses packages from [ugv_ws](https://github.com/waveshareteam/ugv_ws): **`ugv_slam`**. This workspace provides the combined URDF and bringup; mapping launches **include** the robot stack.

Full tutorial: [ugv_ws mapping](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/mapping.md).

---

## Prerequisites

- **`LDLIDAR_MODEL`** set; start LiDAR / scan stack from **[ugv_ws](https://github.com/waveshareteam/ugv_ws)** bringup or SLAM launches — **`ugv_roarm` `bringup_lidar` does not publish `/scan` by default** (see [Hardware Driver](bringup.md))
- **`UGV_MODEL`**, **`ROARM_MODEL`**, **`GRIPPER_TYPE`** set
- Use **`rviz_config:=slam_2d`** or **`slam_3d`** on description/bringup launches for matching RViz views

---

## SLAM Toolbox (2D, recommended)

**T0:**

```bash
ros2 launch ugv_slam slam_toolbox.launch.py use_slam:=sync use_rviz:=true
```

**T1** — drive while mapping:

```bash
ros2 run ugv_tools keyboard_ctrl
```

**T2** — save map (from ugv_ws root):

```bash
./save_map.sh   # choose backend 3 for SLAM Toolbox
```

Maps save to **`ugv_nav/maps/`**.

---

## Other backends

| Launch | Backend |
|--------|---------|
| `gmapping.launch.py` | Gmapping |
| `cartographer.launch.py` | Cartographer |
| `rtabmap.launch.py` | RTAB-Map (3D + OAK-D) |

---

## Arm during mapping

MoveIt can run in **T2+** while mapping, but keep the base slow and avoid cable strain. Prefer mapping with arm stowed.

---

## Simulation

Add **`use_sim_time:=true`** on SLAM launches when using [Gazebo](gazebo.md).

---

## Next

- [Navigation](navigation.md) — use saved maps with Nav2
