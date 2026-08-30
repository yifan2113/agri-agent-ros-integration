"""Subprocess boundary between modern MCP Python and ROS Noetic Python."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Literal


RosAction = Literal[
    "ros_check_online",
    "ros_list_nodes",
    "ros_list_topics",
    "get_robot_status",
]

ALLOWED_ACTIONS = {
    "ros_check_online",
    "ros_list_nodes",
    "ros_list_topics",
    "get_robot_status",
}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_RUNNER = PROJECT_ROOT / "scripts" / "run_ros_adapter.sh"


async def run_ros_adapter(
    action: RosAction, timeout_seconds: float = 5.0
) -> dict[str, Any]:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"ROS action is not allowlisted: {action}")

    try:
        process = await asyncio.create_subprocess_exec(
            str(ADAPTER_RUNNER),
            action,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        return {
            "success": False,
            "error_code": "ROS_ADAPTER_TIMEOUT",
            "message": f"ROS adapter exceeded {timeout_seconds:.1f} seconds.",
        }
    except OSError as exc:
        return {
            "success": False,
            "error_code": "ROS_ADAPTER_START_FAILED",
            "message": str(exc),
        }

    stdout = stdout_bytes.decode(errors="replace").strip()
    stderr = stderr_bytes.decode(errors="replace").strip()
    if not stdout:
        return {
            "success": False,
            "error_code": "ROS_ADAPTER_EMPTY_RESPONSE",
            "message": stderr[-1000:],
            "return_code": process.returncode,
        }

    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error_code": "ROS_ADAPTER_INVALID_JSON",
            "message": str(exc),
            "return_code": process.returncode,
        }

    if not isinstance(result, dict):
        return {
            "success": False,
            "error_code": "ROS_ADAPTER_INVALID_RESPONSE",
            "message": "ROS adapter response must be a JSON object.",
        }

    if process.returncode != 0 and result.get("success") is not False:
        result.update(
            success=False,
            error_code="ROS_ADAPTER_FAILED",
            return_code=process.returncode,
        )
    return result
