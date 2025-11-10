#include <ros/ros.h>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

int main(int argc, char** argv)
{
    ros::init(argc, argv, "xarm5_cpp_control");
    ros::NodeHandle nh;
    ros::AsyncSpinner spinner(1);
    spinner.start();

    moveit::planning_interface::MoveGroupInterface move_group("xarm5");

    // ДЕТАЛЬНА ДІАГНОСТИКА
    ROS_INFO("=== XARM5 DIAGNOSTICS ===");
    ROS_INFO("Planning frame: %s", move_group.getPlanningFrame().c_str());
    ROS_INFO("End effector link: %s", move_group.getEndEffectorLink().c_str());

    // Поточна поза
    geometry_msgs::PoseStamped current_pose = move_group.getCurrentPose();
    ROS_INFO("Current end effector pose:");
    ROS_INFO("  Position: x=%.3f, y=%.3f, z=%.3f",
             current_pose.pose.position.x,
             current_pose.pose.position.y,
             current_pose.pose.position.z);
    ROS_INFO("  Orientation: w=%.3f", current_pose.pose.orientation.w);

    // Поточні значення з'єднань
    std::vector<double> joint_values = move_group.getCurrentJointValues();
    ROS_INFO("Current joint values:");
    for(size_t i = 0; i < joint_values.size(); ++i) {
        ROS_INFO("  Joint %zu: %.3f rad", i+1, joint_values[i]);
    }

    // Налаштування планування
    move_group.setPlanningTime(15.0);
    move_group.setNumPlanningAttempts(10);
    move_group.allowReplanning(true);

    // СПОЧАТКУ спробуємо простий рух у з'єднаннях
    ROS_INFO("=== TEST 1: Simple joint space movement ===");
    std::vector<double> target_joints = joint_values;
    if(target_joints.size() >= 5) {
        target_joints[0] += 0.2;  // Трохи змінити перше з'єднання
        move_group.setJointValueTarget(target_joints);

        moveit::planning_interface::MoveGroupInterface::Plan joint_plan;
        if(move_group.plan(joint_plan) == moveit::planning_interface::MoveItErrorCode::SUCCESS) {
            ROS_INFO("Joint space planning SUCCESS!");
            move_group.move();
        } else {
            ROS_WARN("Joint space planning failed");
        }
    }

    // ТЕПЕР спробуємо простішу декартову ціль
    ROS_INFO("=== TEST 2: Simple Cartesian movement ===");
    geometry_msgs::Pose target_pose = current_pose.pose;
    target_pose.position.z += 0.1;  // Просто підняти руку

    move_group.setPoseTarget(target_pose);

    moveit::planning_interface::MoveGroupInterface::Plan cartesian_plan;
    if(move_group.plan(cartesian_plan) == moveit::planning_interface::MoveItErrorCode::SUCCESS) {
        ROS_INFO("Cartesian planning SUCCESS!");
        move_group.move();
    } else {
        ROS_WARN("Cartesian planning failed");

        // Остання спроба - зовсім проста ціль
        ROS_INFO("=== TEST 3: Minimal movement ===");
        target_pose.position.z += 0.05;  // Дуже маленький рух
        move_group.setPoseTarget(target_pose);

        if(move_group.plan(cartesian_plan) == moveit::planning_interface::MoveItErrorCode::SUCCESS) {
            ROS_INFO("Minimal movement planning SUCCESS!");
            move_group.move();
        } else {
            ROS_ERROR("All planning attempts failed");
        }
    }

    ros::shutdown();
    return 0;
}