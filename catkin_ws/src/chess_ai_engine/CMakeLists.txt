cmake_minimum_required(VERSION 3.0.2)
project(chess_ai_engine)

find_package(catkin REQUIRED COMPONENTS
        roscpp
        rospy
        std_msgs
)

catkin_package(
        CATKIN_DEPENDS roscpp rospy std_msgs
)

include_directories(
        ${catkin_INCLUDE_DIRS}
)

###################################
# BUILD (C++)
###################################

## 1. Компіляція C++ ноди vision_publisher
add_executable(vision_publisher_cpp_node src/vision_publisher.cpp)
target_link_libraries(vision_publisher_cpp_node
        ${catkin_LIBRARIES}
)

## 2. Додавання виконуваного файлу robot_controller (C++)
add_executable(robot_controller_node src/robot_controller_node.cpp)
target_link_libraries(robot_controller_node
        ${catkin_LIBRARIES}
)

###################################
# INSTALL (Python and C++)
###################################

## 1. Встановлення Python скриптів
install(PROGRAMS
        scripts/ai_node.py
        scripts/robot_controller_node.py
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## 2. Встановлення C++ виконуваних файлів
install(TARGETS vision_publisher_cpp_node
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(TARGETS robot_controller_node
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)