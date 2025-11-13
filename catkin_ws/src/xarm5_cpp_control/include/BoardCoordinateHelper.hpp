#ifndef BOARD_COORDINATE_HELPER_HPP
#define BOARD_COORDINATE_HELPER_HPP

#include <string>
#include <map>
#include <vector>
#include <cmath>
#include <geometry_msgs/Pose.h>
#include <geometry_msgs/Quaternion.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <ros/ros.h> // Додано для ROS_ERROR

/**
 * @brief Допоміжний клас для конвертації шахових клітинок у координати Gazebo.
 * Використовує константи, визначені у Gazebo launch-файлі.
 *
 * Базові координати (A1): X: -0.29931, Y: -0.21875
 * Розмір клітинки (Step): 0.0625 м
 */
class BoardCoordinateHelper {
public:
    // Ширина/довжина клітинки
    const double STEP_SIZE = 0.0625;
    // Центр клітинки A1 в декартових координатах (взяті з launch-файлу)
    const double A1_CENTER_X = -0.29931;
    const double A1_CENTER_Y = -0.21875;
    // Висота, на яку рука опускається для захвату/встановлення
    const double PICK_Z = 1.10;      // Висота над дошкою для захвату
    const double APPROACH_Z = 1.20;  // Висота для підльоту/відльоту (вище 10 см)

    /**
     * @brief Конвертує шахову клітинку (напр., "a1", "e4") у цільову позу (Pose)
     * для кінцевого ефектора.
     * @param square Шахова клітинка у форматі алгебраїчної нотації (напр., "e4").
     * @return geometry_msgs::Pose
     */
    geometry_msgs::Pose squareToPose(const std::string& square) const {
        geometry_msgs::Pose pose;

        // Перевірка коректності клітинки
        if (!isValidSquare(square)) {
            ROS_ERROR("Invalid square format: %s. Returning zero pose.", square.c_str());
            return pose;
        }

        char file_char = square[0]; // 'a' до 'h'
        char rank_char = square[1]; // '1' до '8'

        // Індекс файлу: 'a' -> 0, 'b' -> 1, ...
        int file_index = file_char - 'a';
        // Індекс рангу: '1' -> 0, '2' -> 1, ...
        int rank_int = rank_char - '1';

        // Розрахунок X (по горизонталі)
        pose.position.x = A1_CENTER_X + file_index * STEP_SIZE;

        // Розрахунок Y (по вертикалі)
        pose.position.y = A1_CENTER_Y + rank_int * STEP_SIZE;

        // Встановлюємо висоту для захвату
        pose.position.z = PICK_Z;

        // Встановлюємо фіксовану орієнтацію захвату
        pose.orientation = getFixedGripperOrientation();

        return pose;
    }

    /**
     * @brief Перевіряє, чи є рядок коректною шаховою клітинкою (напр., "a1" - "h8").
     * @param square Рядок клітинки.
     * @return true, якщо клітинка коректна.
     */
    bool isValidSquare(const std::string& square) const {
        if (square.length() != 2) {
            return false;
        }
        char file_char = square[0];
        char rank_char = square[1];

        // Файл має бути від 'a' до 'h'
        bool file_ok = (file_char >= 'a' && file_char <= 'h');
        // Ранг має бути від '1' до '8'
        bool rank_ok = (rank_char >= '1' && rank_char <= '8');

        return file_ok && rank_ok;
    }

    /**
     * @brief Повертає фіксовану орієнтацію (Quaternion) для вертикального захвату фігури.
     * @return geometry_msgs::Quaternion
     */
    geometry_msgs::Quaternion getFixedGripperOrientation() const {
        geometry_msgs::Quaternion orientation;

        tf2::Quaternion q;
        // Орієнтація: Робот дивиться вертикально вниз (Roll=0, Pitch=-90deg, Yaw=0)
        q.setRPY(0, -M_PI_2, 0);

        orientation = tf2::toMsg(q);
        return orientation;
    }

};

#endif // BOARD_COORDINATE_HELPER_HPP