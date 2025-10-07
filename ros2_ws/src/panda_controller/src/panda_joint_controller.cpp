#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64.hpp"

int main(int argc, char **argv) {
    rclcpp::init(argc, argv);

    auto node = rclcpp::Node::make_shared("panda_joint_controller");

    // Publisher to control joint1
    auto pub = node->create_publisher<std_msgs::msg::Float64>(
        "/panda/joint1_position_controller/command", 10
    );

    rclcpp::WallRate loop_rate(1); // 1 Hz

    double angle = 0.0;
    while (rclcpp::ok()) {
        auto msg = std_msgs::msg::Float64();
        angle += 0.1;
        if (angle > 1.57) angle = 0.0;
        msg.data = angle;
        pub->publish(msg);
        RCLCPP_INFO(node->get_logger(), "Sent angle: %.2f", angle);
        rclcpp::spin_some(node);
        loop_rate.sleep();
    }

    rclcpp::shutdown();
    return 0;
}
