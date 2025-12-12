import cv2
import numpy as np
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILE_RELATIVE = "../data/current_photo/board.jpg"
OUTPUT_FOLDER_RELATIVE = "../data/cells"

IMAGE_FILE = os.path.join(SCRIPT_DIR, IMAGE_FILE_RELATIVE)
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, OUTPUT_FOLDER_RELATIVE)


# КУТ: Ставимо 0.0, бо координати вже досить точні
ROTATION_ANGLE = 0.0


# Це трохи "внутрішні" точки, щоб дерево точно не попало в кадр
src_points = np.float32([[114, 39], [515, 27], [526, 444], [114, 444]])


def rotate_image(image, angle):
    if angle == 0.0: return image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

def draw_grid(image):
    h, w = image.shape[:2]
    step_x = w // 8
    step_y = h // 8
    color = (0, 0, 255)
    for i in range(1, 8):
        cv2.line(image, (i * step_x, 0), (i * step_x, h), color, 2)
        cv2.line(image, (0, i * step_y), (w, i * step_y), color, 2)
    return image

def process():
    img = cv2.imread(IMAGE_FILE)
    if img is None:
        print(f"Помилка: Немає файлу {IMAGE_FILE}")
        return

    side = 640 
    dst_points = np.float32([[0, 0], [side, 0], [side, side], [0, side]])
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(img, matrix, (side, side))

    warped = rotate_image(warped, ROTATION_ANGLE)
    
    # Показуємо сітку
    debug = draw_grid(warped.copy())
    cv2.imshow("Result (Space - Slice)", debug)
    
    key = cv2.waitKey(0)
    cv2.destroyAllWindows()

    if key == 32: # SPACE
        if os.path.exists(OUTPUT_FOLDER): shutil.rmtree(OUTPUT_FOLDER)
        os.makedirs(OUTPUT_FOLDER)

        step = side // 8
        # УВАГА: Перевір порядок!
        # Якщо на фото зліва цифри 1,2,3... (зверху вниз), то ranks = ['1', '2'...]
        # На твоєму фото H1 зліва зверху?
        # Стандарт: 
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
        files = ['h', 'g', 'f', 'e', 'd', 'c', 'b', 'a'] 

        for r in range(8):
            for c in range(8):
                piece = warped[r*step:(r+1)*step, c*step:(c+1)*step]
                filename = f"{OUTPUT_FOLDER}/{files[c]}{ranks[r]}.jpg"
                cv2.imwrite(filename, piece)

        print(f"✅ Готово! Клітинки в папці {OUTPUT_FOLDER}")

if __name__ == "__main__":
    process()