cmake_minimum_required(VERSION 3.0.2)
project(chess_vision)

find_package(catkin REQUIRED COMPONENTS
        cv_bridge
        rospy
        sensor_msgs
        std_msgs
)

catkin_package(
        CATKIN_DEPENDS cv_bridge rospy sensor_msgs std_msgs
)

include_directories(
        ${catkin_INCLUDE_DIRS}
)


install(PROGRAMS
        scripts/vision_node.py
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
