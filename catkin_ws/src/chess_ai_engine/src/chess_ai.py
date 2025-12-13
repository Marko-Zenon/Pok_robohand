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
        """Синхронне підключення до рушія Stockfish."""
        if not os.path.exists(self.stockfish_path):
            print(f"❌ Помилка: Stockfish не знайдено за шляхом: {self.stockfish_path}")
            sys.exit(1)
            
        try:
            # === СИНХРОННЕ ПІДКЛЮЧЕННЯ ===
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            return True
        except Exception as e:
            print(f"❌ Помилка підключення до Stockfish: {e}")
            self.engine = None
            return False

    def set_position(self, fen: str):
        # (Залишається без змін)
        try:
            self.board = chess.Board(fen)
            return True
        except ValueError:
            print(f"❌ Помилка: Невірний формат FEN: {fen}")
            return False

    def get_best_move(self, time_limit=0.5) -> str: # !!! СИНХРОННИЙ МЕТОД
        """Обчислює найкращий хід синхронно."""
        if self.engine is None or self.board.is_game_over():
            return None

        limit = chess.engine.Limit(time=time_limit)
        
        try:
            # === СИНХРОННИЙ ВИКЛИК .play ===
            result = self.engine.play(self.board, limit)
            return result.move.uci() 
        except Exception as e:
            print(f"❌ Помилка при розрахунку ходу: {e}")
            return None

    def quit_engine(self): # !!! СИНХРОННИЙ МЕТОД
        """Закриває рушій синхронно."""
        if self.engine:
            self.engine.quit() # !!! БЕЗ await
