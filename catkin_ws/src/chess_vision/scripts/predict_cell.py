#!/usr/bin/env python3

import rospy
import chess
import os
import cv2
import numpy as np
import joblib
from std_msgs.msg import String
from sklearn.svm import SVC


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.join(SCRIPT_DIR, '..')
MODELS_DIR = os.path.join(PACKAGE_ROOT, 'models')
DATA_DIR = os.path.join(PACKAGE_ROOT, 'data')

MODEL_PATH = os.path.join(MODELS_DIR, 'piece_classifier.pkl')
CELLS_FOLDER = os.path.join(DATA_DIR, 'cells')

classifier = None
MODEL_LOAD_SUCCESS = False

def extract_features(img: np.ndarray, bins=(8, 8, 8)) -> np.ndarray or None:
    """
    Видобуває гістограму кольорів HSV як ознаку для класифікатора.
    Функція ідентична тій, що використовувалася під час навчання.
    """
    if img is None or img.size == 0:
        return None

    try:
        # Зміна розміру зображення
        image = cv2.resize(img, (64, 64))

        # Перетворення колірного простору на HSV
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Обчислення 3D гістограми
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        # Нормалізація та повернення як вектор ознак
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        print(f"Помилка під час обробки ознак: {e}")
        return None

def load_classifier():
    """Завантажує модель класифікатора у пам'ять."""
    global classifier, MODEL_LOAD_SUCCESS
    if classifier is not None:
        MODEL_LOAD_SUCCESS = True
        return

    rospy.loginfo(f"Спроба завантажити модель з: {MODEL_PATH}")
    try:
        joblib.load
        classifier = joblib.load(MODEL_PATH)
        rospy.loginfo("Модель класифікатора зайнятості успішно завантажено.")
        MODEL_LOAD_SUCCESS = True
    except FileNotFoundError:
        rospy.logerr(f"Модель не знайдено! Перевірте шлях: {MODEL_PATH}")
        rospy.logerr("Будь ласка, спочатку запустіть train_classifier.py.")
        MODEL_LOAD_SUCCESS = False
    except Exception as e:
        rospy.logerr(f"[FATAL] Помилка завантаження моделі: {e}")
        MODEL_LOAD_SUCCESS = False


def is_occupied_classifier(img: np.ndarray) -> bool:
    """
    Виконує класифікацію зображення клітинки.
    Повертає True, якщо клітинка зайнята (клас 1), False, якщо порожня (клас 0).
    """
    if not MODEL_LOAD_SUCCESS or classifier is None:
        rospy.logwarn_once("Класифікатор не завантажено. Використовуються тимчасові значення.")
        return False

    features = extract_features(img)

    if features is None:
        return False

    try:
        # Класифікація
        features = features.reshape(1, -1)
        # prediction повертає масив, беремо перший елемент
        prediction = classifier.predict(features)[0]

        # 1 означає "WITH PIECE" (Зайнято), 0 означає "EMPTY" (Порожньо)
        return int(prediction) == 1

    except Exception as e:
        rospy.logerr(f"Помилка під час класифікації зображення: {e}")
        return False


class ChessVisionProcessor:
    """
    Обробляє дані з камери, визначає хід за зміною зайнятих клітинок (дельта-трекінг)
    та публікує новий FEN-рядок.
    """
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        rospy.init_node('vision_node_processor', anonymous=False)
        load_classifier() # Завантажуємо модель при ініціалізації вузла

        self.board = chess.Board(initial_fen)
        # Отримуємо початковий список зайнятих клітинок із FEN
        self.last_occupied_squares = self._get_occupied_squares_from_board(self.board)
        self.fen_publisher = rospy.Publisher('/chess_state/fen', String, queue_size=1)

        rospy.loginfo(f"ChessVisionProcessor ініціалізовано. FEN-паблішер на /chess_state/fen.")
        rospy.loginfo(f"Початковий FEN: {self.board.fen()}")

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
        Читає 64 зображення з папки CELLS_FOLDER та повертає список зайнятих клітинок.
        """
        occupied_squares = []

        if not os.path.exists(CELLS_FOLDER):
            rospy.logwarn(f"Папка клітинок не знайдена: {CELLS_FOLDER}")
            return []

        # Ітеруємо по всіх 64 шахових клітинках (a1 до h8)
        for i in range(64):
            square_name = chess.square_name(i)
            filename = f"{square_name}.jpg"
            filepath = os.path.join(CELLS_FOLDER, filename)

            img = cv2.imread(filepath)

            if img is None:
                continue

            # --- ВИКЛИК ВАШОГО КЛАСИФІКАТОРА ---
            if is_occupied_classifier(img):
                occupied_squares.append(square_name)

            # --- КІНЕЦЬ КЛАСИФІКАЦІЇ ---

        # rospy.loginfo(f"Зорова система визначила {len(occupied_squares)} зайнятих клітинок.")
        return occupied_squares

    def loop(self):
        """Головний цикл обробки."""
        rospy.loginfo("Початок циклу обробки зору. Виконується дельта-трекінг зайнятості.")
        rate = rospy.Rate(1) # Перевіряємо раз на секунду

        # Перевірка, чи була модель успішно завантажена
        if not MODEL_LOAD_SUCCESS:
            rospy.logfatal("Модель класифікатора не була завантажена. Вузол зупиняється.")
            return

        while not rospy.is_shutdown():
            self.process_new_state()
            rate.sleep()

    def process_new_state(self):
        """
        1. Отримує новий список зайнятих клітинок.
        2. Знаходить дельту (зниклі/з'явилися клітинки).
        3. Ідентифікує легальний хід і застосовує його.
        """
        # 1. Отримуємо новий стан
        new_occupied_squares = self._classify_all_squares_to_occupied_list()

        if not new_occupied_squares and len(self.last_occupied_squares) > 0:
            # Можливо, виникла помилка читання файлів, але ми не хочемо зупинятися
            rospy.logwarn_throttle(5, "Новий список зайнятих клітинок порожній. Перевірте, чи генеруються зображення.")
            return

        old_occupied_squares = self.last_occupied_squares

        # Якщо набори зайнятих клітинок ідентичні, хід не відбувся
        if set(new_occupied_squares) == set(old_occupied_squares):
            # rospy.loginfo("Позиція не змінилася. Очікування наступного читання.")
            return

        rospy.loginfo("Виявлено зміну позиції. Виконуємо дельта-трекінг...")

        # 2. Знаходження дельти
        start_squares = sorted([sq for sq in old_occupied_squares if sq not in new_occupied_squares]) # ЗНИКЛА
        end_squares = sorted([sq for sq in new_occupied_squares if sq not in old_occupied_squares])   # З'ЯВИЛАСЯ

        uci_move = None

        # 3. Ідентифікація ходу на основі дельти

        if len(start_squares) == 1 and len(end_squares) == 1:
            # ПРОСТИЙ ХІД (e2e4) або ПОБИТТЯ
            candidate_move = f"{start_squares[0]}{end_squares[0]}"

            # Шукаємо легальний хід, який починається з цієї комбінації
            for move in self.board.legal_moves:
                if move.uci().startswith(candidate_move):
                    uci_move = move.uci()
                    break

            if uci_move:
                rospy.loginfo(f"Виявлено простий хід/побиття (1-1): {uci_move}")
            else:
                rospy.logwarn(f"Хід {candidate_move} не є легальним або є нестандартним (наприклад, перетворення пішака).")

                # Спеціальна обробка для ПЕРЕТВОРЕННЯ ПІШАКА (Pawn Promotion)
                # Якщо цільова клітинка - остання горизонталь (rank 8 або 1)
                end_sq = end_squares[0]
                piece_to_move = self.board.piece_at(chess.parse_square(start_squares[0]))

                if piece_to_move and piece_to_move.piece_type == chess.PAWN and \
                        ((self.board.turn == chess.WHITE and end_sq[1] == '8') or \
                         (self.board.turn == chess.BLACK and end_sq[1] == '1')):

                    # Перевіряємо всі можливі перетворення (q, r, b, n)
                    for promo in ['q', 'r', 'b', 'n']:
                        promo_move = f"{candidate_move}{promo}"
                        try:
                            move = self.board.parse_uci(promo_move)
                            if move in self.board.legal_moves:
                                uci_move = promo_move
                                rospy.loginfo(f"Виявлено ПЕРЕТВОРЕННЯ ПІШАКА: {uci_move}")
                                break
                        except ValueError:
                            continue

                    if not uci_move:
                        rospy.logwarn("Виявлено зміну 1-1 на останній горизонталі, але легального перетворення не знайдено.")


        elif len(start_squares) == 2 and len(end_squares) == 2:
            # РОКІРУВАННЯ (e1g1 / e1c1)
            # Ми просто шукаємо єдиний легальний хід рокірування, оскільки дельта 2-2 є найбільш характерною ознакою
            for move in self.board.legal_moves:
                if self.board.is_castling(move):
                    uci_move = move.uci()
                    rospy.loginfo(f"Виявлено рокірування (2-2): {uci_move}")
                    break

            if not uci_move:
                rospy.logwarn("Виявлено складну зміну (2-2), але не знайдено легального рокірування.")

        else:
            # Якщо кількість змінених клітинок не відповідає типовому ходу
            rospy.logwarn(f"Не вдалося ідентифікувати хід. Зміни: Зникло={start_squares}, З'явилося={end_squares}. Можливо, це нелегальний хід.")
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
                    rospy.loginfo(f"✅ Успішно застосовано хід {uci_move}. Опубліковано FEN: {new_fen}")

                else:
                    rospy.logwarn(f"[ERROR] Виявлений хід {uci_move} є нелегальним для FEN: {self.board.fen()}")

            except ValueError:
                rospy.logerr(f"[ERROR] Не вдалося розібрати UCI хід: {uci_move}.")

            except Exception as e:
                rospy.logerr(f"[FATAL] Не вдалося застосувати хід {uci_move}: {e}")

        # Якщо нічого не виявлено, просто чекаємо наступного циклу.


if __name__ == '__main__':
    try:
        processor = ChessVisionProcessor()
        processor.loop()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"Критична помилка вузла зору: {e}")
