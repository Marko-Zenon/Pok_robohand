cmake_minimum_required(VERSION 3.5)
project(panda_controller)

# Find required packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Add your executable
add_executable(panda_joint_controller src/panda_joint_controller.cpp)
ament_target_dependencies(panda_joint_controller rclcpp std_msgs)

# Install executable
install(TARGETS
  panda_joint_controller
  DESTINATION lib/${PROJECT_NAME})

ament_package()

