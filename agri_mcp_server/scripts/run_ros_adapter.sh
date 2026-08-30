#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly REPOSITORY_ROOT="$(cd -- "${PROJECT_ROOT}/.." && pwd)"
readonly CATKIN_WORKSPACE="${AGRI_CATKIN_WS:-${REPOSITORY_ROOT}/catkin_ws}"

if [[ $# -ne 1 ]]; then
  printf 'usage: %s <allowlisted-action>\n' "$0" >&2
  exit 2
fi

case "$1" in
  ros_check_online|ros_list_nodes|ros_list_topics|get_robot_status)
    ;;
  *)
    printf 'action is not allowlisted: %s\n' "$1" >&2
    exit 2
    ;;
esac

set +u
source /opt/ros/noetic/setup.bash
source "${CATKIN_WORKSPACE}/devel/setup.bash"
set -u

export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_HOME=/tmp/agri_mcp_ros_home
mkdir -p "${ROS_HOME}"

exec /usr/bin/python3 \
  "${PROJECT_ROOT}/src/agri_mcp_server/ros_adapter.py" \
  "$1"
