#!/bin/bash
set -e

WS=/home/ws/ugv_roarm_ws
BASHRC=~/.bashrc

add_if_not_exist () {
    grep -qxF "$1" "$BASHRC" || echo "$1" >> "$BASHRC"
}

echo "=============================="
echo "   UGV RoArm Build & Config Script"
echo "=============================="
echo

# ---------- Model selection ----------
echo
echo "[1/5] Select UGV model:"
select UGV_MODEL in ugv_rover ugv_beast rasp_rover; do
    [ -n "$UGV_MODEL" ] && break
    echo "Invalid selection."
done

echo
echo "Select LiDAR model:"
select LDLIDAR_MODEL in ld19 ld06 stl27l; do
    [ -n "$LDLIDAR_MODEL" ] && break
    echo "Invalid selection."
done

echo
echo "Selected configuration:"
echo "  UGV_MODEL     = $UGV_MODEL"
echo "  LDLIDAR_MODEL = $LDLIDAR_MODEL"

read -p "Save model selection to ~/.bashrc? [y/N]: " SAVE_ENV
if [[ "$SAVE_ENV" =~ ^[Yy]$ ]]; then
    add_if_not_exist "export UGV_MODEL=$UGV_MODEL"
    add_if_not_exist "export LDLIDAR_MODEL=$LDLIDAR_MODEL"
    echo "✔ Model selection saved to ~/.bashrc"
else
    export UGV_MODEL
    export LDLIDAR_MODEL
    echo "✔ Model selection exported for current shell only"
fi

# ---------- Model selection ----------
echo
echo "[2/5] Select ROARM model:"
select ROARM_MODEL in roarm_m2 roarm_m3; do
    [ -n "$ROARM_MODEL" ] && break
    echo "Invalid selection."
done

echo

echo
echo "[3/5] Select GRIPPER type:"
select GRIPPER_TYPE in angular_direct angular_gear; do
    [ -n "$GRIPPER_TYPE" ] && break
    echo "Invalid selection."
done

echo

echo
echo "Selected configuration:"
echo "  ROARM_MODEL     = $ROARM_MODEL"
echo "  GRIPPER_TYPE    = $GRIPPER_TYPE"

read -p "Save model selection to ~/.bashrc? [y/N]: " SAVE_ENV
if [[ "$SAVE_ENV" =~ ^[Yy]$ ]]; then
    add_if_not_exist "export ROARM_MODEL=$ROARM_MODEL"
    add_if_not_exist "export GRIPPER_TYPE=$GRIPPER_TYPE"
    echo "✔ Model selection saved to ~/.bashrc"
else
    export ROARM_MODEL
    export GRIPPER_TYPE
    echo "✔ Model selection exported for current shell only"
fi

# ---------- Build ----------
echo
echo "[4/5] Building workspace: $WS"
cd "$WS" || exit 1

colcon build \
  --packages-select \
    ugv_roarm_cmd \
    ugv_roarm_moveit_ikfast_plugins \
    ugv_roarm_moveit_mtc_demo \
    ugv_roarm_moveit_servo \
  --symlink-install \
  --executor sequential

colcon build \
  --packages-select \
    ugv_roarm_description \
    ugv_roarm_bringup \
    ugv_roarm_moveit \
    ugv_roarm_gazebo \
  --symlink-install \
  --executor sequential

# ---------- Final env ----------
echo
echo "[5/5] Finalizing environment..."
add_if_not_exist "source $WS/install/setup.bash"
source ~/.bashrc

echo
echo "=============================="
echo "✔ Environment ready."
echo "✔ UGV_MODEL=$UGV_MODEL"
echo "✔ LDLIDAR_MODEL=$LDLIDAR_MODEL"
echo "✔ ROARM_MODEL=$ROARM_MODEL"
echo "✔ GRIPPER_TYPE=$GRIPPER_TYPE"
echo "=============================="

