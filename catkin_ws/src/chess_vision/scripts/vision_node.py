#!/usr/bin/env python3
import rospy
import cv2
import os
import sys
import time
import numpy as np
import chess
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from split_board import ChessSplitter

class ChessBlueDetector:
    def __init__(self):
        rospy.init_node('chess_vision_blue', anonymous=True)
        self.bridge = CvBridge()
        
        # Внутрішня логіка шахів
        self.board = chess.Board()
        

        # Публікуємо FEN, бо твій AI чекає саме його
        self.fen_pub = rospy.Publisher('/chess_state/fen', String, queue_size=10, latch=True)

        # Налаштування шляхів
        self.board_path = os.path.normpath(os.path.join(current_dir, "../data/current_photo/board2.jpg"))
        self.cells_dir = os.path.normpath(os.path.join(current_dir, "../data/cells"))
        self.splitter = ChessSplitter(self.cells_dir)

        # Стан (сині маркери)
        self.previous_state = {}
        
        self.last_process_time = 0
        self.interval = 10.0 # Час між перевірками (щоб встигнути забрати руки)

        rospy.Subscriber("/usb_cam/image_raw", Image, self.callback)
        
        # Відправляємо початковий стан
        self.fen_pub.publish(self.board.fen())
        
        print("VISION: Запущено. Шукаю сині маркери.")
        print(f"Публікую FEN у /chess_state/fen")

    def is_blue_present(self, image):
        if image is None: return False
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # Налаштування синього
        mask = cv2.inRange(hsv, np.array([90, 80, 50]), np.array([130, 255, 255]))
        return cv2.countNonZero(mask) > 50

    def detect_move(self, current_state):
        if not self.previous_state: return None

        vanished = []
        appeared = []
        
        for sq, is_occupied in current_state.items():
            prev = self.previous_state.get(sq, False)
            if prev and not is_occupied: vanished.append(sq)
            elif not prev and is_occupied: appeared.append(sq)

        if not vanished and not appeared: return None

        print(f"Зміни: Пішло з {vanished}, Прийшло на {appeared}")

        # Шукаємо легальний хід, який пояснює ці зміни
        for move in self.board.legal_moves:
            uci = move.uci()
            src, dst = uci[:2], uci[2:4]

            # Звичайний хід або взяття
            if src in vanished and (dst in appeared or (self.board.is_capture(move) and current_state.get(dst))):
                return move
        return None

    def callback(self, data):
        if time.time() - self.last_process_time < self.interval: return

        try:
            # Обробка фото
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
            cv_image = cv2.resize(cv_image, (640, 480)) # РЕСАЙЗ ОБОВ'ЯЗКОВИЙ
            self.splitter.process_image(cv_image)

            # Сканування клітинок
            current_state = {}
            files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

            for f in files:
                for r in ranks:
                    sq = f"{f}{r}"
                    img = cv2.imread(os.path.join(self.cells_dir, f"{sq}.jpg"))
                    current_state[sq] = self.is_blue_present(img)

            if not self.previous_state:
                self.previous_state = current_state
                self.last_process_time = time.time()
                return

            # Спроба знайти хід
            move = self.detect_move(current_state)

            if move:
                print(f"ХІД ЛЮДИНИ: {move.uci()}")
                self.board.push(move) # Оновлюємо внутрішню логіку
                
                # ВІДПРАВЛЯЄМО FEN ДЛЯ ТВОГО AI
                fen_str = self.board.fen()
                self.fen_pub.publish(fen_str)
                print(f"Відправлено FEN: {fen_str}")
                
                self.previous_state = current_state
            
            self.last_process_time = time.time()

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    try:
        ChessBlueDetector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass