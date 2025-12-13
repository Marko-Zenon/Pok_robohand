#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
from xarm.wrapper import XArmAPI
import time
import sys

class RobotMover:
    def __init__(self):
        rospy.init_node('robot_mover_node', anonymous=True)
        
        # 1. Підключення до робота (з твого test.py)
        ip = '192.168.1.242'
        self.arm = XArmAPI(ip)
        self.arm.motion_enable(True)
        self.arm.set_mode(0)
        self.arm.set_state(0)
        time.sleep(1)
        
        print(f"Robot Connected: {ip}")

        # 2. Твої координати (HARDCODED POSITIONS)
        self.BOARD_POSITIONS = {
            "a1": [-16.2, 87.3, -137, 51.7, 0],
            "b1": [-11.2, 86.7, -135.3, 52.8, 0],
            "c1": [-6.3, 79.6, -120.5, 42.6, 0],
            "d1": [-1.5, 79.5, -120.5, 42.6, 0],
            "e1": [3.6, 81.2, -124.1, 45.8, 0],
            "f1": [8.3, 83.1, -128.5, 49.9, 0],
            "g1": [13.2, 84.7, -130.6, 48.9, 0],
            "h1": [17.8, 90.3, -141.6, 53.6, 0],

            "a2": [-17.4, 73, -109.1, 39.8, 0],
            "b2": [-12.3, 72.2, -107.6, 41.4, 0],
            "c2": [-7.2, 71.6, -106.5, 41.4, 0],
            "d2": [-1.7, 71.2, -105.1, 41.4, 0],
            "e2": [3.5, 73.2, -109.5, 44.6, 0],
            "f2": [8.8, 73.2, -109.5, 44.6, 0],
            "g2": [13.9, 74.7, -112.3, 44.6, 0],
            "h2": [19, 77.3, -117.8, 46, 0],

            "a3": [-19.4, 63.8, -88.2, 26.4, 0],
            "b3": [-14.5, 62.7, -85.9, 26.8, 0],
            "c3": [-9, 62.2, -85, 28.3, 0],
            "d3": [-3.2, 60.8, -80.9, 23, 0],
            "e3": [2.9, 62.3, -85.5, 29.5, 0],
            "f3": [9.2, 61.8, -83.1, 24.7, 0],
            "g3": [15.2, 64.4, -89.9, 30.6, 0],
            "h3": [19.7, 63.2, -84.2, 18.6, 0],

            "a4": [-21.6, 57.8, -74.2, 18.6, 0],
            "b4": [16, 55.5, -65.4, 7.8, 0],
            "c4": [-10, 54.7, -63.6, 7.8, 0],
            "d4": [-3.4, 54.8, -65.5, 12.6, 0],
            "e4": [3.5, 55, -65.7, 12.6, 0],
            "f4": [10.1, 55.8, -67.4, 12.6, 0],
            "g4": [16.8, 57, -71.3, 16.5, 0],
            "h4": [22.3, 60.6, -81, 27.1, 0],

            "a5": [-24.6, 53.2, -61.9, 11.6, 0],
            "b5": [-17.9, 52.2, -59.2, 11.6, 0],
            "c5": [-10.6, 51.4, -56.2, 8.3, 0],
            "d5": [-3.4, 51.4, -55.8, 8.3, 0],
            "e5": [3.9, 51.5, -55.7, 8.3, 0],
            "f5": [11.5, 52.2, -55.4, 5.1, 0],
            "g5": [18.4, 53.2, -60.4, 11.4, 0],
            "h5": [24.8, 54.4, -64, 12.6, 0],

            "a6": [-28.1, 49.8, -50.4, 2.6, 0],
            "b6": [-20.5, 48.9, -47.7, 2.6, 0],
            "c6": [-12.8, 48.4, -46, 2.6, 0],
            "d6": [-3.8, 48.4, -45.5, 2.6, 0],
            "e6": [4.7, 48.8, -47.6, 6, 0],
            "f6": [12.9, 49.4, -47.9, 3.6, 0],
            "g6": [21, 50.8, -54.1, 11.6, 0],
            "h6": [28, 51.7, -57, 11.6, 0],

            "a7": [-32, 47.9, -45.4, 3.8, 0],
            "b7": [-23.5, 47.3, -42.8, 3.7, 0],
            "c7": [-14.8, 46.8, -40.7, 3.8, 0],
            "d7": [-5.1, 46.8, -39.8, 3.8, 0],
            "e7": [5.7, 47.4, -37.4, -2.8, 0],
            "f7": [14.8, 47.5, -38.3, -2.8, 0],
            "g7": [24.2, 48.2, -40.9, -2.8, 0],
            "h7": [32.9, 48.9, -45.9, 1.5, 0],

            "a8": [-37, 47.3, -34.9, -9.2, 0],
            "b8": [-28.3, 46.9, -31.9, -9.2, 0],
            "c8": [-17.4, 47, -30.3, -9.2, 0],
            "d8": [-5.4, 46.8, -29.5, -9.2, 0],
            "e8": [6.5, 46.6, -31.8, -4.2, 0],
            "f8": [17.9, 46.8, -33.2, -4.2, 0],
            "g8": [29.2, 48.2, -32.3, -12.4, 0],
            "h8": [36.8, 47.6, -42.2, 3.8, 0],
        }
        
        # Безпечна позиція (над дошкою)
        self.SAFE_POS = [0.1, -17.7, -64, 83.1, 0]

        # 3. Підписка на топік AI
        rospy.Subscriber("/ai_move", String, self.move_callback)
        print("Waiting for commands on topic /ai_move ...")

    def move_callback(self, msg):
        move_str = msg.data
        print(f"Received move command: {move_str}")
        self.execute_physical_move(move_str)

    def execute_physical_move(self, move: str):
        # Перевірка формату (наприклад, "e2e4")
        if len(move) < 4: 
            print("Invalid move format")
            return
            
        start = move[:2]
        end = move[2:]
        
        if start not in self.BOARD_POSITIONS or end not in self.BOARD_POSITIONS:
            print(f"Unknown coordinates: {start} -> {end}")
            return

        print(f"🔧 Executing move: {start} -> {end}")

        
        # 1. Відкрити грипер, піднятися
        self.arm.set_gripper_position(500, wait=True)
        # self.arm.set_servo_angle(angle=self.SAFE_POS, speed=20, wait=True, is_radian=False)

        # 2. Піти на СТАРТ
        print(f"Going to {start}...")
        self.arm.set_servo_angle(angle=self.BOARD_POSITIONS[start], speed=20, wait=True, is_radian=False)
        time.sleep(0.4)

        # 3. Взяти фігуру
        self.arm.set_gripper_position(160, wait=True)
        time.sleep(1) # Дати час на захват

        # 4. Підняти (в безпечну)
        self.arm.set_servo_angle(angle=self.SAFE_POS, speed=20, wait=True, is_radian=False)
        time.sleep(0.4)

        # 5. Піти на ФІНІШ
        print(f"Going to {end}...")
        self.arm.set_servo_angle(angle=self.BOARD_POSITIONS[end], speed=20, wait=True, is_radian=False)
        time.sleep(0.4)

        # 6. Відпустити
        self.arm.set_gripper_position(500, wait=True)
        time.sleep(1)

        # 7. Повернутись додому (безпечна позиція)
        self.arm.set_servo_angle(angle=self.SAFE_POS, speed=20, wait=True, is_radian=False)
        
        print("Move complete!")

    def shutdown(self):
        self.arm.disconnect()

if __name__ == '__main__':
    try:
        mover = RobotMover()
        rospy.spin()
    except rospy.ROSInterruptException:
        mover.shutdown()
