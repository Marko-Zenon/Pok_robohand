import cv2
import os
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILE_RELATIVE = "../data/current_photo/board_start.jpg"
OUTPUT_FOLDER_RELATIVE = "../data/cells"

IMAGE_FILE = os.path.join(SCRIPT_DIR, IMAGE_FILE_RELATIVE)
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, OUTPUT_FOLDER_RELATIVE)

points = []

def click_event(event, x, y, flags, params):
    # Ловимо клік лівою кнопкою
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"✅ Клік {len(points)+1}/4: [{x}, {y}]")
        points.append([x, y])
        
        # Малюємо точку
        cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        cv2.imshow("Click Corners", img)

        # Коли наклікали 4 точки
        if len(points) == 4:
            print("\n" + "="*40)
            print("👇 КОПІЮЙ ЦЕ В СВІЙ КОД (split_board.py) 👇")
            print("="*40)
            print(f"src_points = np.float32({points})")
            print("="*40)
            print("Тепер натисни будь-яку клавішу, щоб вийти.")

img = cv2.imread(IMAGE_FILE)

if img is None:
    print(f"Помилка: Не бачу файл {IMAGE_FILE}. Перевір назву!")
else:
    print("--- ІНСТРУКЦІЯ ---")
    print("Клікай по черзі 4 ВНУТРІШНІ кути дошки:")
    print("1. Верхній-Лівий")
    print("2. Верхній-Правий")
    print("3. Нижній-Правий")
    print("4. Нижній-Лівій")
    
    cv2.imshow("Click Corners", img)
    
    # ОСЬ ЦЬОГО РЯДКА НЕ ВИСТАЧАЛО:
    cv2.setMouseCallback("Click Corners", click_event)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()