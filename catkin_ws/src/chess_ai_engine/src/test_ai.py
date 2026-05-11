import chess_ai

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MID_GAME_FEN = "r1b2rk1/pp1n1ppp/1q2p3/2b5/8/3BBN2/PPP2PPP/R2Q1RK1 b - - 0 12"

def run_sync_test(fen_string, test_name, time_limit=0.5):
    print(f"\n=== {test_name} ===")
    ai_engine = chess_ai.ChessAI(stockfish_path="/usr/games/stockfish")

    if not ai_engine.connect_engine():
        return

    if not ai_engine.set_position(fen_string):
        ai_engine.quit_engine()
        return

    print(ai_engine.board)
    best_move = ai_engine.get_best_move(time_limit=time_limit)

    if best_move:
        print(f"\nFound teh move: {best_move}")
    else:
        print("Couldn`t find the move")

    ai_engine.quit_engine()

if __name__ == "__main__":
    run_sync_test(START_FEN, "Starting position", time_limit=0.1)
    run_sync_test(MID_GAME_FEN, "Midgame", time_limit=0.5)

