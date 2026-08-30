#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly TAILSCALE_BIN=/usr/bin/tailscale

tailscale_host="${AGRI_MCP_TAILSCALE_HOST:-$(${TAILSCALE_BIN} ip -4)}"
if [[ ! ${tailscale_host} =~ ^100\.(6[4-9]|[789][0-9]|1[01][0-9]|12[0-7])\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
  printf 'Refusing stage 4 start: invalid Tailscale IPv4 address: %s\n' \
    "${tailscale_host}" >&2
  exit 1
fi

export AGRI_MCP_HOST="${tailscale_host}"
export AGRI_MCP_PORT="${AGRI_MCP_PORT:-8000}"
export AGRI_MCP_TAILSCALE_HOST="${tailscale_host}"

printf 'MCP Tailscale endpoint: http://%s:%s/mcp\n' \
  "${AGRI_MCP_TAILSCALE_HOST}" "${AGRI_MCP_PORT}"

exec "${PROJECT_ROOT}/.venv/bin/agri-mcp-server"
