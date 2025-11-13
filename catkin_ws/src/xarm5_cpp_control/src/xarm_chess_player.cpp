#include <ros/ros.h>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit_visual_tools/moveit_visual_tools.h>
#include <geometry_msgs/Pose.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <vector>
#include <string>
#include <algorithm>
#include <thread>
#include <chrono>

// Включаємо класи-хелпери
#include "BoardCoordinateHelper.hpp"
#include "ChessVision.hpp"

// Назва групи для MoveIt
const std::string PLANNING_GROUP = "xarm5";

/**
 * @brief Головний клас для управління роботом xArm5 та гри в шахи.
 */
class XArmChessPlayer {
private:
    ros::NodeHandle nh_;
    moveit::planning_interface::MoveGroupInterface move_group_;
    moveit::planning_interface::PlanningSceneInterface planning_scene_interface_;
    BoardCoordinateHelper coord_helper_;
    ChessVision vision_helper_;

    // Параметри захвату
    const std::string EE_LINK = "link_eef";
    const std::string GRIPPER_GROUP = "xarm_gripper";
    const std::string GRIPPER_JOINT = "drive_joint";

    /**
     * @brief Виводить доступні іменовані позиції
     */
    void printAvailableNamedPoses() {
        std::vector<std::string> named_targets = move_group_.getNamedTargets();
        ROS_INFO("Available named poses:");
        if (named_targets.empty()) {
            ROS_INFO("  - No named poses found");
        } else {
            for (const auto& target : named_targets) {
                ROS_INFO("  - %s", target.c_str());
            }
        }
    }

    /**
     * @brief Імітує відкриття/закриття захвату.
     */
    bool setGripper(bool close) {
        moveit::planning_interface::MoveGroupInterface gripper_group(GRIPPER_GROUP);

        if (gripper_group.getCurrentJointValues().empty()) {
            ROS_WARN("Gripper group '%s' not found. Simulating gripper action.", GRIPPER_GROUP.c_str());
            // Імітуємо успіх для тестування
            ROS_INFO("Simulating gripper %s", close ? "CLOSE" : "OPEN");
            return true;
        }

        double target_position = close ? 0.8 : 0.0;
        gripper_group.setJointValueTarget(GRIPPER_JOINT, target_position);

        moveit::planning_interface::MoveGroupInterface::Plan gripper_plan;
        bool success = (gripper_group.plan(gripper_plan) == moveit::core::MoveItErrorCode::SUCCESS);

        if (success) {
            ROS_INFO("%s gripper plan successful. Executing...", close ? "Closing" : "Opening");
            return gripper_group.execute(gripper_plan) == moveit::core::MoveItErrorCode::SUCCESS;
        }
        ROS_ERROR("%s gripper failed to plan.", close ? "Closing" : "Opening");
        return false;
    }

    /**
     * @brief Виконує планування та рух до цільової позиції.
     */
    bool executePlan(const geometry_msgs::Pose& target_pose) {
        move_group_.setPoseTarget(target_pose);

        moveit::planning_interface::MoveGroupInterface::Plan my_plan;
        move_group_.setNumPlanningAttempts(10);
        move_group_.setPlanningTime(15.0);

        bool success = (move_group_.plan(my_plan) == moveit::core::MoveItErrorCode::SUCCESS);

        if (success) {
            ROS_INFO("Plan successful. Executing...");
            return move_group_.execute(my_plan) == moveit::core::MoveItErrorCode::SUCCESS;
        } else {
            ROS_WARN("Planning failed for the target pose. Timed out or No IK solution.");
            return false;
        }
    }

    /**
     * @brief Рухає робот до іменованої позиції
     */
    bool setNamedPose(const std::string& pose_name) {
        auto named_targets = move_group_.getNamedTargets();
        if (std::find(named_targets.begin(), named_targets.end(), pose_name) == named_targets.end()) {
            ROS_WARN("Named pose '%s' not found.", pose_name.c_str());
            return false;
        }

        move_group_.setNamedTarget(pose_name);

        moveit::planning_interface::MoveGroupInterface::Plan my_plan;
        bool success = (move_group_.plan(my_plan) == moveit::core::MoveItErrorCode::SUCCESS);

        if (success) {
            ROS_INFO("Moving to named pose '%s'...", pose_name.c_str());
            return move_group_.move() == moveit::core::MoveItErrorCode::SUCCESS;
        } else {
            ROS_ERROR("Failed to plan to named pose '%s'.", pose_name.c_str());
            return false;
        }
    }

    /**
     * @brief Очікує хід гравця (чорних фігур)
     */
    void waitForPlayerMove() {
        ROS_INFO("=== YOUR TURN (BLACK) ===");
        ROS_INFO("Make your move with black pieces...");
        ROS_INFO("Press ENTER in this terminal when you finish your move");

        std::string input;
        std::getline(std::cin, input);

        ROS_INFO("Player move completed. Processing...");
        std::this_thread::sleep_for(std::chrono::seconds(2)); // Даємо час на стабілізацію
    }

public:
    XArmChessPlayer() :
        nh_("~"),
        move_group_(PLANNING_GROUP),
        vision_helper_(nh_)
    {
        ROS_INFO("Initializing XArm Chess Player...");

        // Виведення доступних поз
        printAvailableNamedPoses();

        // --- НАЛАШТУВАННЯ MOVEIT ---
        move_group_.setPlanningTime(20.0);
        move_group_.setEndEffectorLink(EE_LINK);

        // Перевірка групи планування
        if (std::find(move_group_.getJointModelGroupNames().begin(),
                      move_group_.getJointModelGroupNames().end(),
                      PLANNING_GROUP) == move_group_.getJointModelGroupNames().end()) {
            ROS_FATAL("Planning Group '%s' not found. Check your SRDF.", PLANNING_GROUP.c_str());
            return;
        }

        ROS_INFO("MoveIt initialized. Planning time set to 20.0s.");

        // Спробуємо знайти будь-яку безпечну позу
        std::vector<std::string> possible_start_poses = {"home", "ready", "standby", "upright"};
        bool start_pose_found = false;

        for (const auto& pose_name : possible_start_poses) {
            auto named_targets = move_group_.getNamedTargets();
            if (std::find(named_targets.begin(), named_targets.end(), pose_name) != named_targets.end()) {
                ROS_INFO("Found named pose '%s'. Moving to it...", pose_name.c_str());
                if (setNamedPose(pose_name)) {
                    start_pose_found = true;
                    break;
                }
            }
        }

        if (!start_pose_found) {
            ROS_WARN("No suitable named pose found. Robot will stay in current position.");
        }

        // --- ОЧІКУВАННЯ КАЛІБРУВАННЯ ЗОРУ ---
        int calibration_attempts = 0;
        const int max_calibration_attempts = 100; // 10 секунд

        while(ros::ok() && !vision_helper_.isCalibrated() && calibration_attempts < max_calibration_attempts) {
            ROS_INFO_THROTTLE(2, "Waiting for camera image and vision calibration... (%d/%d)",
                             calibration_attempts, max_calibration_attempts);
            ros::spinOnce();
            ros::Duration(0.1).sleep();
            calibration_attempts++;
        }

        if (vision_helper_.isCalibrated()) {
            ROS_INFO("Vision calibrated! Player node ready.");
        } else {
            ROS_WARN("Vision calibration failed after %d attempts. Continuing with limited functionality.",
                    max_calibration_attempts);
        }
    }

    /**
     * @brief Виконує повний шаховий хід
     */
    bool performMove(const std::string& from_square, const std::string& to_square) {
        ROS_INFO("🤖 ROBOT MOVE: %s to %s", from_square.c_str(), to_square.c_str());

        // 1. Перевірка коректності клітинок
        if (!coord_helper_.isValidSquare(from_square) || !coord_helper_.isValidSquare(to_square)) {
            ROS_ERROR("Invalid square name provided.");
            return false;
        }

        // --- Визначення ключових поз ---
        geometry_msgs::Pose pickup_pose = coord_helper_.squareToPose(from_square);
        geometry_msgs::Pose approach_pose = pickup_pose;
        approach_pose.position.z = coord_helper_.APPROACH_Z;

        geometry_msgs::Pose dropoff_pose = coord_helper_.squareToPose(to_square);
        geometry_msgs::Pose retract_pose = dropoff_pose;
        retract_pose.position.z = coord_helper_.APPROACH_Z;

        // --- ЕТАПИ ХОДУ ---
        ROS_INFO("1. Moving to approach position...");
        if (!executePlan(approach_pose)) return false;

        ROS_INFO("2. Moving to pickup position...");
        if (!executePlan(pickup_pose)) return false;

        ROS_INFO("3. Closing gripper...");
        if (!setGripper(true)) return false;
        ros::Duration(0.5).sleep();

        ROS_INFO("4. Moving back to approach position...");
        if (!executePlan(approach_pose)) return false;

        ROS_INFO("5. Moving to dropoff approach position...");
        if (!executePlan(retract_pose)) return false;

        ROS_INFO("6. Moving to dropoff position...");
        if (!executePlan(dropoff_pose)) return false;

        ROS_INFO("7. Opening gripper...");
        if (!setGripper(false)) return false;
        ros::Duration(0.5).sleep();

        ROS_INFO("8. Moving back to retract position...");
        if (!executePlan(retract_pose)) return false;

        ROS_INFO("9. Returning to safe position...");
        // Спробуємо повернутися до будь-якої безпечної позиції
        std::vector<std::string> safe_poses = {"home", "ready", "standby"};
        for (const auto& pose_name : safe_poses) {
            auto named_targets = move_group_.getNamedTargets();
            if (std::find(named_targets.begin(), named_targets.end(), pose_name) != named_targets.end()) {
                if (setNamedPose(pose_name)) {
                    return true;
                }
            }
        }

        ROS_WARN("No safe pose found. Staying in current position.");
        return true;
    }

    /**
     * @brief Виводить поточний стан дошки
     */
    void printBoardState() {
        auto current_board = vision_helper_.getCurrentBoardState();

        ROS_INFO("--- Current Board State ---");
        for (int rank = 7; rank >= 0; --rank) {
            std::string row_output = std::to_string(rank + 1) + " | ";
            for (int file = 0; file < 8; ++file) {
                switch (current_board[file][rank]) {
                    case PieceType::WHITE: row_output += "W "; break;
                    case PieceType::BLACK: row_output += "B "; break;
                    case PieceType::EMPTY: row_output += ". "; break;
                    case PieceType::UNKNOWN:
                    default: row_output += "? "; break;
                }
            }
            ROS_INFO("%s", row_output.c_str());
        }
        ROS_INFO("    -----------------");
        ROS_INFO("      a b c d e f g h");
    }

    /**
     * @brief Головний цикл гри
     */
    void runGame() {
        if (!ros::ok()) return;

        ROS_INFO("🎮 === CHESS GAME STARTED ===");
        ROS_INFO("🤖 Robot plays WHITE pieces");
        ROS_INFO("👤 You play BLACK pieces");

        int move_count = 0;

        while (ros::ok() && move_count < 10) { // Обмежимо кількість ходів для тесту
            ROS_INFO("\n=== MOVE %d ===", move_count + 1);

            // 1. Хід робота (білі)
            ROS_INFO("🤖 ROBOT'S TURN (WHITE)");
            printBoardState();

            auto robot_move = vision_helper_.getRandomWhiteMove();
            if (robot_move.first.empty() || robot_move.second.empty()) {
                ROS_ERROR("No valid moves for white pieces. Game over?");
                break;
            }

            if (performMove(robot_move.first, robot_move.second)) {
                ROS_INFO("✅ Robot move completed: %s to %s",
                        robot_move.first.c_str(), robot_move.second.c_str());
            } else {
                ROS_ERROR("❌ Robot move failed!");
                break;
            }

            move_count++;
            if (move_count >= 10) break;

            // 2. Очікуємо хід гравця (чорні)
            waitForPlayerMove();

            // 3. Перевіряємо новий стан дошки після ходу гравця
            ROS_INFO("Updating board state after player move...");
            printBoardState();
        }

        ROS_INFO("🎯 === GAME FINISHED ===");
        ROS_INFO("Total moves made: %d", move_count);
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "xarm_chess_player_node");
    ros::AsyncSpinner spinner(1);
    spinner.start();

    try {
        XArmChessPlayer player;
        player.runGame();
    } catch (const std::exception& e) {
        ROS_ERROR("Exception in main: %s", e.what());
    }

    ros::waitForShutdown();
    return 0;
}