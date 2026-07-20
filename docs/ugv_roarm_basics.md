# UGV + RoArm Basics

Concepts for the **UGV Rover + RoArm-M2** combination in **`ugv_roarm_ws`**. For more detail, see [RoArm Basics](roarm_basics.md) and [UGV Basics](ugv_basics.md).

!!! note "Scope"
    This repo documents **`UGV_MODEL=ugv_rover`** and **`ROARM_MODEL=roarm_m2`** only.

---

## One robot, one driver

In standalone workspaces:

| Workspace | Driver | Serial |
|-----------|--------|--------|
| [ugv_ws](https://github.com/waveshareteam/ugv_ws) | `ugv_bringup` | `/dev/ttyAMA0` — base only |
| [roarm_ws](https://github.com/waveshareteam/roarm_ws) | `roarm_driver` | USB — arm only |

In **`ugv_roarm_ws`**, **`ugv_roarm_bringup`** handles **both** on the UGV Rover ESP32 link:

- **`/cmd_vel`** → wheel motion
- **`/joint_states`** → RoArm-M2 joint targets
- IMU, battery, LED control on the same UART

Do **not** run `ugv_bringup` and `ugv_roarm_bringup` together on the same port.

---

## Combined TF tree (simplified)

```text
map → odom → base_footprint → base_link → ugv_roarm_base_link → link1 → link2 → link3 → hand_tcp
```

| Frame | Subsystem | Role |
|-------|-----------|------|
| `odom`, `base_footprint` | UGV Rover | Mobile-base localization |
| `base_link` | UGV Rover | Chassis; arm mounted here |
| `ugv_roarm_base_link` | Mount | Fixed joint (Rover + M2 offset) |
| `link1` … `hand_tcp` | RoArm-M2 | Arm chain |

When the rover drives, the arm TF subtree moves with `base_link`. MoveIt plans in **`base_link`**.

---

## Environment variables

```bash
export UGV_MODEL=ugv_rover
export ROARM_MODEL=roarm_m2
export GRIPPER_TYPE=angular_direct
export LDLIDAR_MODEL=ld19            # match your LiDAR
```

Set via [Installation](installation.md) (`build_first.sh`) or `~/.bashrc`.

---

## Typical terminal layout

| Terminal | Role | Example |
|----------|------|---------|
| **T0** | Robot stack — always first | `bringup_lidar.launch.py` (teleop, vision, or MoveIt/Servo with `use_moveit_servo:=true`) |
| **T1** | Arm or base teleop | MoveIt / Servo / `keyboard_ctrl` |

---

## External packages from ugv_ws / roarm_ws {#external-packages-from-ugv_ws--roarm_ws}

This workspace **builds** the `ugv_roarm_*` packages locally. Teleop and description pieces come from sibling packages (factory image or clone [ugv_ws](https://github.com/waveshareteam/ugv_ws) + [roarm_ws](https://github.com/waveshareteam/roarm_ws)):

| Package | Source | Used for |
|---------|--------|----------|
| `ugv_tools` | ugv_ws | `keyboard_ctrl`, gamepad teleop |
| `ugv_description` | ugv_ws | UGV Rover base xacro in `ugv_roarm.xacro` |
| `roarm_moveit_cmd`, `roarm_msgs` | roarm_ws | Optional CLI motion services — [Command Control](command_control.md) |

---

## Next steps

- [Installation](installation.md) — clone, `build_first.sh`
- [Robot Description](description.md) — UGV Rover + M2 URDF
- [Hardware Driver](bringup.md) — launch bringup on real hardware
