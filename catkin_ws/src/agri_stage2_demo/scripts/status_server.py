#!/usr/bin/env python3

import json
import socket
from typing import Any, Dict

import rospy

from agr_service.srv import agr_service, agr_serviceRequest, agr_serviceResponse


SERVICE_NAME = "/agri/demo_status"


def make_result(success: bool, message: str, **extra: Any) -> str:
    result: Dict[str, Any] = {
        "success": success,
        "stage": 2,
        "mode": "safe_status_only",
        "ros_online": True,
        "hardware_connected": False,
        "hostname": socket.gethostname(),
        "message": message,
    }
    result.update(extra)
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


def handle_status(request: agr_serviceRequest) -> agr_serviceResponse:
    control_fields = {
        "control": request.control,
        "planning": request.planning,
        "slam": request.slam,
        "navigation": request.navigation,
    }
    nonzero_fields = {
        name: value for name, value in control_fields.items() if value != 0
    }

    if nonzero_fields:
        rospy.logwarn("Rejected unsafe stage 2 request: %s", nonzero_fields)
        return agr_serviceResponse(
            result=make_result(
                False,
                "Stage 2 accepts status-only requests; all control fields must be zero.",
                error_code="CONTROL_DISABLED_STAGE2",
                rejected_fields=nonzero_fields,
                requested_state=request.state,
            )
        )

    if request.state.strip().lower() != "status":
        rospy.logwarn("Rejected unsupported stage 2 state: %s", request.state)
        return agr_serviceResponse(
            result=make_result(
                False,
                "Stage 2 accepts only state='status'.",
                error_code="UNSUPPORTED_STATE_STAGE2",
                requested_state=request.state,
            )
        )

    return agr_serviceResponse(
        result=make_result(
            True,
            "Agri_ROS stage 2 status service is online.",
            requested_state=request.state,
        )
    )


def main() -> None:
    rospy.init_node("agri_stage2_status_server")
    rospy.Service(SERVICE_NAME, agr_service, handle_status)
    rospy.loginfo("Safe stage 2 service ready at %s", SERVICE_NAME)
    rospy.spin()


if __name__ == "__main__":
    main()
