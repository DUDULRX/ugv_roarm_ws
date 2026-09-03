#!/bin/bash
set -e

WS=/home/ws/ugv_roarm_ws
BASHRC=~/.bashrc

UGV_WS=/home/ws/ugv_ws
ROARM_WS=/home/ws/roarm_ws

LDLIDAR_MODEL=ld19
UGV_MODEL=ugv_rover
ROARM_MODEL=roarm_m2
GRIPPER_TYPE=angular_direct

add_if_not_exist () {
    grep -qxF "$1" "$BASHRC" || echo "$1" >> "$BASHRC"
}

set_bashrc_export () {
    local var="$1"
    local val="$2"
    local line="export ${var}=${val}"
    if grep -qE "^export ${var}=" "$BASHRC" 2>/dev/null; then
        sed -i -E "s|^export ${var}=.*$|${line}|" "$BASHRC"
    else
        echo "$line" >> "$BASHRC"
    fi
}

source_if_exists () {
    if [ -f "$1" ]; then
        echo "✔ Sourcing $1"
        # shellcheck disable=SC1090
        source "$1"
    else
        echo "⏭ Not found, skip: $1"
    fi
}

load_bashrc_var () {
    local var="$1"
    local val
    val=$(grep -E "^export ${var}=" "$BASHRC" 2>/dev/null | tail -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)
    if [ -n "$val" ]; then
        export "$var=$val"
    fi
}

detect_installed_gz () {
    if dpkg -l 2>/dev/null | awk '
        $1 ~ /^ii/ && ($2 ~ /^gz-harmonic/ || $2 ~ /^ros-humble-ros-gzharmonic/) {found=1}
        END {exit !found}'; then
        echo "harmonic"
    elif dpkg -l 2>/dev/null | awk '
        $1 ~ /^ii/ && $2 ~ /^(gazebo|libgazebo11|ros-humble-gazebo-ros)(|-.*)$/ {found=1}
        END {exit !found}'; then
        echo "classic"
    else
        echo ""
    fi
}

reload_bashrc () {
    # shellcheck disable=SC1090
    source "$BASHRC" 2>/dev/null || true

    # 非交互脚本里 bashrc 可能直接 return，再强制加载关键变量
    while IFS= read -r line; do
        eval "$line"
    done < <(grep -E '^export (GZ_VERSION|UGV_MODEL|LDLIDAR_MODEL|ROARM_MODEL|GRIPPER_TYPE)=' "$BASHRC" 2>/dev/null || true)

    echo "✔ Reloaded env from ~/.bashrc (GZ_VERSION=${GZ_VERSION:-none})"
}

echo "=============================="
echo "   UGV RoArm Build & Config Script"
echo "   Target: UGV Rover + RoArm-M2 (angular_direct)"
echo "=============================="
echo

load_bashrc_var GZ_VERSION
DETECTED_GZ="$(detect_installed_gz)"
GAZEBO_INSTALLED=false

if [ -n "$DETECTED_GZ" ]; then
    GAZEBO_INSTALLED=true
    GZ_VERSION="${GZ_VERSION:-$DETECTED_GZ}"
fi

echo "Fixed configuration:"
echo "  LDLIDAR_MODEL = $LDLIDAR_MODEL"
echo "  UGV_MODEL     = $UGV_MODEL"
echo "  ROARM_MODEL   = $ROARM_MODEL"
echo "  GRIPPER_TYPE  = $GRIPPER_TYPE"
echo "  Gazebo        = $GAZEBO_INSTALLED"
echo "  GZ_VERSION    = ${GZ_VERSION:-none}"
echo "  Detected GZ   = ${DETECTED_GZ:-none}"
echo

echo "[1/2] Configuration"
read -p "Save to ~/.bashrc? [y/N]: " SAVE_ENV
if [[ "$SAVE_ENV" =~ ^[Yy]$ ]]; then
    set_bashrc_export UGV_MODEL "$UGV_MODEL"
    set_bashrc_export ROARM_MODEL "$ROARM_MODEL"
    set_bashrc_export LDLIDAR_MODEL "$LDLIDAR_MODEL"
    set_bashrc_export GRIPPER_TYPE "$GRIPPER_TYPE"
    echo "✔ Configuration saved to ~/.bashrc"
else
    export UGV_MODEL ROARM_MODEL LDLIDAR_MODEL GRIPPER_TYPE
    echo "✔ Configuration exported for current shell only"
fi

echo
echo "Preparing build environment..."
source_if_exists /opt/ros/humble/setup.bash
source_if_exists "$UGV_WS/install/setup.bash"
source_if_exists "$ROARM_WS/install/setup.bash"
export UGV_MODEL ROARM_MODEL LDLIDAR_MODEL GRIPPER_TYPE

echo
echo "[2/2] Building workspace: $WS"
if [ ! -d "$WS" ]; then
    echo "❌ Workspace not found: $WS"
    exit 1
fi
cd "$WS" || exit 1

colcon build \
  --packages-select \
    ugv_roarm_cmd \
    ugv_roarm_moveit_ikfast_plugins \
    ugv_roarm_moveit_mtc_demo \
    ugv_roarm_moveit_servo \
  --symlink-install \
  --executor sequential

UGV_ROARM_PKGS=(
  ugv_roarm_description
  ugv_roarm_bringup
  ugv_roarm_moveit
)

if [ "$GAZEBO_INSTALLED" = true ]; then
  echo "✔ Gazebo detected (${GZ_VERSION}) → build ugv_roarm_gazebo"
  UGV_ROARM_PKGS+=(ugv_roarm_gazebo)
else
  echo "⏭ Skip ugv_roarm_gazebo (Gazebo not installed — optional on the robot / Docker)"
fi

colcon build \
  --packages-select "${UGV_ROARM_PKGS[@]}" \
  --symlink-install \
  --executor sequential

echo
echo "Finalizing environment..."
add_if_not_exist "source /opt/ros/humble/setup.bash"
add_if_not_exist "source $WS/install/setup.bash"

source_if_exists /opt/ros/humble/setup.bash
source_if_exists "$WS/install/setup.bash"

echo
echo "=============================="
echo "✔ Environment ready."
echo "✔ UGV_MODEL=$UGV_MODEL"
echo "✔ ROARM_MODEL=$ROARM_MODEL"
echo "✔ LDLIDAR_MODEL=$LDLIDAR_MODEL"
echo "✔ GRIPPER_TYPE=$GRIPPER_TYPE"
echo "✔ Gazebo installed: $GAZEBO_INSTALLED"
echo "✔ GZ_VERSION=${GZ_VERSION:-none}"
echo "✔ Workspace=$WS"
echo "=============================="

reload_bashrc
