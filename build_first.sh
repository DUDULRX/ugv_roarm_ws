#!/bin/bash
set -e

WS=/home/ws/ugv_roarm_ws
BASHRC=~/.bashrc

# This workspace currently targets UGV Rover + RoArm-M2 + angular_direct gripper only.
UGV_MODEL=ugv_rover
ROARM_MODEL=roarm_m2
GRIPPER_TYPE=angular_direct

add_if_not_exist () {
    grep -qxF "$1" "$BASHRC" || echo "$1" >> "$BASHRC"
}

echo "=============================="
echo "   UGV RoArm Build & Config Script"
echo "   Target: UGV Rover + RoArm-M2 (angular_direct)"
echo "=============================="
echo

echo "Fixed configuration:"
echo "  UGV_MODEL    = $UGV_MODEL"
echo "  ROARM_MODEL  = $ROARM_MODEL"
echo "  GRIPPER_TYPE = $GRIPPER_TYPE"
echo

echo "[1/2] Select LiDAR model:"
select LDLIDAR_MODEL in ld19 ld06 stl27l; do
    [ -n "$LDLIDAR_MODEL" ] && break
    echo "Invalid selection."
done

echo
echo "Selected configuration:"
echo "  UGV_MODEL      = $UGV_MODEL"
echo "  ROARM_MODEL    = $ROARM_MODEL"
echo "  LDLIDAR_MODEL  = $LDLIDAR_MODEL"
echo "  GRIPPER_TYPE   = $GRIPPER_TYPE"

read -p "Save to ~/.bashrc? [y/N]: " SAVE_ENV
if [[ "$SAVE_ENV" =~ ^[Yy]$ ]]; then
    add_if_not_exist "export UGV_MODEL=$UGV_MODEL"
    add_if_not_exist "export ROARM_MODEL=$ROARM_MODEL"
    add_if_not_exist "export LDLIDAR_MODEL=$LDLIDAR_MODEL"
    add_if_not_exist "export GRIPPER_TYPE=$GRIPPER_TYPE"
    echo "✔ Configuration saved to ~/.bashrc"
else
    export UGV_MODEL
    export ROARM_MODEL
    export LDLIDAR_MODEL
    export GRIPPER_TYPE
    echo "✔ Configuration exported for current shell only"
fi

echo
echo "[2/2] Building workspace: $WS"
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

echo
echo "Finalizing environment..."
add_if_not_exist "source $WS/install/setup.bash"
source ~/.bashrc

echo
echo "=============================="
echo "✔ Environment ready."
echo "✔ UGV_MODEL=$UGV_MODEL"
echo "✔ ROARM_MODEL=$ROARM_MODEL"
echo "✔ LDLIDAR_MODEL=$LDLIDAR_MODEL"
echo "✔ GRIPPER_TYPE=$GRIPPER_TYPE"
echo "=============================="
