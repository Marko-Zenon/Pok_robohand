# import os
# import cv2
# import numpy as np
# from sklearn.svm import SVC
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import accuracy_score, classification_report
# import joblib
#
# PACKAGE_ROOT = os.path.join(os.path.dirname(__file__), '..')
# DATA_DIR = os.path.join(PACKAGE_ROOT, 'data')
# MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
# MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')
#
# os.makedirs(MODELS_DIR, exist_ok=True)
#
# EMPTY_LIGHT_DIR = os.path.join(DATA_DIR, 'empty_white')
# EMPTY_DARK_DIR = os.path.join(DATA_DIR, 'empty_black')
# PIECE_DIR = os.path.join(DATA_DIR, 'with_piece')
#
# def extract_features(image_path, bins=(8, 8, 8)):
#     """
#     Видобуває гістограму кольорів HSV як ознаку для класифікатора.
#     """
#     try:
#         image = cv2.imread(image_path)
#         if image is None:
#             print(f"Помилка: Не вдалося завантажити зображення {image_path}")
#             return None
#
#         # Зміна розміру зображення (для швидкості)
#         image = cv2.resize(image, (64, 64))
#
#         # Перетворення колірного простору на HSV (H-колір, S-насиченість, V-яскравість)
#         image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#
#         # Обчислення 3D гістограми
#         hist = cv2.calcHist([image], [0, 1, 2], None, bins,
#                             [0, 180, 0, 256, 0, 256])
#
#         # Нормалізація та повернення як вектор ознак
#         hist = cv2.normalize(hist, hist).flatten()
#         return hist
#
#     except Exception as e:
#         print(f"Помилка під час обробки {image_path}: {e}")
#         return None
#
#
# def train_and_save_model():
#     print("1. Завантаження та видобування ознак")
#
#     data = [] # Список для ознак
#     labels = [] # Список для міток (0: порожня, 1: з фігурою)
#
#
#     # Завантаження СВІТЛИХ порожніх клітинок
#     if os.path.isdir(EMPTY_LIGHT_DIR):
#         print(f"Завантаження з: {os.path.basename(EMPTY_LIGHT_DIR)}")
#         for filename in os.listdir(EMPTY_LIGHT_DIR):
#             if filename.endswith(('.jpg', '.png', '.jpeg')):
#                 path = os.path.join(EMPTY_LIGHT_DIR, filename)
#                 features = extract_features(path)
#                 if features is not None:
#                     data.append(features)
#                     labels.append(0)
#     else:
#         print(f"[WARNING] Папку {os.path.basename(EMPTY_LIGHT_DIR)} не знайдено. Пропущено.")
#
#     # Завантаження ТЕМНИХ порожніх клітинок
#     if os.path.isdir(EMPTY_DARK_DIR):
#         print(f"Завантаження з: {os.path.basename(EMPTY_DARK_DIR)}")
#         for filename in os.listdir(EMPTY_DARK_DIR):
#             if filename.endswith(('.jpg', '.png', '.jpeg')):
#                 path = os.path.join(EMPTY_DARK_DIR, filename)
#                 features = extract_features(path)
#                 if features is not None:
#                     data.append(features)
#                     labels.append(0)
#     else:
#         print(f"[WARNING] Папку {os.path.basename(EMPTY_DARK_DIR)} не знайдено. Пропущено.")
#
#     # ЗАВАНТАЖЕННЯ КЛІТИНОК З ФІГУРАМИ (Мітка 1)
#     if os.path.isdir(PIECE_DIR):
#         print(f"Завантаження з: {os.path.basename(PIECE_DIR)}")
#         for filename in os.listdir(PIECE_DIR):
#             if filename.endswith(('.jpg', '.png', '.jpeg')):
#                 path = os.path.join(PIECE_DIR, filename)
#                 features = extract_features(path)
#                 if features is not None:
#                     data.append(features)
#                     labels.append(1)
#     else:
#         print(f"[WARNING] Папку {os.path.basename(PIECE_DIR)} не знайдено. Пропущено.")
#
#
#     if not data:
#         print("\n[ПОМИЛКА] Не знайдено зображень для навчання. Перевірте, чи існують папки в data/!")
#         return
#
#     data = np.array(data)
#     labels = np.array(labels)
#
#     print(f"\nЗагальна кількість зразків: {len(data)}")
#
#     # Розділення на навчальний та тестовий набори (80% / 20%)
#     (train_data, test_data, train_labels, test_labels) = train_test_split(
#         data, labels, test_size=0.20, random_state=42
#     )
#
#     print("\n 2. Навчання класифікатора SVM")
#     model = SVC(kernel="linear", C=1.0, random_state=42)
#     model.fit(train_data, train_labels)
#
#     print("\n 3. Оцінка моделі")
#     predictions = model.predict(test_data)
#     accuracy = accuracy_score(test_labels, predictions)
#     print(f"Загальна точність на тестовому наборі: {accuracy * 100:.2f}%\n")
#
#     # ДЕТАЛЬНИЙ ЗВІТ ДЛЯ ДІАГНОСТИКИ
#     print("--- Звіт про Класифікацію (Classification Report) ---")
#     print("Мітки: 0=EMPTY (Порожня клітинка), 1=WITH PIECE (З фігурою)")
#
#     target_names = ['EMPTY (0)', 'WITH PIECE (1)']
#     print(classification_report(test_labels, predictions, target_names=target_names, zero_division=0))
#
#     # 4. Збереження моделі
#     joblib.dump(model, MODEL_PATH)
#     print(f"\n[УСПІХ] Модель збережено до: {MODEL_PATH}")
#
# if __name__ == '__main__':
#     train_and_save_model()


import os
import cv2
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# =========================================================================
# НАЛАШТУВАННЯ ТА ШЛЯХИ
# =========================================================================

PACKAGE_ROOT = os.path.join(os.path.dirname(__file__), '..')
DATA_DIR = os.path.join(PACKAGE_ROOT, 'data')
MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')

os.makedirs(MODELS_DIR, exist_ok=True)

EMPTY_WHITE_DIR = os.path.join(DATA_DIR, 'empty_white')
EMPTY_BLACK_DIR = os.path.join(DATA_DIR, 'empty_black')
PIECE_DIR = os.path.join(DATA_DIR, 'with_piece')

# =========================================================================
# ФУНКЦІЯ АУГМЕНТАЦІЇ (ОНОВЛЕНО)
# =========================================================================

def augment_image(image: np.ndarray) -> np.ndarray:
    """
    Застосовує випадкові перетворення для імітації поганої якості (шум, зміна освітлення).

    :param image: Оригінальне зображення клітинки (BGR).
    :return: Аугментоване зображення.
    """
    # 1. Зміна яскравості та контрасту (імітація тіней/відблисків)
    # Alpha (контраст) від 0.85 до 1.15
    alpha = 1.0 + np.random.uniform(-0.15, 0.15)
    # Beta (яскравість) від -10 до +10
    beta = np.random.uniform(-10, 10)

    # Використовуємо cv2.convertScaleAbs для застосування: image * alpha + beta
    augmented_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)

    # 2. Додавання невеликого Гаусового шуму
    row, col, ch = augmented_image.shape
    mean = 0
    sigma = np.random.uniform(1, 5) # Випадкова інтенсивність шуму
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)

    # Додавання шуму та обмеження значень від 0 до 255
    noisy_image = augmented_image.astype(float) + gauss
    noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)

    return noisy_image


# =========================================================================
# ФУНКЦІЯ ВИДОБУВАННЯ ОЗНАК (FEATURE EXTRACTION)
# =========================================================================

def extract_features(image: np.ndarray, bins=(8, 8, 8)):
    """
    Видобуває гістограму кольорів HSV як ознаку з об'єкта зображення.
    """
    try:
        if image is None:
            return None

        # 1. Зміна розміру зображення (для швидкості)
        image = cv2.resize(image, (64, 64))

        # 2. Перетворення колірного простору на HSV (H-колір, S-насиченість, V-яскравість)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 3. Обчислення 3D гістограми
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        # 4. Нормалізація та повернення як вектор ознак
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        print(f"Помилка під час обробки зображення: {e}")
        return None

# =========================================================================
# НАВЧАННЯ МОДЕЛІ
# =========================================================================

def load_and_augment_data(directory, label, num_augmentations=4):
    """ Завантажує оригінальні зображення та генерує аугментовані версії. """
    features_list = []
    labels_list = []

    if os.path.isdir(directory):
        print(f"Завантаження та аугментація з: {os.path.basename(directory)}")

        for filename in os.listdir(directory):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                path = os.path.join(directory, filename)
                original_image = cv2.imread(path)

                if original_image is None:
                    continue

                # 1. Обробка оригінального зображення
                original_features = extract_features(original_image)
                if original_features is not None:
                    features_list.append(original_features)
                    labels_list.append(label)

                # 2. Обробка аугментованих зображень (для збільшення набору даних)
                for _ in range(num_augmentations):
                    augmented_image = augment_image(original_image)
                    augmented_features = extract_features(augmented_image)
                    if augmented_features is not None:
                        features_list.append(augmented_features)
                        labels_list.append(label)

    return features_list, labels_list


def train_and_save_model():
    print("1. Завантаження та видобування ознак")

    data = [] # Список для ознак
    labels = [] # Список для міток (0: порожня, 1: з фігурою)

    # Кількість аугментацій на оригінальне зображення
    NUM_AUGMENT = 4

    # --- ЗАВАНТАЖЕННЯ ПОРОЖНІХ КЛІТИНОК (Мітка 0) ---
    print(f"Примітка: Кожен знімок буде аугментовано {NUM_AUGMENT} разів.")

    # Завантаження БІЛИХ порожніх клітинок
    f, l = load_and_augment_data(EMPTY_WHITE_DIR, 0, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)

    # Завантаження ЧОРНИХ порожніх клітинок
    f, l = load_and_augment_data(EMPTY_BLACK_DIR, 0, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)

    # --- ЗАВАНТАЖЕННЯ КЛІТИНОК З ФІГУРАМИ (Мітка 1) ---
    f, l = load_and_augment_data(PIECE_DIR, 1, NUM_AUGMENT)
    data.extend(f)
    labels.extend(l)


    if not data:
        print("\n[ПОМИЛКА] Не знайдено зображень для навчання. Перевірте, чи існують папки в data/!")
        return

    data = np.array(data)
    labels = np.array(labels)

    print(f"\nЗагальна кількість зразків (з аугментацією): {len(data)}")

    # Розділення на навчальний та тестовий набори (80% / 20%)
    # Тестовий набір залишається чистим (без аугментації)
    (train_data, test_data, train_labels, test_labels) = train_test_split(
        data, labels, test_size=0.20, random_state=42
    )

    # Виводимо кількість тестових зразків для контролю
    print(f"Кількість тестових зразків: {len(test_data)}")


    print("\n 2. Навчання класифікатора SVM")
    model = SVC(kernel="linear", C=1.0, random_state=42)
    model.fit(train_data, train_labels)

    print("\n 3. Оцінка моделі")
    predictions = model.predict(test_data)
    accuracy = accuracy_score(test_labels, predictions)
    print(f"Загальна точність на тестовому наборі: {accuracy * 100:.2f}%\n")

    # === ДЕТАЛЬНИЙ ЗВІТ ДЛЯ ДІАГНОСТИКИ ===
    print("--- Звіт про Класифікацію (Classification Report) ---")
    print("Мітки: 0=EMPTY (Порожня клітинка), 1=WITH PIECE (З фігурою)")

    target_names = ['EMPTY (0)', 'WITH PIECE (1)']
    print(classification_report(test_labels, predictions, target_names=target_names, zero_division=0))
    # =====================================

    # 4. Збереження моделі
    joblib.dump(model, MODEL_PATH)
    print(f"\n[УСПІХ] Модель збережено до: {MODEL_PATH}")

if __name__ == '__main__':
    train_and_save_model()