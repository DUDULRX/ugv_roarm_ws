# RoArm Basics

RoArm-M2 concepts used in **`ugv_roarm_ws`**: **coordinate frames**, **`hand_tcp`**, and **TCP** (tool center point). For the standalone arm kit, see [roarm_ws](https://github.com/waveshareteam/roarm_ws).

!!! note "Scope"
    This repo uses **`ROARM_MODEL=roarm_m2`** with **`GRIPPER_TYPE=angular_direct`** (direct gripper).

For URDF link/joint diagrams and TF tree images, see [Robot Description — TF Tree](description.md#tf-tree).

Already built **`ugv_roarm_ws`**? Skip to [Robot Description](description.md) or [Hardware Driver](bringup.md).

---

## Frames and TF

A **frame** is a 3D coordinate system (origin + X/Y/Z). Each URDF **link** has one. **TF** publishes how frames move relative to each other as joints rotate.

```text
world → base_link → link1 → link2 → link3 → … → hand_tcp
```

| Frame | Role |
|-------|------|
| `world` | Fixed scene frame — common RViz **Fixed Frame** in MoveIt |
| `base_link` | Robot base on the desk; most poses are expressed relative to this |
| `link1` … `link3` | Arm links (RoArm-M2) |
| `gripper_*` | Gripper meshes (`gripper_base`, fingers) |
| `hand_tcp` | Named **tool frame** for MoveIt and Servo |

`robot_state_publisher` reads `/joint_states` + URDF and broadcasts TF. RViz and MoveIt draw the arm from that tree.

### `base_link` axes (right-hand rule)

Most Cartesian commands — Servo jog, `/move_joint_cmd` x/y/z, solver poses — are expressed in **`base_link`** (on the arm; the mobile base uses `base_footprint` / `odom` — see [UGV + RoArm Basics](ugv_roarm_basics.md)). The frame follows the usual **right-hand rule** (same convention as ROS2 / RViz axis colors: **red = X**, **green = Y**, **blue = Z**):

**Click an image for full-screen view** — click outside, press **Esc**, or **×** to close.

<div class="img-row img-row-2 img-row-equal img-row-h-sm">

<figure>
<img class="img-zoom" alt="roarm_m2 axes" src="https://github.com/user-attachments/assets/2e4a131d-0831-4852-bd01-9f2012706ee2" />
<figcaption>right-hand rule</figcaption>
</figure>

<figure>
<img class="img-zoom" alt="roarm_m2 axes" src="https://github.com/user-attachments/assets/4779154d-fdea-4cf8-85a1-058c3f37d3ad" />
<figcaption>roarm_m2</figcaption>
</figure>

</div>

---

## Two TCP concepts

**TCP** = the point you want to move — where the tool approaches or touches an object. A service call like `move_joint_cmd` with `x, y, z` means “move the TCP to that position in **`base_link`**”.

In `ugv_roarm_ws` there are two layers:

| | **`hand_tcp`** | **Real TCP** |
|---|----------------|--------------|
| **What** | Frame defined in URDF / MoveIt | Physical contact point on the hardware |
| **Defined in** | `roarm_description` (fixed joint) | Analytical solver in `roarm_moveit_cmd` (`solver.hpp`) |
| **Moves when gripper opens?** | **No** — always fixed on the arm link | **No** on **`angular_direct`** (this branch) — fixed offset from `link3` |
| **Used by** | MoveIt drag marker, Servo frame, IKFast tip | `/get_pose_cmd`, `/move_*_cmd` |

On **`angular_direct`**, **`hand_tcp` ≈ real TCP** — the RViz marker and physical tip stay aligned for pick-place.

---

### `hand_tcp` — planning frame (URDF / MoveIt)

`hand_tcp` is a **fixed** joint in URDF. It does **not** follow finger motion.

| Model | Parent link | URDF joint |
|-------|-------------|------------|
| **roarm_m2** *(this repo)* | `link3` | `link3_to_hand_tcp` |

MoveIt group **`hand`** plans to `hand_tcp`. The RViz drag marker uses **`hand_tcp`**; in Servo, **`e`** jogs in **`hand_tcp`**, **`w`** in **`base_link`**.

Check the live transform:

```bash
ros2 run tf2_ros tf2_echo base_link hand_tcp
```

---

### Real TCP — the hardware

The solver computes XYZ in **`base_link`** from joint angles. With **`GRIPPER_TYPE=angular_direct`**:

- Jaw rotates around `gripper_joint`, but the **contact point offset from `link3` is treated as fixed**.
- **`hand_tcp` ≈ real TCP** — RViz marker and physical tip stay aligned for pick-place.
- For **`move_joint_cmd`**, the `gripper` field is optional for IK; jaw motion uses **`/gripper_cmd`**.

<img class="img-zoom img-center" width="200" height="100" alt="roarm_m2 angular_direct tcp"  src="https://github.com/user-attachments/assets/5bc8d7f7-5d82-4b31-bd76-990fd8a13a03" />

Gripper mesh selection: [Gripper Configuration](description.md#gripper-configuration).

---

## Which feature uses which frame?

| Feature | Frame / TCP |
|---------|-------------|
| MoveIt — drag & **Plan & Execute** | `hand_tcp` (URDF) |
| MoveIt Servo — **`w`** / **`e`** or gamepad **X** / **Y** | `base_link` / `hand_tcp` |
| `/get_pose_cmd` | Solver real TCP in `base_link` |
| `/move_joint_cmd`, `/move_line_cmd`, … | Solver IK target → MoveIt executes arm joints |

**Units:** TF, URDF, MoveIt, and service responses use **meters** and **radians**.

---

## Related Tutorials

| Chapter | What it adds |
|---------|----------------|
| [Installation](installation.md) | Build **`roarm_ws`** and set `ROARM_MODEL`, `GRIPPER_TYPE` (and `GZ_VERSION` if you use Gazebo) |
| [Robot Description](description.md#tf-tree) | TF tree diagrams & joint tables |
| [MoveIt2](moveit2.md) | Drag marker in RViz |
| [MoveIt Servo](moveit_servo.md) | Keyboard / gamepad arm jog |
| [Command Control](command_control.md) | *(Optional)* CLI services & poses |
| [ROS2 Basics — TF2](ros2_basics.md#tf2) | Debug TF with ROS2 tools |
