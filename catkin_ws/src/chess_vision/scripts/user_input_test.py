#!/usr/bin/env python3
"""
Скрипт для симуляції ходу людини шляхом маніпуляції файлами зображень.
"""
import os
import sys
import shutil
import glob
import chess



PACKAGE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CURRENT_SNAPSHOT_DIR = os.path.join(PACKAGE_ROOT, 'data/current_snapshot')
STARTING_POSITION_DIR = os.path.join(PACKAGE_ROOT, 'data/starting_position')

MOCK_CLEAN_FILES = {
    'white': 'a4.jpg',
    'black': 'a3.jpg',
}

CHESS_BOARD = chess.Board(None)

def reset_current_snapshot():
    """
    Видаляє вміст робочої папки (CURRENT_SNAPSHOT_DIR) і копіює туди
    чистий набір файлів із джерела (STARTING_POSITION_DIR).
    """
    # (Функція скидання залишається майже без змін, оскільки вона коректно працює)
    print("\nРОЗПОЧАТО СКИДАННЯ СТАНУ")

    if not os.path.isdir(STARTING_POSITION_DIR) or not any(glob.glob(os.path.join(STARTING_POSITION_DIR, '*'))):
        print(f"Не знайдено папку-джерело або вона порожня: {STARTING_POSITION_DIR}")
        return False

    try:
        # Видалення поточного вмісту
        files_to_delete = glob.glob(os.path.join(CURRENT_SNAPSHOT_DIR, '*'))
        for f in files_to_delete:
            if os.path.isfile(f):
                os.remove(f)
        print(f"Видалено {len(files_to_delete)} поточних файлів.")

        # Копіювання файлів із джерела
        copied_count = 0
        for item_name in os.listdir(STARTING_POSITION_DIR):
            source_item = os.path.join(STARTING_POSITION_DIR, item_name)
            target_item = os.path.join(CURRENT_SNAPSHOT_DIR, item_name)
            if os.path.isfile(source_item):
                shutil.copy2(source_item, target_item)
                copied_count += 1

        print(f"Скопійовано {copied_count} файлів. Дошка повернута до початкової позиції.")
        return True
    except Exception as e:
        print(f"Виникла помилка: {e}")
        return False

def is_valid_uci(uci_input):
    """Проста перевірка формату UCI (4 або 5 символів)."""
    return 4 <= len(uci_input) <= 5 and uci_input.isalnum()

def get_square_color(square_name: str) -> str:
    """Визначає, чи є клітинка чорною або білою."""
    try:
        sq_index = chess.parse_square(square_name)
        if CHESS_BOARD.color_at(sq_index) == chess.BLACK:
            return 'black'
        else:
            return 'white'
    except:
        return 'white'

def simulate_move(uci_move: str):
    """
    Симулює хід (переміщення або биття) шляхом копіювання файлів.

    :param uci_move: Хід у форматі UCI (наприклад, 'e2e4', 'e4d5').
    """
    start_sq = uci_move[:2].lower() # e.g., 'e4'
    end_sq = uci_move[2:4].lower()   # e.g., 'd5'

    start_path_orig = os.path.join(CURRENT_SNAPSHOT_DIR, f"{start_sq}.jpg")
    end_path_orig = os.path.join(CURRENT_SNAPSHOT_DIR, f"{end_sq}.jpg")

    # Визначаємо, яким має стати 'порожній' файл для клітинки відправлення (start_sq)
    start_sq_color = get_square_color(start_sq)
    empty_template_name = MOCK_CLEAN_FILES.get(start_sq_color, MOCK_CLEAN_FILES['white'])
    empty_template_path = os.path.join(STARTING_POSITION_DIR, empty_template_name)

    if not os.path.exists(empty_template_path):
        print(f"[ERROR] Не знайдено шаблон порожньої клітинки: {empty_template_path}. Неможливо скинути start_sq.")
        return

    # 2. Перевіряємо існування файлів
    if not os.path.exists(start_path_orig) or not os.path.exists(end_path_orig):
        print(f"[ERROR] Не знайдено один або обидва файли: {start_sq}.jpg або {end_sq}.jpg")
        return


    try:
        shutil.copy2(empty_template_path, start_path_orig)
        print(f"Клітинка {start_sq} очищена (стала {start_sq_color} клітинкою).")
    except Exception as e:
        print(f"Не вдалося очистити клітинку {start_sq}: {e}")
        return

    source_piece_template = os.path.join(STARTING_POSITION_DIR, f"{start_sq}.jpg")

    if os.path.exists(source_piece_template):
        try:
            # Копіюємо зображення з фігурою (наприклад, e4) на клітинку призначення (d5)
            shutil.copy2(source_piece_template, end_path_orig)
            print(f"[SIMULATE] Фігура з {start_sq} переміщена/захопила {end_sq}.")
        except Exception as e:
            print(f"[ERROR] Не вдалося перемістити фігуру на клітинку {end_sq}: {e}")
            return
    else:
        print(f"Не знайдено шаблон фігури {start_sq}.jpg у джерелі.")

    print(f"Хід {uci_move} імітовано: {start_sq}.jpg тепер порожній, {end_sq}.jpg оновлено.")


def main():
    """Головний цикл симулятора ходів."""
    print("OS Chess Vision Move Simulator (user_input.py)")
    print(f"Використовується папка знімків: {CURRENT_SNAPSHOT_DIR}")

    if not os.path.exists(CURRENT_SNAPSHOT_DIR):
        print(f"Папка {CURRENT_SNAPSHOT_DIR} не знайдена")
        sys.exit(1)

    reset_current_snapshot()

    while True:
        try:
            user_input = input("\nВведіть хід UCI (напр., e2e4 або e4d5), 'reset' або 'quit': ").strip().lower()

            if user_input == 'quit':
                break

            if user_input == 'reset':
                reset_current_snapshot()
                continue

            if not is_valid_uci(user_input):
                print("Неправильний формат. Введіть 4 або 5 символів UCI (наприклад, 'a7a6').")
                continue

            simulate_move(user_input)

        except EOFError:
            break

        except Exception as e:
            print(f"Виникла помилка: {e}")
            break

    reset_current_snapshot()

if __name__ == '__main__':
    main()
