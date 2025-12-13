#!/usr/bin/env python3
import rospy
import cv2
import os
import sys
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from std_srvs.srv import Trigger, TriggerResponse

# --- ШЛЯХИ ---
# Додаємо поточну директорію, щоб бачити split_board.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Імпортуємо твій клас нарізки
try:
    from split_board import ChessSplitter
except ImportError:
    print("❌ Помилка: Не знайдено файл split_board.py в тій же папці!")
    sys.exit(1)

class ChessCameraReader:
    def __init__(self):
        rospy.init_node('chess_camera_reader', anonymous=True)
        self.bridge = CvBridge()
        
        # Налаштування папок
        self.board_path = os.path.normpath(os.path.join(current_dir, "../data/current_photo/board2.jpg"))
        self.cells_dir = os.path.normpath(os.path.join(current_dir, "../data/cells"))

        if not os.path.exists(os.path.dirname(self.board_path)):
            os.makedirs(os.path.dirname(self.board_path))

        # Ініціалізація сплітера
        self.splitter = ChessSplitter(self.cells_dir)
        
        self.latest_image = None

        # Підписка на камеру (тільки для читання потоку)
        rospy.Subscriber("/usb_cam/image_raw", Image, self.image_callback)
        
        # Створення СЕРВІСУ (чекає виклику від робота)
        self.service = rospy.Service('trigger_chess_capture', Trigger, self.handle_capture_request)
        
        print(f"✅ Camera Node запущено. Чекаю на хід робота...")

    def image_callback(self, data):
        """Просто оновлює останній кадр у пам'яті"""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except Exception as e:
            pass

    def handle_capture_request(self, req):
        """Викликається роботом, коли він закінчив хід"""
        if self.latest_image is None:
            return TriggerResponse(success=False, message="No image received yet")

        try:
            print("📸 Отримано сигнал! Обробка фото...")
            
            # 1. Ресайз
            cv_image = cv2.resize(self.latest_image, (640, 480))
            
            # 2. Збереження
            cv2.imwrite(self.board_path, cv_image)
            
            # 3. Нарізка
            self.splitter.process_image(cv_image)
            
            print("✅ Фото оновлено і нарізано.")
            return TriggerResponse(success=True, message="Success")
            
        except Exception as e:
            print(f"❌ Помилка обробки: {e}")
            return TriggerResponse(success=False, message=str(e))

if __name__ == '__main__':
    try:
        ChessCameraReader()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass