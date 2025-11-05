import copy
from chess_engine import ChessGame

class MinimaxAI:
    def __init__(self, depth=3):
        self.depth = depth

    def get_best_move(self, game: ChessGame):
        best_score = float('-inf')
        best_move = None

        # Go through all moves for current player
        for piece in game.pieces:
            if piece.color != game.turn:
                continue

            for to_x, to_y in game.get_legal_moves(piece.pos_x, piece.pos_y):
                # Clone the game so we don't mutate original
                new_game = copy.deepcopy(game)
                new_game.make_move(piece.pos_x, piece.pos_y, to_x, to_y)

                score = self._minimax(new_game, self.depth - 1, float('-inf'), float('inf'), False)
                if score > best_score:
                    best_score = score
                    best_move = (piece.pos_x, piece.pos_y, to_x, to_y)

        return best_move

    def _minimax(self, game, depth, alpha, beta, maximizing):
        if depth == 0 or game.checkmate:
            return self._evaluate_board(game)

        if maximizing:
            max_eval = float('-inf')
            for piece in game.pieces:
                if piece.color != game.turn:
                    continue
                for to_x, to_y in game.get_legal_moves(piece.pos_x, piece.pos_y):
                    new_game = copy.deepcopy(game)
                    new_game.make_move(piece.pos_x, piece.pos_y, to_x, to_y)
                    eval = self._minimax(new_game, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
            return max_eval
        else:
            min_eval = float('inf')
            for piece in game.pieces:
                if piece.color != game.turn:
                    continue
                for to_x, to_y in game.get_legal_moves(piece.pos_x, piece.pos_y):
                    new_game = copy.deepcopy(game)
                    new_game.make_move(piece.pos_x, piece.pos_y, to_x, to_y)
                    eval = self._minimax(new_game, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
            return min_eval

    def _evaluate_board(self, game):
        piece_values = {'p':1, 'n':3, 'b':3, 'r':5, 'q':9, 'k':0}
        score = 0
        for piece in game.pieces:
            value = piece_values[piece.type]
            if piece.color == 'w':
                score += value
            else:
                score -= value
        
        print(f"EVAL ({game.turn}): {score}")
        return score
