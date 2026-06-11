#!/bin/bash
set -e

WS=/home/ws/ugv_roarm_ws
cd $WS || exit 1

PACKAGES=(
    ugv_roarm_cmd
    ugv_roarm_moveit_ikfast_plugins
    ugv_roarm_moveit_mtc_demo
    ugv_roarm_moveit_servo
    ugv_roarm_description
)

echo "=============================="
echo "  Select packages to build"
echo "=============================="

for i in "${!PACKAGES[@]}"; do
  printf "[%2d] %s\n" $((i+1)) "${PACKAGES[$i]}"
done

echo
read -p "Please enter the package number to be compiled (space-separated): " SELECTION

SELECTED_PKGS=""

for index in $SELECTION; do
  pkg="${PACKAGES[$((index-1))]}"
  if [ -n "$pkg" ]; then
    SELECTED_PKGS="$SELECTED_PKGS $pkg"
  else
    echo "❌ Invalid number: $index"
    exit 1
  fi
done

echo
echo "✔ The following packages will be compiled.:"
echo "$SELECTED_PKGS"
echo

colcon build \
  --packages-select $SELECTED_PKGS \
  --symlink-install \
  --executor sequential

echo
echo "===== Build finished ====="
source install/setup.bash
echo "✔ Workspace sourced."
