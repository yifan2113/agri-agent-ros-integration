#!/usr/bin/env bash

set -Eeuo pipefail

for session_name in agri-ros-stage4 agri-mcp-stage4; do
  if tmux has-session -t "${session_name}" 2>/dev/null; then
    printf '%s: running\n' "${session_name}"
    tmux capture-pane -p -t "${session_name}" -S -12 | tail -12
  else
    printf '%s: stopped\n' "${session_name}"
  fi
done
