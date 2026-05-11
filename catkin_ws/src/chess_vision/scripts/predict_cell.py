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
    Extracts color histogram
    """
    if img is None or img.size == 0:
        return None

    try:
        image = cv2.resize(img, (64, 64))

        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Calculate histogram
        hist = cv2.calcHist([image], [0, 1, 2], None, bins,
                            [0, 180, 0, 256, 0, 256])

        hist = cv2.normalize(hist, hist).flatten()
        return hist

    except Exception as e:
        print(f"Error in extract_features(): {e}")
        return None

def load_classifier():
    """Loads classifier"""
    global classifier, MODEL_LOAD_SUCCESS
    if classifier is not None:
        MODEL_LOAD_SUCCESS = True
        return

    rospy.loginfo(f"Trying to upload from: {MODEL_PATH}")
    try:
        joblib.load
        classifier = joblib.load(MODEL_PATH)
        rospy.loginfo("Model is uploaded")
        MODEL_LOAD_SUCCESS = True
    except FileNotFoundError:
        rospy.logerr(f"Model not found")
        rospy.logerr("Firstly run train_classifier.py.")
        MODEL_LOAD_SUCCESS = False
    except Exception as e:
        rospy.logerr(f"Error: {e}")
        MODEL_LOAD_SUCCESS = False


def is_occupied_classifier(img: np.ndarray) -> bool:
    """
    Classifies one cell. Returns True if it`s taken, False if it is free
    """
    if not MODEL_LOAD_SUCCESS or classifier is None:
        rospy.logwarn_once("Classifier not found")
        return False

    features = extract_features(img)

    if features is None:
        return False

    try:
        features = features.reshape(1, -1)
        prediction = classifier.predict(features)[0]

        # 1 - "WITH PIECE", 0 - "EMPTY"
        return int(prediction) == 1

    except Exception as e:
        rospy.logerr(f"Error in is_occupied_classifier(): {e}")
        return False


class ChessVisionProcessor:
    """
    Procceses data from camera, sees the move that has beed done, sends FEN-line
    """
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        rospy.init_node('vision_node_processor', anonymous=False)
        load_classifier()

        self.board = chess.Board(initial_fen)
        # Initial occupied cells from FEN
        self.last_occupied_squares = self._get_occupied_squares_from_board(self.board)
        self.fen_publisher = rospy.Publisher('/chess_state/fen', String, queue_size=1)

        rospy.loginfo(f"ChessVisionProcessor initialised. FEN-publisher to /chess_state/fen.")
        rospy.loginfo(f"Starting FEN: {self.board.fen()}")

    def _get_occupied_squares_from_board(self, board_state: chess.Board) -> list:
        """Returns a list of occupied cells from chess.Board object"""
        occupied = []
        for i in range(64):
            sq_name = chess.square_name(i)
            # Checks if a piece is in the cell
            if board_state.piece_at(i) is not None:
                occupied.append(sq_name)
        return occupied

    def _classify_all_squares_to_occupied_list(self) -> list:
        """
        Reads 64 images of cells and returns a list of occupied cells
        """
        occupied_squares = []

        if not os.path.exists(CELLS_FOLDER):
            rospy.logwarn(f"Cells folder not found: {CELLS_FOLDER}")
            return []

        # Iterating through a1-h8
        for i in range(64):
            square_name = chess.square_name(i)
            filename = f"{square_name}.jpg"
            filepath = os.path.join(CELLS_FOLDER, filename)

            img = cv2.imread(filepath)

            if img is None:
                continue

            if is_occupied_classifier(img):
                occupied_squares.append(square_name)

        # rospy.loginfo(f"len(occupied_squares)} occupied cells")
        return occupied_squares

    def loop(self):
        """Main cycle"""
        rospy.loginfo("Starting vision processing cycle")
        rate = rospy.Rate(1) # Check 1 time every second, adjust

        if not MODEL_LOAD_SUCCESS:
            rospy.logfatal("Classifier not loaded. Stop")
            return

        while not rospy.is_shutdown():
            self.process_new_state()
            rate.sleep()

    def process_new_state(self):
        """
        1. Takes a new list of occupied cells
        2. Finds delta (dissepeared/appeared cells)
        3. Finds a legal move and does it
        """
        # Gets a new state of the board
        new_occupied_squares = self._classify_all_squares_to_occupied_list()

        if not new_occupied_squares and len(self.last_occupied_squares) > 0:
            rospy.logwarn_throttle(5, "New list of occupied cells is empty")
            return

        old_occupied_squares = self.last_occupied_squares

        if set(new_occupied_squares) == set(old_occupied_squares):
            # rospy.loginfo("Position remains the same. Waiting for the next reading")
            return

        rospy.loginfo("The position changed. Proceed to delta-tracking")

        # Find delta
        start_squares = sorted([sq for sq in old_occupied_squares if sq not in new_occupied_squares]) # Dissepeared
        end_squares = sorted([sq for sq in new_occupied_squares if sq not in old_occupied_squares])   # Appeared

        uci_move = None

        # Calculate a move
        if len(start_squares) == 1 and len(end_squares) == 1:
            # Simple move or a piece take
            candidate_move = f"{start_squares[0]}{end_squares[0]}"

            for move in self.board.legal_moves:
                if move.uci().startswith(candidate_move):
                    uci_move = move.uci()
                    break

            if uci_move:
                rospy.loginfo(f"Found a simple move/take of another piece (1-1): {uci_move}")
            else:
                rospy.logwarn(f"(1-1), but move {candidate_move} is not legal")

                # Pawn Promotion
                end_sq = end_squares[0]
                piece_to_move = self.board.piece_at(chess.parse_square(start_squares[0]))

                if piece_to_move and piece_to_move.piece_type == chess.PAWN and \
                        ((self.board.turn == chess.WHITE and end_sq[1] == '8') or \
                         (self.board.turn == chess.BLACK and end_sq[1] == '1')):

                    # All possible promotions (q, r, b, n)
                    for promo in ['q', 'r', 'b', 'n']:
                        promo_move = f"{candidate_move}{promo}"
                        try:
                            move = self.board.parse_uci(promo_move)
                            if move in self.board.legal_moves:
                                uci_move = promo_move
                                rospy.loginfo(f"Found a pawn promotion: {uci_move}")
                                break
                        except ValueError:
                            continue

                    if not uci_move:
                        rospy.logwarn("(1-1), but move is not legal")


        elif len(start_squares) == 2 and len(end_squares) == 2:
            # Castling (e1g1 / e1c1)
            for move in self.board.legal_moves:
                if self.board.is_castling(move):
                    uci_move = move.uci()
                    rospy.loginfo(f"Found castling (2-2): {uci_move}")
                    break

            if not uci_move:
                rospy.logwarn("(2-2), but not a legal move")

        else:
            rospy.logwarn(f"Couldn`t identify a move. Dissepeared={start_squares}, Appeared={end_squares}")
            return


        # Move making, publishing
        if uci_move:
            try:
                move = self.board.parse_uci(uci_move)

                if move in self.board.legal_moves:
                    self.board.push(move)
                    new_fen = self.board.fen()

                    self.last_occupied_squares = self._get_occupied_squares_from_board(self.board)

                    # Publish new FEN
                    msg = String()
                    msg.data = new_fen
                    self.fen_publisher.publish(msg)
                    rospy.loginfo(f"Made a move {uci_move}. Published FEN: {new_fen}")

                else:
                    rospy.logwarn(f"Move {uci_move} is illegal for FEN: {self.board.fen()}")

            except ValueError:
                rospy.logerr(f"Couldn`t detect a legal UCI move: {uci_move}.")

            except Exception as e:
                rospy.logerr(f"Couldn`t make a move {uci_move}: {e}")

        # if nothing was detected, wait for a new cycle


if __name__ == '__main__':
    try:
        processor = ChessVisionProcessor()
        processor.loop()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"Error: {e}")
