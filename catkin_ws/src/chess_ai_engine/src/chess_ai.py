import chess
import chess.engine
import os
import sys

class ChessAI:
    def __init__(self, stockfish_path="/usr/games/stockfish"):
        self.stockfish_path = stockfish_path
        self.board = chess.Board() 
        self.engine = None

    def connect_engine(self):
        """Connects to Stockfish"""
        if not os.path.exists(self.stockfish_path):
            print(f"Stokfish not found for {self.stockfish_path}")
            sys.exit(1)
            
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            return True
        except Exception as e:
            print(f"Erorr in stockfish connection: {e}")
            self.engine = None
            return False

    def set_position(self, fen: str):
        try:
            self.board = chess.Board(fen)
            return True
        except ValueError:
            print(f"Error in FEN: {fen}")
            return False

    def get_best_move(self, time_limit=0.5) -> str:
        """Calculates the best move"""
        if self.engine is None or self.board.is_game_over():
            return None

        limit = chess.engine.Limit(time=time_limit)
        
        try:
            result = self.engine.play(self.board, limit)
            return result.move.uci() 
        except Exception as e:
            print(f"Error while caluclating a move: {e}")
            return None

    def quit_engine(self):
        if self.engine:
            self.engine.quit()
