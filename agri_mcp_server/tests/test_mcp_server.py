import asyncio

from mcp import Client
import pytest

import agri_mcp_server.server as server_module
from agri_mcp_server.server import mcp


EXPECTED_TOOLS = {
    "get_robot_status",
    "ros_check_online",
    "ros_list_nodes",
    "ros_list_topics",
}


def test_in_process_mcp_discovery_and_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_adapter(_action: str) -> dict[str, object]:
        return {"success": True, "online": True}

    monkeypatch.setattr(server_module, "run_ros_adapter", fake_adapter)

    async def scenario() -> None:
        async with Client(mcp) as client:
            discovered = await client.list_tools()
            assert {tool.name for tool in discovered.tools} == EXPECTED_TOOLS

            result = await client.call_tool("ros_check_online", {})
            assert result.is_error is False
            assert result.structured_content is not None
            assert result.structured_content["success"] is True
            assert isinstance(result.structured_content["online"], bool)

    asyncio.run(scenario())
