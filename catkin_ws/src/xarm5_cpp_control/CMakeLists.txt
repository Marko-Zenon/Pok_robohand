cmake_minimum_required(VERSION 3.0.2)
project(xarm5_cpp_control)

find_package(catkin REQUIRED COMPONENTS
        roscpp
        moveit_ros_planning_interface
        moveit_core
        moveit_visual_tools
        geometry_msgs
)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS})

add_executable(xarm5_move src/xarm5_move.cpp)
target_link_libraries(xarm5_move ${catkin_LIBRARIES})
