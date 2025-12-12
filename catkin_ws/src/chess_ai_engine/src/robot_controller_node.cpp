#include <iostream>
#include <string>
#include <cmath>

struct Pose {
    double x;
    double y;
    double z;
};

struct JointAngles {
    double joint1, joint2, joint3, joint4, joint5, joint6;
};


const double BOARD_HEIGHT = 0.03;  // 3 cm
const double SQUARE_SIZE_M = 0.05; // 5 см
const double X_A1_CENTER = -0.21875;
const double Y_A1_CENTER = -0.21875;

// Верхня позиція над полем
const Pose UPPER_POSE = {0.0, 0.0, 0.15}; // 150 мм

// Імітація IK
JointAngles inverse_kinematics(const Pose& p, double roll, double pitch, double yaw) {
    JointAngles angles;
    angles.joint1 = atan2(p.y, p.x);
    angles.joint2 = atan2(p.z, sqrt(p.x*p.x + p.y*p.y));
    angles.joint3 = 0.5; // приклад
    angles.joint4 = roll;
    angles.joint5 = pitch;
    angles.joint6 = yaw;
    return angles;
}

void print_joint_angles(const std::string& name, const JointAngles& angles) {
    std::cout << name << " angles: ["
              << angles.joint1 << ", "
              << angles.joint2 << ", "
              << angles.joint3 << ", "
              << angles.joint4 << ", "
              << angles.joint5 << ", "
              << angles.joint6 << "]" << std::endl;
}

// Перетворення UCI клітинки в координати
Pose uci_to_coords(const std::string& square) {
    char col_char = square[0];
    char row_char = square[1];
    int col_index = col_char - 'a';
    int row_index = row_char - '1';
    double x = X_A1_CENTER + col_index * SQUARE_SIZE_M;
    double y = Y_A1_CENTER + row_index * SQUARE_SIZE_M;
    double z = BOARD_HEIGHT + 0.001; // висота захоплення
    return {x, y, z};
}

// Симуляція ходу
void simulate_move(const std::string& uci_move) {
    if (uci_move.length() != 4) {
        std::cerr << "UCI move format incorrect!" << std::endl;
        return;
    }

    Pose start_pose = uci_to_coords(uci_move.substr(0,2));
    Pose end_pose = uci_to_coords(uci_move.substr(2,2));

    double roll = 0.0;
    double pitch = 1.57; // 90 градусів
    double yaw = 0.0;

    // 1. Верхня позиція (початкова)
    print_joint_angles("Upper start", inverse_kinematics(UPPER_POSE, roll, pitch, yaw));

    // 2. Опуститися до стартової клітинки
    print_joint_angles("Start square", inverse_kinematics(start_pose, roll, pitch, yaw));

    // 3. Підняти назад
    print_joint_angles("Upper after pickup", inverse_kinematics(UPPER_POSE, roll, pitch, yaw));

    // 4. Перемістити до кінцевої клітинки
    print_joint_angles("End square", inverse_kinematics(end_pose, roll, pitch, yaw));

    // 5. Підняти після ходу
    print_joint_angles("Upper after drop", inverse_kinematics(UPPER_POSE, roll, pitch, yaw));
}

int main() {
    std::string move;
    std::cout << "Enter UCI move (e.g. e2e4): ";
    std::cin >> move;

    simulate_move(move);
    return 0;
}
