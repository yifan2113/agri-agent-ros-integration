cmake_minimum_required(VERSION 3.0.2)
project(agri_stage2_demo)

find_package(catkin REQUIRED COMPONENTS
  agr_service
  rospy
)

catkin_package(
  CATKIN_DEPENDS agr_service rospy
)

catkin_install_python(
  PROGRAMS scripts/status_server.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(
  DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
