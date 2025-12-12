#!/usr/bin/env python3
import rospy
import chess
import os
import cv2
import numpy as np
import joblib
from std_msgs.msg import String


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CELLS_FOLDER_RELATIVE = "../data/current_snapshot"
CELLS_FOLDER = os.path.join(SCRIPT_DIR, CELLS_FOLDER_RELATIVE)

PACKAGE_ROOT = os.path.join(SCRIPT_DIR, '..')
MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')

CLASSIFIER_MODEL = None

def extract_features(image: np.ndarray, bins=(8, 8, 8)):
    """
    Видобуває гістограму кольорів HSV як ознаку для класифікатора.
    NOTE: Приймає numpy array (зображення), а не шлях до файлу.
    """
    try:
        # Зміна розміру зображення (64x64, узгоджено з навчанням)
        image = cv2.resize(image, (64, 64))

        # Перетворення колірного простору на HSV
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Обчислення 3D гістограми
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        # Нормалізація та повернення як вектор ознак
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        rospy.logerr(f"Помилка під час видобування ознак: {e}")
        return None


def load_classifier():
    """ Завантажує навчену модель SVM у глобальну змінну CLASSIFIER_MODEL. """
    global CLASSIFIER_MODEL
    try:
        CLASSIFIER_MODEL = joblib.load(MODEL_PATH)
        rospy.loginfo(f"[CV INIT] Модель успішно завантажено з {MODEL_PATH}")
        return True
    except FileNotFoundError:
        rospy.logfatal(f"[CV FATAL] Модель не знайдено! Шлях: {MODEL_PATH}. Спочатку запустіть train_classifier.py.")
        return False
    except Exception as e:
        rospy.logfatal(f"[CV FATAL] Помилка завантаження моделі: {e}")
        return False


def is_occupied_classifier(img: np.ndarray) -> bool:
    """
    Використовує навчений класифікатор (SVM) для визначення зайнятості клітинки.

    :param img: Зображення клітинки як numpy array.
    :return: True, якщо на клітинці є фігура (1); False, якщо порожньо (0).
    """
    global CLASSIFIER_MODEL

    if CLASSIFIER_MODEL is None:
        # Попереджаємо, але не надто часто
        rospy.logwarn_throttle(5, "Класифікатор не завантажений. Пропускаємо класифікацію.")
        return False

    if img is None or img.size == 0:
        return False

    try:
        # 1. Видобування ознак
        features = extract_features(img)

        if features is None:
            return False

        # 2. Класифікація (features.reshape(1, -1) для одного зразка)
        features = features.reshape(1, 1) if features.ndim == 0 else features.reshape(1, -1)
        prediction = CLASSIFIER_MODEL.predict(features)[0]

        # 1 = WITH PIECE (З фігурою), 0 = EMPTY (Порожня клітинка)
        return prediction == 1

    except Exception as e:
        rospy.logerr(f"Помилка в класифікаторі: {e}")
        return False


class ChessVisionProcessor:
    """
    Обробляє дані з камери, визначає хід за зміною зайнятих клітинок (дельта-трекінг)
    та публікує новий FEN-рядок.
    """
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        # Ініціалізація дошки
        self.board = chess.Board(initial_fen)
        self.last_occupied_squares = self._get_occupied_squares_from_board(self.board)
        self.fen_publisher = rospy.Publisher('/chess_state/fen', String, queue_size=1)

        rospy.loginfo(f"ChessVisionProcessor ініціалізовано. FEN-паблішер на /chess_state/fen.")
        rospy.loginfo(f"Початковий стан: {self.board.fen()}")

    def _get_occupied_squares_from_board(self, board_state: chess.Board) -> list:
        """Повертає список зайнятих клітинок на основі об'єкта chess.Board."""
        occupied = []
        for i in range(64):
            sq_name = chess.square_name(i)
            # Перевіряє, чи є фігура на клітинці
            if board_state.piece_at(i) is not None:
                occupied.append(sq_name)
        return occupied

    def _classify_all_squares_to_occupied_list(self) -> list:
        """
        Читає 64 зображення з папки CELLS_FOLDER та повертає список зайнятих клітинок,
        використовуючи навчений класифікатор.
        """
        occupied_squares = []

        if not os.path.exists(CELLS_FOLDER):
            rospy.logwarn(f"Папка клітинок не знайдена: {CELLS_FOLDER}")
            return []

        # Перевірка на наявність достатньої кількості файлів
        if len([name for name in os.listdir(CELLS_FOLDER) if name.endswith(('.jpg', '.jpeg', '.png'))]) < 64:
            rospy.logwarn("Знайдено менше 64 зображень. Очікування нарізки.")
            return []

        # Ітеруємо по всіх 64 шахових клітинках (a1 до h8)
        for i in range(64):
            square_name = chess.square_name(i)
            # Припускаємо, що файли названі за шаховими клітинками (наприклад, a1.jpg)
            filename = f"{square_name}.jpg"
            filepath = os.path.join(CELLS_FOLDER, filename)

            img = cv2.imread(filepath)

            if img is None:
                continue

            # КЛАСИФІКАЦІЯ
            if is_occupied_classifier(img):
                occupied_squares.append(square_name)
            # КІНЕЦЬ КЛАСИФІКАЦІЇ

        # rospy.loginfo(f"Зорова система визначила {len(occupied_squares)} зайнятих клітинок.")
        return occupied_squares

    def loop(self):
        """Головний цикл обробки. Запускається після успішного завантаження моделі."""
        rospy.loginfo("Початок циклу обробки зору. Виконується дельта-трекінг зайнятості.")
        rate = rospy.Rate(1/20) # Перевіряємо раз на 20 секунду
        while not rospy.is_shutdown():
            self.process_new_state()
            rate.sleep()

    def process_new_state(self):
        """
        1. Отримує новий список зайнятих клітинок.
        2. Знаходить дельту (зниклі/з'явилися клітинки).
        3. Ідентифікує легальний хід і застосовує його.
        """
        # 1. Отримуємо новий стан через ML-класифікатор
        new_occupied_squares = self._classify_all_squares_to_occupied_list()

        if not new_occupied_squares:
            return

        old_occupied_squares = self.last_occupied_squares

        # Якщо набори зайнятих клітинок ідентичні, хід не відбувся
        if set(new_occupied_squares) == set(old_occupied_squares):
            rospy.loginfo("Позиція не змінилася. Очікування наступного читання.")
            return

        rospy.loginfo("Виявлено зміну позиції. Виконуємо дельта-трекінг...")

        # 2. Знаходження дельти
        start_squares = [sq for sq in old_occupied_squares if sq not in new_occupied_squares]
        end_squares = [sq for sq in new_occupied_squares if sq not in old_occupied_squares]

        uci_move = None

        # 3. Ідентифікація ходу на основі дельти

        # Випадок 1: ПРОСТИЙ ХІД / ПОБИТТЯ (1-1)
        if len(start_squares) == 1 and len(end_squares) == 1:
            start_sq = start_squares[0]
            end_sq = end_squares[0]
            candidate_move = f"{start_sq}{end_sq}"

            # Розраховуємо, який легальний хід відповідає цій зміні
            for move in self.board.legal_moves:
                # Перевіряємо простий хід або просування без перетворення
                if move.uci().startswith(candidate_move):
                    uci_move = move.uci()
                    break

                # Обробка просування пішака (якщо це легальний хід, але без 'q', 'r'...)
                # Треба спробувати всі 4 варіанти просування (e7e8q, e7e8r, e7e8b, e7e8n)
                if move.to_square == chess.parse_square(end_sq) and self.board.piece_at(move.from_square).piece_type == chess.PAWN:
                    if move.uci()[:-1] == candidate_move: # Якщо move.uci() = e7e8q, а candidate_move = e7e8
                        uci_move = move.uci()
                        break


        # Випадок 2: РОКІРУВАННЯ (2-2)
        elif len(start_squares) == 2 and len(end_squares) == 2:
            # Тут ми просто шукаємо легальне рокірування, бо дельта-трекінг не може відрізнити
            # куди пішов король, а куди тура (це має бути вирішено автоматично бібліотекою)
            for move in self.board.legal_moves:
                if self.board.is_castling(move):
                    uci_move = move.uci()
                    rospy.loginfo(f"Виявлено рокірування (2-2): {uci_move}")
                    break

        # Випадок 3: ВЗЯТТЯ НА ПРОХОДІ (En Passant)
        # 1 зникла (пішак, що побив), 2 з'явилися (пішак, що побив, + пуста клітинка для побитого пішака)
        # Цей випадок складний для зорової системи, тому поки що покладаємося на те,
        # що легальний хід буде знайдено під час ітерації

        if not uci_move:
            rospy.logwarn(f"Не вдалося ідентифікувати легальний хід. Зміни: Зникло={len(start_squares)}, З'явилося={len(end_squares)}.")
            return


        # 4. Застосування ходу та публікація
        if uci_move:
            try:
                move = self.board.parse_uci(uci_move)

                if move in self.board.legal_moves:
                    self.board.push(move)
                    new_fen = self.board.fen()

                    # Оновлюємо внутрішній стан зайнятих клітинок
                    self.last_occupied_squares = self._get_occupied_squares_from_board(self.board)

                    # Публікація нового FEN
                    msg = String()
                    msg.data = new_fen
                    self.fen_publisher.publish(msg)
                    rospy.loginfo(f"Успішно застосовано хід {uci_move}. Опубліковано FEN: {new_fen}")

                else:
                    rospy.logwarn(f"[Виявлений хід {uci_move} є нелегальним для FEN: {self.board.fen()}")

            except ValueError:
                rospy.logerr(f"Не вдалося розібрати UCI хід: {uci_move}.")

            except Exception as e:
                rospy.logerr(f"[FATAL] Не вдалося застосувати хід {uci_move}: {e}")

def main():
    """ Головна функція ROS-вузла. """
    # 1. Завантаження класифікатора
    if not load_classifier():
        return

    rospy.init_node('vision_node', anonymous=False)
    # 2. Ініціалізація та запуск процесора
    try:
        processor = ChessVisionProcessor()
        processor.loop()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()