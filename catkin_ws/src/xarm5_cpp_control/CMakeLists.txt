cmake_minimum_required(VERSION 3.0.2)
project(xarm5_cpp_control)

# Тільки необхідні компоненти
find_package(catkin REQUIRED COMPONENTS
        roscpp
        std_msgs
        geometry_msgs
        sensor_msgs
        moveit_core
        moveit_ros_planning_interface
        moveit_ros_move_group
        moveit_visual_tools
        tf2_geometry_msgs
        image_transport
        cv_bridge
)

find_package(OpenCV REQUIRED)

catkin_package()

include_directories(
        include
        ${catkin_INCLUDE_DIRS}
        ${OpenCV_INCLUDE_DIRS}
)

add_executable(xarm_chess_player src/xarm_chess_player.cpp)

target_link_libraries(xarm_chess_player
        ${catkin_LIBRARIES}
        ${OpenCV_LIBRARIES}
)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)