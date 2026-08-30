"""Run an end-to-end smoke test against a live local MCP server."""

from __future__ import annotations

import asyncio
import json
import os

from mcp import Client


EXPECTED_TOOLS = {
    "get_robot_status",
    "ros_check_online",
    "ros_list_nodes",
    "ros_list_topics",
}


async def main() -> None:
    endpoint = os.environ.get("AGRI_MCP_TEST_URL", "http://127.0.0.1:8000/mcp")
    async with Client(endpoint, mode="legacy") as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        assert names == EXPECTED_TOOLS, names

        results: dict[str, object] = {"tools": sorted(names)}
        for name in sorted(EXPECTED_TOOLS):
            response = await client.call_tool(name, {})
            assert response.is_error is False, response
            results[name] = response.structured_content

        check = results["ros_check_online"]
        status = results["get_robot_status"]
        nodes = results["ros_list_nodes"]
        topics = results["ros_list_topics"]
        assert isinstance(check, dict) and check.get("online") is True
        assert isinstance(status, dict) and status.get("success") is True
        assert isinstance(nodes, dict) and "/agri_stage2_status_server" in nodes.get(
            "nodes", []
        )
        assert isinstance(topics, dict) and "/rosout" in {
            item["name"] for item in topics.get("topics", [])
        }
        print(json.dumps(results, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
