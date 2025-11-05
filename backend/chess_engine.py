"""
Python chess engine
"""

class Piece:
    def __init__(self, color, piece_type, pos_x, pos_y, has_moved=0):
        self.color = color  # 'w' or 'b'
        self.type = piece_type  # 'p', 'r', 'n', 'b', 'q', 'k'
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.has_moved = has_moved
        
    def to_dict(self):
        """For JSON response"""
        return {
            'color': self.color,
            'type': self.type,
            'pos_x': self.pos_x,
            'pos_y': self.pos_y,
            'has_moved': self.has_moved
        }


class ChessGame:
    def __init__(self, start_fen=None):
        self.turn = "w"
        self.check = False
        self.checkmate = False
        self.move_count = 1
        
        # Castling rights
        self.w_can_castle_k = True
        self.w_can_castle_q = True
        self.b_can_castle_k = True
        self.b_can_castle_q = True
        
        # Init board
        self.board = [[None for _ in range(8)] for _ in range(8)]
        
        self.pieces = []
        self.king_w = None
        self.king_b = None
        
        fen = start_fen if start_fen else self.default_fen()
        self.load_from_fen(fen)
        
        
    def default_fen(self):
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    
    def load_from_fen(self, fen):
        """Loads board state from FEN string"""
        parts = fen.split()
        board_part = parts[0]
        
        char_to_piece = {
            "r": "rook", "n": "knight", "b": "bishop", 
            "q": "queen", "k": "king", "p": "pawn"
        }
        
        rows = board_part.split("/")
        self.pieces = []
        
        for row_index, row in enumerate(rows):
            col_index = 0
            for char in row:
                if char.isdigit():
                    col_index += int(char)
                else:
                    piece_color = "w" if char.isupper() else "b"
                    piece_type = char.lower()
                    
                    piece = Piece(piece_color, piece_type, col_index, row_index)
                    self.pieces.append(piece)
                    self.board[row_index][col_index] = piece
                    
                    if piece_type == "k":
                        if piece_color == "w":
                            self.king_w = piece
                        else:
                            self.king_b = piece
                    
                    col_index += 1
        
        if len(parts) >= 2:
            self.turn = parts[1]
            
        if len(parts) >= 3:
            castling = parts[2]
            self.w_can_castle_k = 'K' in castling
            self.w_can_castle_q = 'Q' in castling
            self.b_can_castle_k = 'k' in castling
            self.b_can_castle_q = 'q' in castling
            
        if len(parts) >= 6:
            self.move_count = int(parts[5])
    
    
    def to_fen(self):
        """Convert current board state to FEN string"""
        fen = ""
        for row in self.board:
            empty = 0
            for square in row:
                if square is None:
                    empty += 1
                else:
                    if empty:
                        fen += str(empty)
                        empty = 0
                    symbol = square.type.upper() if square.color == "w" else square.type.lower()
                    fen += symbol
            if empty:
                fen += str(empty)
            fen += "/"
        fen = fen[:-1]
        
        castling_rights = ""
        if self.w_can_castle_k:
            castling_rights += "K"
        if self.w_can_castle_q:
            castling_rights += "Q"
        if self.b_can_castle_k:
            castling_rights += "k"
        if self.b_can_castle_q:
            castling_rights += "q"
        if not castling_rights:
            castling_rights = "-"
        
        fen += f" {self.turn} {castling_rights} - 0 {self.move_count}"
        return fen
    
    
    def get_legal_moves(self, from_x, from_y):
        """Gets all legal moves for a given piece at (from_x, from_y)"""
        piece = self.board[from_y][from_x]
        if piece is None or piece.color != self.turn:
            return []
        
        moves = []
        
        if piece.type == "p":
            moves = self._get_pawn_moves(from_x, from_y)
        elif piece.type == "r":
            moves = self._get_rook_moves(from_x, from_y)
        elif piece.type == "n":
            moves = self._get_knight_moves(from_x, from_y)
        elif piece.type == "b":
            moves = self._get_bishop_moves(from_x, from_y)
        elif piece.type == "q":
            moves = self._get_queen_moves(from_x, from_y)
        elif piece.type == "k":
            moves = self._get_king_moves(from_x, from_y)
        
        # Filter out moves that leave king in check
        legal_moves = []
        for to_x, to_y in moves:
            if self._is_legal_move(from_x, from_y, to_x, to_y):
                legal_moves.append((to_x, to_y))
        
        return legal_moves
    
    
    def _get_pawn_moves(self, x, y):
        piece = self.board[y][x]
        moves = []
        direction = -1 if piece.color == "w" else 1
        
        # Forward move
        if 0 <= y + direction < 8 and self.board[y + direction][x] is None:
            moves.append((x, y + direction))
            
            # Double move from starting position
            if piece.has_moved == 0:
                if 0 <= y + 2 * direction < 8 and self.board[y + 2 * direction][x] is None:
                    moves.append((x, y + 2 * direction))
        
        # Captures
        for dx in [-1, 1]:
            new_x, new_y = x + dx, y + direction
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target = self.board[new_y][new_x]
                if target is not None and target.color != piece.color:
                    moves.append((new_x, new_y))
        
        return moves
    
    
    def _get_rook_moves(self, x, y):
        return self._get_sliding_moves(x, y, [(0, 1), (1, 0), (0, -1), (-1, 0)])
    
    
    def _get_bishop_moves(self, x, y):
        return self._get_sliding_moves(x, y, [(1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    
    def _get_queen_moves(self, x, y):
        return self._get_sliding_moves(x, y, [(0, 1), (1, 0), (0, -1), (-1, 0), 
                                               (1, 1), (1, -1), (-1, 1), (-1, -1)])
    
    
    def _get_sliding_moves(self, x, y, directions):
        piece = self.board[y][x]
        moves = []
        
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            while 0 <= new_x < 8 and 0 <= new_y < 8:
                target = self.board[new_y][new_x]
                if target is None:
                    moves.append((new_x, new_y))
                else:
                    if target.color != piece.color:
                        moves.append((new_x, new_y))
                    break
                new_x += dx
                new_y += dy
        
        return moves
    
    
    def _get_knight_moves(self, x, y):
        piece = self.board[y][x]
        moves = []
        knight_moves = [(1, 2), (1, -2), (-1, 2), (-1, -2), 
                       (2, 1), (2, -1), (-2, 1), (-2, -1)]
        
        for dx, dy in knight_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target = self.board[new_y][new_x]
                if target is None or target.color != piece.color:
                    moves.append((new_x, new_y))
        
        return moves
    
    
    def _get_king_moves(self, x, y):
        piece = self.board[y][x]
        moves = []
        
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), 
                     (0, 1), (1, -1), (1, 0), (1, 1)]
        
        for dx, dy in king_moves:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 8 and 0 <= new_y < 8:
                target = self.board[new_y][new_x]
                if target is None or target.color != piece.color:
                    moves.append((new_x, new_y))
        
        # Castling
        if piece.has_moved == 0:
            moves.extend(self._get_castling_moves(x, y))
        
        return moves
    
    
    def _get_castling_moves(self, x, y):
        moves = []
        king = self.board[y][x]
        
        # Kingside castling
        if king.color == "w" and self.w_can_castle_k:
            if (self.board[7][5] is None and self.board[7][6] is None):
                rook = self.board[7][7]
                if rook and rook.type == "r" and rook.has_moved == 0:
                    if (not self._is_square_attacked(5, 7, "b") and
                        not self._is_square_attacked(6, 7, "b")):
                        moves.append((6, 7))

        elif king.color == "b" and self.b_can_castle_k:
            if (self.board[0][5] is None and self.board[0][6] is None):
                rook = self.board[0][7]
                if rook and rook.type == "r" and rook.has_moved == 0:
                    if (not self._is_square_attacked(5, 0, "w") and
                        not self._is_square_attacked(6, 0, "w")):
                        moves.append((6, 0))
        
        # Queenside castling
        if king.color == "w" and self.w_can_castle_q:
            if (self.board[7][1] is None and self.board[7][2] is None and self.board[7][3] is None):
                rook = self.board[7][0]
                if rook and rook.type == "r" and rook.has_moved == 0:
                    if (not self._is_square_attacked(3, 7, "b") and
                        not self._is_square_attacked(2, 7, "b")):
                        moves.append((2, 7))

        elif king.color == "b" and self.b_can_castle_q:
            if (self.board[0][1] is None and self.board[0][2] is None and self.board[0][3] is None):
                rook = self.board[0][0]
                if rook and rook.type == "r" and rook.has_moved == 0:
                    if (not self._is_square_attacked(3, 0, "w") and
                        not self._is_square_attacked(2, 0, "w")):
                        moves.append((2, 0))

        return moves
       
        
    def _is_square_attacked(self, x, y, by_color):
        """Check if square (x, y) is attacked by pieces of color by_color"""
        opponent_color = "b" if by_color == "w" else "w"
        
        for piece in self.pieces:
            if piece.color == by_color:
                # Get raw moves without checking for pins
                if piece.type == "p":
                    direction = -1 if piece.color == "w" else 1
                    for dx in [-1, 1]:
                        if piece.pos_x + dx == x and piece.pos_y + direction == y:
                            return True
                else:
                    attacks = self._get_piece_attacks(piece.pos_x, piece.pos_y)
                    if (x, y) in attacks:
                        return True
        return False
    
    
    def _get_piece_attacks(self, x, y):
        """Get all squares attacked by piece at (x, y) - doesn't check legality"""
        piece = self.board[y][x]
        if piece is None:
            return []
        
        if piece.type == "n":
            return self._get_knight_moves(x, y)
        elif piece.type == "b":
            return self._get_bishop_moves(x, y)
        elif piece.type == "r":
            return self._get_rook_moves(x, y)
        elif piece.type == "q":
            return self._get_queen_moves(x, y)
        elif piece.type == "k":
            moves = []
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), 
                          (0, 1), (1, -1), (1, 0), (1, 1)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < 8 and 0 <= new_y < 8:
                    moves.append((new_x, new_y))
            return moves
        return []
    
    
    def _is_legal_move(self, from_x, from_y, to_x, to_y):
        """Check if move is legal (doesn't leave own king in check)"""
        piece = self.board[from_y][from_x]
        captured = self.board[to_y][to_x]
        
        # Temporarily take off captured piece from pieces 
        if captured and captured in self.pieces:
            self.pieces.remove(captured)
        
        # Simulate the move
        self.board[to_y][to_x] = piece
        self.board[from_y][from_x] = None
        old_x, old_y = piece.pos_x, piece.pos_y
        piece.pos_x, piece.pos_y = to_x, to_y
        
        # Check if king is safe
        king = self.king_w if piece.color == "w" else self.king_b
        is_legal = not self._is_square_attacked(king.pos_x, king.pos_y, 
                                                "b" if piece.color == "w" else "w")
        
        # Undo the temp move
        self.board[from_y][from_x] = piece
        self.board[to_y][to_x] = captured
        piece.pos_x, piece.pos_y = old_x, old_y
        
        # Put captured piece back in pieces list
        if captured and captured not in self.pieces:
            self.pieces.append(captured)
        
        return is_legal
    
    
    def make_move(self, from_x, from_y, to_x, to_y, promotion_piece=None):
        """Executes a move and updates state"""
        piece = self.board[from_y][from_x]
        if piece is None or piece.color != self.turn:
            return False
        
        legal_moves = self.get_legal_moves(from_x, from_y)
        if (to_x, to_y) not in legal_moves:
            return False
        
        # Check if pawn promotion is needed but not provided
        if piece.type == "p" and (to_y == 0 or to_y == 7):
            if promotion_piece is None:
                return "promotion_needed"
            if promotion_piece not in ['q', 'r', 'b', 'n']:
                return False
        
        # Castling
        if piece.type == "k" and abs(to_x - from_x) == 2:
            self._execute_castling(from_x, from_y, to_x, to_y)
        else:
            # Regular
            captured = self.board[to_y][to_x]
            if captured:
                if captured.type == "k":
                    return False
                self.pieces.remove(captured)
            
            self.board[to_y][to_x] = piece
            self.board[from_y][from_x] = None
            piece.pos_x, piece.pos_y = to_x, to_y
            piece.has_moved = 1
            
            # Handles pawn promotion
            if piece.type == "p" and (to_y == 0 or to_y == 7):
                self._promote_pawn(piece, promotion_piece)
        
        # Update castling rights
        if piece.type == "k":
            if piece.color == "w":
                self.w_can_castle_k = False
                self.w_can_castle_q = False
            else:
                self.b_can_castle_k = False
                self.b_can_castle_q = False
        elif piece.type == "r":
            if piece.color == "w":
                if from_x == 0 and from_y == 7:
                    self.w_can_castle_q = False
                elif from_x == 7 and from_y == 7:
                    self.w_can_castle_k = False
            else:
                if from_x == 0 and from_y == 0:
                    self.b_can_castle_q = False
                elif from_x == 7 and from_y == 0:
                    self.b_can_castle_k = False
        
        # Handle turns
        self.turn = "b" if self.turn == "w" else "w"
        if self.turn == "w":
            self.move_count += 1
        
        # Check for m8
        self._update_game_status()
        
        return True
    
    
    def _execute_castling(self, from_x, from_y, to_x, to_y):
        """Castles"""
        king = self.board[from_y][from_x]
        
        # Move king
        self.board[to_y][to_x] = king
        self.board[from_y][from_x] = None
        king.pos_x, king.pos_y = to_x, to_y
        king.has_moved = 1
        
        # Move rook
        if to_x > from_x:  # Kingside
            rook = self.board[from_y][7]
            self.board[from_y][5] = rook
            self.board[from_y][7] = None
            rook.pos_x = 5
        else:  # Queenside
            rook = self.board[from_y][0]
            self.board[from_y][3] = rook
            self.board[from_y][0] = None
            rook.pos_x = 3
        
        rook.has_moved = 1
    
    
    def _promote_pawn(self, pawn, promotion_piece):
        """Promotes a pawn to the chosen piece"""
        # Remove old pawn from pieces list
        if pawn in self.pieces:
            self.pieces.remove(pawn)
        
        # Create new piece
        new_piece = Piece(pawn.color, promotion_piece, pawn.pos_x, pawn.pos_y, has_moved=1)
        self.board[pawn.pos_y][pawn.pos_x] = new_piece
        self.pieces.append(new_piece)
        
        
    def _update_game_status(self):
        """Update check and checkmate status"""
        king = self.king_w if self.turn == "w" else self.king_b
        opponent_color = "b" if self.turn == "w" else "w"
        
        self.check = self._is_square_attacked(king.pos_x, king.pos_y, opponent_color)
        
        if self.check:
            # Check if anymore legal moves exist
            has_legal_move = False
            for piece in self.pieces:
                if piece.color == self.turn:
                    if self.get_legal_moves(piece.pos_x, piece.pos_y):
                        has_legal_move = True
                        break
            self.checkmate = not has_legal_move
        else:
            self.checkmate = False
    
    
    def get_board_state(self):
        """Return full board state for API response"""
        return {
            'board': [[piece.to_dict() if piece else None for piece in row] 
                     for row in self.board],
            'turn': self.turn,
            'check': self.check,
            'checkmate': self.checkmate,
            'fen': self.to_fen(),
            'move_count': self.move_count
        }

