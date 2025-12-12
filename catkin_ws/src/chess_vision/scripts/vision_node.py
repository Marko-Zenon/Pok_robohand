import rospy
import chess
import os
import cv2
import numpy as np
from std_msgs.msg import String

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CELLS_FOLDER_RELATIVE = "../data/cells"
CELLS_FOLDER = os.path.join(SCRIPT_DIR, CELLS_FOLDER_RELATIVE)

def is_occupied_classifier(img: np.ndarray) -> bool:
    """
    [ВАШ КЛАСИФІКАТОР]

    Вставляйте логіку свого класифікатора сюди.
    Він повинен повертати True (зайнято) або False (порожньо).

    Вхід:
    - img: Зображення клітинки (наприклад, 80x80 px).

    Вихід:
    - bool: True, якщо на клітинці є фігура; False, якщо порожньо.
    """
    if img is None or img.size == 0:
        return False

    # =========================================================================
    # !!! МІСЦЕ ДЛЯ ІНТЕГРАЦІЇ ВАШОЇ ЛОГІКИ ТУТ !!!
    # Замініть цей блок на виклик вашої моделі:
    #
    # prediction = your_model.predict(img)
    # return prediction == 'occupied'
    #
    # =========================================================================

    # --- ТИМЧАСОВА ЗАГЛУШКА (Простий CV-аналіз) ---
    # Цей код шукає темні пікселі (фігури) на клітинці
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Визначаємо, наскільки світла клітинка в середньому
        average_brightness = np.mean(gray)

        # Якщо середня яскравість значно нижча за 255 (наприклад, менше 230),
        # це означає, що є темна фігура.
        OCCUPANCY_THRESHOLD = 230

        if average_brightness < OCCUPANCY_THRESHOLD:
            return True
        return False
    except Exception as e:
        rospy.logerr(f"Помилка в заглушці класифікатора: {e}")
        return False
    # --- КІНЕЦЬ ЗАГЛУШКИ ---


class ChessVisionProcessor:
    """
    Обробляє дані з камери, визначає хід за зміною зайнятих клітинок (дельта-трекінг)
    та публікує новий FEN-рядок.
    """
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        rospy.init_node('vision_node_processor', anonymous=False)
        self.board = chess.Board(initial_fen)
        # Отримуємо початковий список зайнятих клітинок із FEN
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
        Читає 64 зображення з папки CELLS_FOLDER та повертає список зайнятих клітинок.
        """
        occupied_squares = []

        if not os.path.exists(CELLS_FOLDER):
            rospy.logwarn(f"Папка клітинок не знайдена: {CELLS_FOLDER}")
            return []

        # Якщо в папці недостатньо файлів, чекаємо
        if len([name for name in os.listdir(CELLS_FOLDER) if name.endswith('.jpg')]) < 64:
            rospy.logwarn("Знайдено менше 64 зображень. Очікування нарізки.")
            return []

        # Ітеруємо по всіх 64 шахових клітинках (a1 до h8)
        for i in range(64):
            square_name = chess.square_name(i)
            filename = f"{square_name}.jpg"
            filepath = os.path.join(CELLS_FOLDER, filename)

            img = cv2.imread(filepath)

            if img is None:
                continue

            # --- КЛАСИФІКАЦІЯ ---
            if is_occupied_classifier(img):
                occupied_squares.append(square_name)

            # --- КІНЕЦЬ КЛАСИФІКАЦІЇ ---

        rospy.loginfo(f"Зорова система визначила {len(occupied_squares)} зайнятих клітинок.")
        return occupied_squares

    def loop(self):
        """Головний цикл обробки."""
        rospy.loginfo("Початок циклу обробки зору. Виконується дельта-трекінг зайнятості.")
        rate = rospy.Rate(1) # Перевіряємо раз на секунду
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

        if not new_occupied_squares:
            return

        old_occupied_squares = self.last_occupied_squares

        # Якщо набори зайнятих клітинок ідентичні, хід не відбувся
        if set(new_occupied_squares) == set(old_occupied_squares):
            rospy.loginfo("Позиція не змінилася. Очікування наступного читання.")
            return

        rospy.loginfo("Виявлено зміну позиції. Виконуємо дельта-трекінг...")

        # 2. Знаходження дельти
        # Клітинки, з яких фігура ЗНИКЛА (Це наш START SQUARE)
        start_squares = [sq for sq in old_occupied_squares if sq not in new_occupied_squares]
        # Клітинки, на яких фігура З'ЯВИЛАСЯ (Це наш END SQUARE)
        end_squares = [sq for sq in new_occupied_squares if sq not in old_occupied_squares]

        uci_move = None

        # 3. Ідентифікація ходу на основі дельти

        if len(start_squares) == 1 and len(end_squares) == 1:
            # ПРОСТИЙ ХІД (e2e4) або ПОБИТТЯ
            # Оскільки ми не знаємо колір/тип, ми припускаємо, що це хід з 'start' на 'end'
            start_sq = start_squares[0]
            end_sq = end_squares[0]
            candidate_move = f"{start_sq}{end_sq}"

            # Розраховуємо, який легальний хід відповідає цій зміні
            for move in self.board.legal_moves:
                if move.uci().startswith(candidate_move):
                    uci_move = move.uci()
                    break

            if uci_move:
                rospy.loginfo(f"Виявлено простий хід/побиття (1-1): {uci_move}")
            else:
                rospy.logwarn(f"Хід {candidate_move} не є легальним.")


        elif len(start_squares) == 2 and len(end_squares) == 2:
            # РОКІРУВАННЯ (e1g1 / e1c1)
            # Два зниклих (Король + Тура), Два з'явившихся (Король + Тура на нових позиціях)
            for move in self.board.legal_moves:
                if self.board.is_castling(move):
                    uci_move = move.uci()
                    rospy.loginfo(f"Виявлено рокірування (2-2): {uci_move}")
                    break

            if not uci_move:
                rospy.logwarn("Виявлено складну зміну (2-2), але не знайдено легального рокірування.")

        else:
            rospy.logwarn(f"Не вдалося ідентифікувати хід. Зміни: Зникло={len(start_squares)}, З'явилося={len(end_squares)}.")
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
                    rospy.logwarn(f"[Виявлений хід {uci_move} є нелегальним для FEN: {self.board.fen()}")

            except ValueError:
                rospy.logerr(f"Не вдалося розібрати UCI хід: {uci_move}.")

            except Exception as e:
                rospy.logerr(f"[FATAL] Не вдалося застосувати хід {uci_move}: {e}")