# Navigation

Autonomous **base** navigation with [Nav2](https://navigation.ros.org/) via **`ugv_nav`** from [ugv_ws](https://github.com/waveshareteam/ugv_ws).

Full tutorial: [ugv_ws navigation](https://github.com/waveshareteam/ugv_ws/blob/ros2-humble-develop-251125/docs/navigation.md).

---

## Prerequisites

- Saved map from [Mapping](mapping.md) (`ugv_nav/maps/`)
- **`UGV_MODEL`** matches Nav2 parameter files
- Stop teleop and motion demos before starting Nav2

---

## Navigate on saved map (AMCL + TEB)

**T0:**

```bash
ros2 launch ugv_nav nav.launch.py use_rviz:=true
```

Set initial pose in RViz (**2D Pose Estimate**), then **Nav2 Goal**.

Use **`rviz_config:=nav_2d`** on bringup if you launch description separately.

---

## SLAM while navigating

**T0:**

```bash
ros2 launch ugv_nav nav.launch.py use_rviz:=true use_slam:=true
```

**T1** *(optional)*:

```bash
ros2 launch explore_lite explore.launch.py
```

---

## Mobile manipulation + Nav2

For pick-place at multiple stations:

1. **T0** — `nav.launch.py` + `bringup_lidar.launch.py` (or integrated factory launch)
2. **T1** — MoveIt command / vision
3. **T2** — `ros2 run ugv_roarm_cmd navigatetoposecmd` with `saved_points.json` at the workspace root

See [Command Control](command_control.md).

---

## Arm interaction

Nav2 plans in **`map`** / **`base_footprint`**. MoveIt plans in **`base_link`**. When the base is **stationary**, arm pick-place during Nav2 idle states is typical; avoid arm motion during sharp base turns.

---

## Simulation

```bash
ros2 launch ugv_gazebo bringup_gazebo.launch.py   # or ugv_roarm_gazebo
ros2 launch ugv_nav nav.launch.py use_sim_time:=true use_rviz:=true
```

---

## Next

- [Command Control](command_control.md) — orchestrate Nav + arm
- [Vision](vision.md) — detect objects at goal poses
