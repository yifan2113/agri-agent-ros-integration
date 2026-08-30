"""Read-only MCP tools for the stage 3 Agri_ROS integration."""

from __future__ import annotations

import os
from ipaddress import ip_address, ip_network
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from agri_mcp_server import __version__
from agri_mcp_server.ros_bridge import run_ros_adapter


mcp = MCPServer(
    name="agri-ros",
    title="Agri_ROS Safe Tools",
    description="Read-only MCP facade for ROS Noetic and Agri_ROS.",
    instructions=(
        "Stages 3 and 4 are status-only. These tools never publish ROS topics, start launch "
        "files, or control navigation, SLAM, motors, sensors, or actuators."
    ),
    version=__version__,
)

TAILSCALE_IPV4_NETWORK = ip_network("100.64.0.0/10")


def allowed_http_hosts() -> list[str]:
    """Build the DNS-rebinding allowlist for local and optional Tailscale access."""
    allowed = ["127.0.0.1:*", "localhost:*"]
    forwarded_host = os.environ.get("AGRI_MCP_TAILSCALE_HOST")
    if forwarded_host is None:
        return allowed

    try:
        forwarded_ip = ip_address(forwarded_host)
    except ValueError as exc:
        raise ValueError("AGRI_MCP_TAILSCALE_HOST must be an IPv4 address") from exc
    if forwarded_ip.version != 4 or forwarded_ip not in TAILSCALE_IPV4_NETWORK:
        raise ValueError("AGRI_MCP_TAILSCALE_HOST must be inside 100.64.0.0/10")

    allowed.append(f"{forwarded_ip}:*")
    return allowed


def validate_bind_host(host: str) -> None:
    """Permit localhost, or the exact validated Tailscale host for stage 4."""
    if host in {"127.0.0.1", "localhost"}:
        return

    tailscale_host = os.environ.get("AGRI_MCP_TAILSCALE_HOST")
    if tailscale_host is None or host != tailscale_host:
        raise RuntimeError(
            "MCP may bind only to localhost or the configured Tailscale address."
        )
    allowed_http_hosts()

@mcp.tool(structured_output=True)
async def ros_check_online() -> dict[str, Any]:
    """Check whether the localhost ROS master is reachable; performs no control action."""
    return await run_ros_adapter("ros_check_online")


@mcp.tool(structured_output=True)
async def ros_list_nodes() -> dict[str, Any]:
    """List names registered with the localhost ROS master; read-only."""
    return await run_ros_adapter("ros_list_nodes")


@mcp.tool(structured_output=True)
async def ros_list_topics() -> dict[str, Any]:
    """List published ROS topic names and message types; read-only."""
    return await run_ros_adapter("ros_list_topics")


@mcp.tool(structured_output=True)
async def get_robot_status() -> dict[str, Any]:
    """Call the stage 2 status-only ROS service with every control field fixed to zero."""
    return await run_ros_adapter("get_robot_status")


def main() -> None:
    host = os.environ.get("AGRI_MCP_HOST", "127.0.0.1")
    validate_bind_host(host)

    port = int(os.environ.get("AGRI_MCP_PORT", "8000"))
    if not 1 <= port <= 65535:
        raise ValueError("AGRI_MCP_PORT must be between 1 and 65535")

    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_http_hosts(),
        allowed_origins=[],
    )
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        max_request_body_size=64 * 1024,
        transport_security=transport_security,
    )


if __name__ == "__main__":
    main()
