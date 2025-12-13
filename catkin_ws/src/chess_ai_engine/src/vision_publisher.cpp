#include "ros/ros.h"
#include "std_msgs/String.h"
#include <sstream>
#include <string>
#include <vector>

void publish_fen(ros::Publisher& pub, const std::string& fen) {
    std_msgs::String msg;
    msg.data = fen;
    pub.publish(msg);
    ROS_INFO("PUBLISHING FEN: %s", msg.data.c_str());
}

int main(int argc, char **argv)
{
    // 1. Initialization
    ros::init(argc, argv, "vision_publisher_cpp_node");
    ros::NodeHandle nh;

    // 2. Create publisher on /chess_state/fen (ВИПРАВЛЕНО, ЩОБ ВІДПОВІДАВ AI NODE)
    ros::Publisher fen_pub = nh.advertise<std_msgs::String>("/chess_state/fen", 10);

    // Test FEN strings to simulate moves
    std::vector<std::string> fen_list = {
        // 1. Start of game (White to move)
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        // 2. After White's E4 (Black to move)
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
        // 3. After Black's C5 (White to move)
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
    };

    // --- FIX FREQUENCY: 5 SECONDS (0.2 Hz) ---
    double desired_rate = 0.2; // Frequency (Hz) = 1 / 5 seconds
    ros::Rate loop_rate(desired_rate);
    int step = 0;

    ROS_INFO("--- C++ VISION SIMULATOR STARTING ---");
    ROS_INFO("It will publish the next FEN every 5.0 seconds (0.2 Hz).");

    while (ros::ok())
    {
        // Cycle through FEN list
        std::string current_fen = fen_list[step % fen_list.size()];

        publish_fen(fen_pub, current_fen);

        step++;

        ros::spinOnce();
        loop_rate.sleep();
    }

    return 0;
}