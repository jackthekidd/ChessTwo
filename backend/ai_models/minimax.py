import copy
from chess_engine import ChessGame

# Piece value position tables, representing the value of a piece at a given position and time

PAWN_PST_MID = [
    0,   0,   0,   0,   0,   0,   0,   0,
   50,  50,  50,  50,  50,  50,  50,  50,
   10,  10,  20,  30,  30,  20,  10,  10,
    5,   5,  10,  25,  25,  10,   5,   5,
    0,   0,   0,  20,  20,   0,   0,   0,
    5,  -5, -10,   0,   0, -10,  -5,   5,
    5,  10,  10, -20, -20,  10,  10,   5,
    0,   0,   0,   0,   0,   0,   0,   0,
]

PAWN_PST_END = [
     0,   5,   5, -10, -10,   5,   5,   0,
     0,   5, - 5,   0,   0, - 5,   5,   0,
     0,   5,  10,  20,  20,  10,   5,   0,
     0,   5,  10,  25,  25,  10,   5,   0,
     0,   5,  10,  25,  25,  10,   5,   0,
     0,   5,  10,  20,  20,  10,   5,   0,
     0,   5, - 5,   0,   0, - 5,   5,   0,
     0,   5,   5, -10, -10,   5,   5,   0,
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_PST = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  5, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_PST_MID = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]

KING_PST_END = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
]

# Works for both colors:
def pst_value(table, x, y, color):
    idx = y * 8 + x
    if color == "w":
        return table[idx]
    else:
        mirrored_idx = (7 - y) * 8 + x
        return table[mirrored_idx]


# Meat and potatoes: Minimax or "Stockfish at home"
class MinimaxAI:
    def __init__(self, depth=3):
        self.depth = depth

    
    def get_best_move(self, game: ChessGame):

        color = game.turn

        best_score = float('-inf') if color == "w" else float('inf')
        best_move = None

        moves = self._ordered_moves(game)

        for (px, py, tx, ty) in moves:
            new_game = copy.deepcopy(game)
            new_game.make_move(px, py, tx, ty)

            score = self._minimax(
                new_game,
                depth=self.depth - 1,
                alpha=float('-inf'),
                beta=float('inf'),
                maximizing=(color == "w")
            )

            if color == "w":
                if score > best_score:
                    best_score = score
                    best_move = (px, py, tx, ty)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (px, py, tx, ty)

        return best_move

    # Move ordering
    def _ordered_moves(self, game):
        moves = []

        for p in game.pieces:
            if p.color == game.turn:
                for (tx, ty) in game.get_legal_moves(p.pos_x, p.pos_y):

                    # capture bonus ordering
                    capture = (game.board[ty][tx] is not None)
                    score_hint = 100 if capture else 0

                    moves.append((p.pos_x, p.pos_y, tx, ty, score_hint))

        # sort best-first for maximizing player
        reverse = (game.turn == "w")
        moves.sort(key=lambda m: m[4], reverse=reverse)

        return [(a, b, c, d) for a, b, c, d, _ in moves]

   # Alg
    def _minimax(self, game, depth, alpha, beta, maximizing):

        if depth == 0 or game.checkmate:
            return self._evaluate_board(game)

        moves = self._ordered_moves(game)

        if not moves:
            return self._evaluate_board(game)

        if maximizing:
            value = float('-inf')
            for (px, py, tx, ty) in moves:
                new_game = copy.deepcopy(game)
                new_game.make_move(px, py, tx, ty)
                value = max(value, self._minimax(new_game, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # beta cutoff
            return value
        else:
            value = float('inf')
            for (px, py, tx, ty) in moves:
                new_game = copy.deepcopy(game)
                new_game.make_move(px, py, tx, ty)
                value = min(value, self._minimax(new_game, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break  # alpha cutoff
            return value

    # EVAL
    def _evaluate_board(self, game):

        # MATERIAL
        piece_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900}

        material = 0
        pst_score = 0

        # Count total non-king material for endgame detection
        non_king_material = 0

        w_king = (game.king_w.pos_x, game.king_w.pos_y)
        b_king = (game.king_b.pos_x, game.king_b.pos_y)

        for piece in game.pieces:
            x, y = piece.pos_x, piece.pos_y
            color = piece.color

            if piece.type != "k":
                non_king_material += piece_values[piece.type]

            # Material Difference
            val = piece_values.get(piece.type, 0)
            material += val if color == "w" else -val

            # PST scoring
            if piece.type == "p":
                table_mid = PAWN_PST_MID
                table_end = PAWN_PST_END
            elif piece.type == "n":
                table_mid = KNIGHT_PST
                table_end = KNIGHT_PST
            elif piece.type == "b":
                table_mid = BISHOP_PST
                table_end = BISHOP_PST
            elif piece.type == "r":
                table_mid = ROOK_PST
                table_end = ROOK_PST
            elif piece.type == "q":
                table_mid = QUEEN_PST
                table_end = QUEEN_PST
            elif piece.type == "k":
                table_mid = KING_PST_MID
                table_end = KING_PST_END

            # Blends tables for time
            endgame = non_king_material < 1400
            if endgame:
                pst_score += pst_value(table_end, x, y, color) * (1 if color == "w" else -1)
            else:
                pst_score += pst_value(table_mid, x, y, color) * (1 if color == "w" else -1)

        # King endgame motivation to move toward opposing king
        if non_king_material < 1400:
            wx, wy = w_king
            bx, by = b_king
            dist = abs(wx - bx) + abs(wy - by)
            mop_up = (14 - dist) * 10
            pst_score += mop_up

        return material + pst_score
