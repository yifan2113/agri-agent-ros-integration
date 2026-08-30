#!/usr/bin/env python3
"""ROS Noetic adapter executed exclusively with the system Python 3.8 runtime."""

import argparse
import json
import os
import socket
import sys
from typing import Any, Dict, List

import rosgraph
import rospy


ADAPTER_NODE = "/agri_mcp_adapter"
STATUS_SERVICE = "/agri/demo_status"


def emit(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def master_status() -> Dict[str, Any]:
    master_uri = os.environ.get("ROS_MASTER_URI", "http://127.0.0.1:11311")
    try:
        master_pid = rosgraph.Master(ADAPTER_NODE).getPid()
    except Exception as exc:  # ROS uses several XML-RPC/socket exception types.
        return {
            "success": True,
            "online": False,
            "master_uri": master_uri,
            "error_code": "ROS_MASTER_UNAVAILABLE",
            "message": str(exc),
        }

    return {
        "success": True,
        "online": True,
        "master_uri": master_uri,
        "master_pid": master_pid,
    }


def list_nodes() -> Dict[str, Any]:
    status = master_status()
    if not status["online"]:
        return {
            "success": False,
            "online": False,
            "nodes": [],
            "error_code": status["error_code"],
            "message": status["message"],
        }

    try:
        system_state = rosgraph.Master(ADAPTER_NODE).getSystemState()
        node_names = sorted(
            {
                node
                for category in system_state
                for _resource_name, nodes in category
                for node in nodes
            }
        )
    except Exception as exc:
        return {
            "success": False,
            "online": True,
            "nodes": [],
            "error_code": "ROS_NODE_LIST_FAILED",
            "message": str(exc),
        }

    return {
        "success": True,
        "online": True,
        "count": len(node_names),
        "nodes": node_names,
    }


def list_topics() -> Dict[str, Any]:
    status = master_status()
    if not status["online"]:
        return {
            "success": False,
            "online": False,
            "topics": [],
            "error_code": status["error_code"],
            "message": status["message"],
        }

    try:
        published_topics = rosgraph.Master(ADAPTER_NODE).getPublishedTopics("/")
        topics: List[Dict[str, str]] = [
            {"name": name, "type": type_name}
            for name, type_name in sorted(published_topics)
        ]
    except Exception as exc:
        return {
            "success": False,
            "online": True,
            "topics": [],
            "error_code": "ROS_TOPIC_LIST_FAILED",
            "message": str(exc),
        }

    return {
        "success": True,
        "online": True,
        "count": len(topics),
        "topics": topics,
    }


def get_robot_status() -> Dict[str, Any]:
    status = master_status()
    if not status["online"]:
        return {
            "success": False,
            "online": False,
            "error_code": status["error_code"],
            "message": status["message"],
        }

    try:
        from agr_service.srv import agr_service

        rospy.init_node(
            "agri_mcp_status_adapter",
            anonymous=True,
            disable_signals=True,
        )
        rospy.wait_for_service(STATUS_SERVICE, timeout=2.0)
        call_status = rospy.ServiceProxy(STATUS_SERVICE, agr_service)
        response = call_status(
            state="status",
            control=0,
            planning=0,
            slam=0,
            navigation=0,
        )
        service_result = json.loads(response.result)
        if not isinstance(service_result, dict):
            raise ValueError("status service result is not a JSON object")
    except (rospy.ROSException, rospy.ServiceException) as exc:
        return {
            "success": False,
            "online": True,
            "service": STATUS_SERVICE,
            "error_code": "ROBOT_STATUS_SERVICE_UNAVAILABLE",
            "message": str(exc),
        }
    except (ImportError, json.JSONDecodeError, ValueError) as exc:
        return {
            "success": False,
            "online": True,
            "service": STATUS_SERVICE,
            "error_code": "ROBOT_STATUS_INVALID_RESPONSE",
            "message": str(exc),
        }

    return {
        "success": bool(service_result.get("success")),
        "online": True,
        "service": STATUS_SERVICE,
        "robot_status": service_result,
    }


ACTIONS = {
    "ros_check_online": master_status,
    "ros_list_nodes": list_nodes,
    "ros_list_topics": list_topics,
    "get_robot_status": get_robot_status,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Agri_ROS read-only adapter")
    parser.add_argument("action", choices=sorted(ACTIONS))
    args = parser.parse_args()

    try:
        emit(ACTIONS[args.action]())
    except Exception as exc:
        emit(
            {
                "success": False,
                "error_code": "ROS_ADAPTER_INTERNAL_ERROR",
                "message": str(exc),
                "hostname": socket.gethostname(),
            }
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
