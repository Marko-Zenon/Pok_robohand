#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from chess_ai import ChessAI

ai_engine = None
pub_move = None

def process_fen(fen_msg):
    """Gets FEN, checks the turn, calculates the move for Black, and publishes it."""
    fen = fen_msg.data
    rospy.loginfo(f"Received FEN: {fen}")

    try:
        active_color = fen.split(' ')[1]
    except IndexError:
        rospy.logerr("Invalid FEN format received. Cannot determine active color.")
        return

    if active_color == 'w':
        rospy.loginfo("It is White's turn. AI is set to play as Black. Skipping move calculation.")
        return


    if not ai_engine.set_position(fen):
        rospy.logerr("Invalid FEN. Move not calculated.")
        return

    rospy.loginfo("It is Black's turn. Calculating move...")
    best_move = ai_engine.get_best_move(time_limit=0.1) # 0.1 second for calcualting robots move

    if best_move:
        rospy.loginfo(f"Calculated move: {best_move}")
        pub_move.publish(best_move)
    else:
        rospy.logwarn("Stockfish did not find a move or an error occurred.")


def ai_node_main():
    global ai_engine, pub_move

    # Node Initialization
    rospy.init_node('chess_ai_node', anonymous=False)

    # AI Engine Initialization
    ai_engine = ChessAI(stockfish_path="/usr/games/stockfish")

    rospy.loginfo("Connecting to Stockfish...")
    if not ai_engine.connect_engine():
        rospy.logfatal("Cannot connect to Stockfish. Exiting.")
        return

    # Publisher Initialization
    pub_move = rospy.Publisher('/ai_move', String, queue_size=10)

    rospy.loginfo("AI Node Ready. Set to play as Black ('b').")
    rospy.loginfo("Waiting for FEN from vision node on topic /chess_state/fen")

    # Subscribe to FEN topic
    rospy.Subscriber('/chess_state/fen', String, process_fen)

    # Keep the node active
    rospy.spin()

    # Quit engine on exit
    ai_engine.quit_engine()

if __name__ == '__main__':
    try:
        ai_node_main()
    except rospy.ROSInterruptException:
        pass
