# Robot Description

**`ugv_roarm_description`** provides the combined URDF/xacro for **UGV Rover + RoArm-M2**.

The top-level file **`ugv_roarm.xacro`** includes:

- **UGV Rover** base from **`ugv_description`** (`ugv_model:=ugv_rover`)
- **RoArm-M2** from **`ugv_roarm_description/urdf/roarm/bases/roarm_m2.xacro`**
- Fixed mount joint **`ugv_roarm_base_link_joint`** — Rover-specific offset (`xyz="-0.014242 0 0.04"` for M2 on `ugv_rover`)

MoveIt loads the same xacro via **`ugv_roarm_moveit/config/ugv_roarm.urdf.xacro`** with mappings for `gripper_type` and Gazebo.

---

## Package file layout

```
ugv_roarm_description/
├── urdf/
│   ├── ugv_roarm.xacro             # top-level combined model
│   ├── materials.xacro
│   ├── empty.urdf                  # optional extras hook (urdf_extras)
│   ├── ugv/
│   │   ├── bases/                  # local UGV base xacro copies
│   │   │   ├── ugv_rover.xacro     # UGV_MODEL=ugv_rover (this branch)
│   │   │   ├── rasp_rover.xacro
│   │   │   ├── ugv_beast.xacro
│   │   │   └── cobra_*.xacro
│   │   └── gazebo/                 # UGV Gazebo plugins (sim)
│   │       ├── ugv_rover.gazebo
│   │       └── ...
│   └── roarm/
│       ├── bases/
│       │   ├── roarm_m2.xacro      # ROARM_MODEL=roarm_m2 (this branch)
│       │   └── roarm_m3.xacro
│       └── gazebo/
│           ├── roarm_m2.gazebo
│           ├── roarm_m2.trans
│           └── roarm_m3.*
├── meshes/
│   └── ugv_roarm_base_link.stl     # arm mount plate on chassis
├── config/
│   ├── initial_positions_roarm_m2.yaml
│   └── initial_positions_roarm_m3.yaml
├── launch/
│   └── display.launch.py           # URDF + RViz (use_rviz:=true)
└── rviz/
    └── view_description.rviz
```

| Path | Purpose |
|------|---------|
| `urdf/ugv_roarm.xacro` | Main entry — includes UGV base + RoArm + mount joint **`ugv_roarm_base_link_joint`** |
| `urdf/roarm/bases/roarm_m2.xacro` | RoArm-M2 chain, gripper variant, optional camera macros |
| `urdf/roarm/gazebo/` | Arm Gazebo plugins and transmissions when **`use_gazebo:=true`** ([Gazebo](gazebo.md)) |
| `meshes/ugv_roarm_base_link.stl` | Mount bracket between **`base_link`** and **`ugv_roarm_base_link`** |
| `launch/display.launch.py` | `robot_state_publisher` + optional joint GUI or `ros2_control` |
| `config/initial_positions_roarm_m2.yaml` | Default arm joint positions for `ros2_control` / simulation |

Main xacro chain (expanded at launch time):

```text
ugv_roarm_description/urdf/ugv_roarm.xacro
  → ugv_description/urdf/bases/<UGV_MODEL>.xacro      # chassis, wheels, LiDAR, sensors
  → ugv_roarm_description/urdf/roarm/bases/<ROARM_MODEL>.xacro
  → roarm_description/meshes/…                        # arm link STLs (external package)
```

On this branch, **`UGV_MODEL=ugv_rover`** and **`ROARM_MODEL=roarm_m2`**. MoveIt and Gazebo use the same xacro via **`ugv_roarm_moveit/config/ugv_roarm.urdf.xacro`**.

---

## Environment variables

| Variable | Value (this repo) | Effect |
|----------|-------------------|--------|
| `UGV_MODEL` | **`ugv_rover`** | UGV Rover base mesh and mount |
| `ROARM_MODEL` | **`roarm_m2`** | M2 arm chain |
| `GRIPPER_TYPE` | **`angular_direct`** | Direct M2 gripper mesh (this branch) |

---

## Launch — visualize without hardware

Joint sliders (no serial):

```bash
ros2 launch ugv_roarm_description display.launch.py \
  use_rviz:=true \
  rviz_config:=description
```

With **`ros2_control`** (same as bringup/MoveIt path):

```bash
ros2 launch ugv_roarm_description display.launch.py \
  use_rviz:=true \
  rviz_config:=moveit
```

Ensure `UGV_MODEL=ugv_rover` and `ROARM_MODEL=roarm_m2` are exported.

---

## RViz configurations

| `rviz_config` | Config file | Typical use |
|---------------|-------------|-------------|
| `description` | `view_description.rviz` | URDF / sliders (Fixed Frame **`base_footprint`**) |
| `bringup` | `view_bringup.rviz` | Live robot + sensors (Fixed Frame **`odom`**; real-hardware note below) |
| `moveit` | `interact.rviz` | Motion Planning |
| `moveit_servo` | `servo_control.rviz` | Servo teleop |
| `moveit_mtc` | `mtc.rviz` | MTC task solution |

!!! note "RViz empty with `rviz_config:=bringup` (real robot)?"
    On **hardware**, **`view_bringup.rviz`** expects Fixed Frame **`odom`**, which may not be in TF at startup. Set **Global Options → Fixed Frame** to **`base_footprint`** or **`base_link`**. **Gazebo** publishes **`odom`** — see [Gazebo](gazebo.md). Details: [Hardware Driver — RViz Fixed Frame](bringup.md#rviz-bringup-fixed-frame).

---

## Gripper configuration {#gripper-configuration}

This branch uses **`GRIPPER_TYPE=angular_direct`**. See [RoArm Basics](roarm_basics.md).

---

## TF tree {#tf-tree}

```text
base_footprint → base_link → ugv_roarm_base_link → link1 → link2 → link3 → hand_tcp
```

Sensor frames on the UGV Rover base are defined in the URDF — see [UGV Basics](ugv_basics.md). Arm details: [RoArm Basics](roarm_basics.md).

---

## Next

- [Hardware Driver](bringup.md) — publish live joint states from hardware
- [MoveIt2](moveit2.md) — planning with the same URDF
