#!/usr/bin/env python3
import rospy
import cv2
import time
import os
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

class ChessCameraSaver:
    def __init__(self):
        rospy.init_node('chess_photo_saver', anonymous=True)
        self.bridge = CvBridge()
        
        # Назва файлу (буде лежати поруч зі скриптом)
        self.filename = "chess_view.jpg"
        
        # Змінна для відліку часу
        self.last_save_time = 0
        self.interval = 10  # Інтервал у секундах

        # Підписка на камеру
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, self.image_callback)
        print(f"Запущено! Фото буде оновлюватись кожні {self.interval} с у файл '{self.filename}'")

    def image_callback(self, data):
        try:
            # Перевіряємо, чи пройшло 10 секунд
            current_time = time.time()
            if current_time - self.last_save_time >= self.interval:
                
                # Конвертуємо
                cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
                
                # Отримуємо повний шлях до папки, де лежить цей скрипт
                script_dir = os.path.dirname(os.path.realpath(__file__))
                file_path = os.path.join(script_dir, self.filename)
                
                # Зберігаємо (це автоматично видаляє старий файл і пише новий)
                cv2.imwrite(file_path, cv_image)
                
                print(f"[{time.strftime('%H:%M:%S')}] Фото оновлено: {file_path}")
                
                # Оновлюємо таймер
                self.last_save_time = current_time
            
        except CvBridgeError as e:
            print(f"Помилка: {e}")

if __name__ == '__main__':
    saver = ChessCameraSaver()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Роботу завершено")