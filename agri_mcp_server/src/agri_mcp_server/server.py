"""Read-only MCP tools for the stage 3 Agri_ROS integration."""

from __future__ import annotations

import os
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
        "Stage 3 is status-only. These tools never publish ROS topics, start launch "
        "files, or control navigation, SLAM, motors, sensors, or actuators."
    ),
    version=__version__,
)

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
    if host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Stage 3 may bind only to localhost.")

    port = int(os.environ.get("AGRI_MCP_PORT", "8000"))
    if not 1 <= port <= 65535:
        raise ValueError("AGRI_MCP_PORT must be between 1 and 65535")

    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*"],
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
