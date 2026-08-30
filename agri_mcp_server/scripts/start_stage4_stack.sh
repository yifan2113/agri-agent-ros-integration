#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly ROS_SESSION=agri-ros-stage4
readonly MCP_SESSION=agri-mcp-stage4

if ! tmux has-session -t "${ROS_SESSION}" 2>/dev/null; then
  tmux new-session -d -s "${ROS_SESSION}" \
    "${PROJECT_ROOT}/scripts/run_ros_stage4.sh"
fi

if ! tmux has-session -t "${MCP_SESSION}" 2>/dev/null; then
  tmux new-session -d -s "${MCP_SESSION}" \
    "${PROJECT_ROOT}/scripts/run_server_stage4.sh"
fi

printf 'Stage 4 tmux sessions:\n'
tmux list-sessions -F '#{session_name}: #{session_windows} window(s), #{session_attached} attached' \
  | awk '$1 == "agri-ros-stage4:" || $1 == "agri-mcp-stage4:"'

printf '\nInspect logs with:\n'
printf '  tmux capture-pane -p -t %s -S -80\n' "${ROS_SESSION}"
printf '  tmux capture-pane -p -t %s -S -80\n' "${MCP_SESSION}"
