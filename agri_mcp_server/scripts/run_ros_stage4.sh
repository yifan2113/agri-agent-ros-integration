#!/usr/bin/env bash

set -Eeo pipefail

readonly ROS_RUNTIME_ROOT=/tmp/agri_stage4_ros_home
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly REPOSITORY_ROOT="$(cd -- "${PROJECT_ROOT}/.." && pwd)"
readonly CATKIN_WORKSPACE="${AGRI_CATKIN_WS:-${REPOSITORY_ROOT}/catkin_ws}"

mkdir -p "${ROS_RUNTIME_ROOT}/log"

# ROS Noetic setup scripts probe unset variables, so nounset stays disabled here.
source /opt/ros/noetic/setup.bash
source "${CATKIN_WORKSPACE}/devel/setup.bash"

export ROS_MASTER_URI=http://127.0.0.1:11311
export ROS_IP=127.0.0.1
export ROS_HOME="${ROS_RUNTIME_ROOT}"
export ROS_LOG_DIR="${ROS_RUNTIME_ROOT}/log"

exec roslaunch agri_stage2_demo status_demo.launch
