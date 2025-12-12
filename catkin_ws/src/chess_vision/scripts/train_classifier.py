import os
import cv2
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

PACKAGE_ROOT = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(PACKAGE_ROOT, 'data')
MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')

os.makedirs(MODELS_DIR, exist_ok=True)

EMPTY_LIGHT_DIR = os.path.join(DATA_DIR, 'empty_white')
EMPTY_DARK_DIR = os.path.join(DATA_DIR, 'empty_black')
PIECE_DIR = os.path.join(DATA_DIR, 'with_piece')

def extract_features(image_path, bins=(8, 8, 8)):
    """
    Видобуває гістограму кольорів HSV як ознаку для класифікатора.
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Помилка: Не вдалося завантажити зображення {image_path}")
            return None

        # Зміна розміру зображення (для швидкості)
        image = cv2.resize(image, (64, 64))

        # Перетворення колірного простору на HSV (H-колір, S-насиченість, V-яскравість)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Обчислення 3D гістограми
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        # Нормалізація та повернення як вектор ознак
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        print(f"Помилка під час обробки {image_path}: {e}")
        return None


def train_and_save_model():
    print("1. Завантаження та видобування ознак")

    data = [] # Список для ознак
    labels = [] # Список для міток (0: порожня, 1: з фігурою)


    # Завантаження СВІТЛИХ порожніх клітинок
    if os.path.isdir(EMPTY_LIGHT_DIR):
        print(f"Завантаження з: {os.path.basename(EMPTY_LIGHT_DIR)}")
        for filename in os.listdir(EMPTY_LIGHT_DIR):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.join(EMPTY_LIGHT_DIR, filename)
                features = extract_features(path)
                if features is not None:
                    data.append(features)
                    labels.append(0)
    else:
        print(f"[WARNING] Папку {os.path.basename(EMPTY_LIGHT_DIR)} не знайдено. Пропущено.")

    # Завантаження ТЕМНИХ порожніх клітинок
    if os.path.isdir(EMPTY_DARK_DIR):
        print(f"Завантаження з: {os.path.basename(EMPTY_DARK_DIR)}")
        for filename in os.listdir(EMPTY_DARK_DIR):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.join(EMPTY_DARK_DIR, filename)
                features = extract_features(path)
                if features is not None:
                    data.append(features)
                    labels.append(0)
    else:
        print(f"[WARNING] Папку {os.path.basename(EMPTY_DARK_DIR)} не знайдено. Пропущено.")

    # ЗАВАНТАЖЕННЯ КЛІТИНОК З ФІГУРАМИ (Мітка 1)
    if os.path.isdir(PIECE_DIR):
        print(f"Завантаження з: {os.path.basename(PIECE_DIR)}")
        for filename in os.listdir(PIECE_DIR):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.join(PIECE_DIR, filename)
                features = extract_features(path)
                if features is not None:
                    data.append(features)
                    labels.append(1)
    else:
        print(f"[WARNING] Папку {os.path.basename(PIECE_DIR)} не знайдено. Пропущено.")


    if not data:
        print("\n[ПОМИЛКА] Не знайдено зображень для навчання. Перевірте, чи існують папки в data/!")
        return

    data = np.array(data)
    labels = np.array(labels)

    print(f"\nЗагальна кількість зразків: {len(data)}")

    # Розділення на навчальний та тестовий набори (80% / 20%)
    (train_data, test_data, train_labels, test_labels) = train_test_split(
        data, labels, test_size=0.20, random_state=42
    )

    print("\n 2. Навчання класифікатора SVM")
    model = SVC(kernel="linear", C=1.0, random_state=42)
    model.fit(train_data, train_labels)

    print("\n 3. Оцінка моделі")
    predictions = model.predict(test_data)
    accuracy = accuracy_score(test_labels, predictions)
    print(f"Загальна точність на тестовому наборі: {accuracy * 100:.2f}%\n")

    # ДЕТАЛЬНИЙ ЗВІТ ДЛЯ ДІАГНОСТИКИ
    print("--- Звіт про Класифікацію (Classification Report) ---")
    print("Мітки: 0=EMPTY (Порожня клітинка), 1=WITH PIECE (З фігурою)")

    target_names = ['EMPTY (0)', 'WITH PIECE (1)']
    print(classification_report(test_labels, predictions, target_names=target_names, zero_division=0))

    # 4. Збереження моделі
    joblib.dump(model, MODEL_PATH)
    print(f"\n[УСПІХ] Модель збережено до: {MODEL_PATH}")

if __name__ == '__main__':
    train_and_save_model()