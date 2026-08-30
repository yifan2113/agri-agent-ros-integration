#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

export AGRI_MCP_HOST=127.0.0.1
export AGRI_MCP_PORT="${AGRI_MCP_PORT:-8000}"

exec "${PROJECT_ROOT}/.venv/bin/agri-mcp-server"
