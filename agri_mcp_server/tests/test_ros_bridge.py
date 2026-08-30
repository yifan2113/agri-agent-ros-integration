import asyncio
from typing import cast

import pytest

from agri_mcp_server.ros_bridge import RosAction, run_ros_adapter


def test_rejects_non_allowlisted_action() -> None:
    with pytest.raises(ValueError, match="not allowlisted"):
        asyncio.run(run_ros_adapter(cast(RosAction, "start_motor")))


def test_ros_offline_is_structured() -> None:
    result = asyncio.run(run_ros_adapter("ros_check_online"))
    assert result["success"] is True
    assert isinstance(result["online"], bool)
    if not result["online"]:
        assert result["error_code"] == "ROS_MASTER_UNAVAILABLE"
