"""
FastAPI Backend used for chess app
main handles game management, Stockfish AI, and WebSocket multiplayer
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import uuid
import asyncio
from chess_engine import ChessGame
import chess
import chess.engine
from ai_models.minimax import MinimaxAI

app = FastAPI(title="Chess API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory game storage 
games: Dict[str, ChessGame] = {}
multiplayer_rooms: Dict[str, dict] = {}  # room_id -> {game, players, connections}

# Stockfish 
STOCKFISH_PATH = "C:/Users/cagem/Desktop/stockfish/stockfish/stockfish-windows-x86-64-avx2.exe" 


# Request/Response Models
class CreateGameRequest(BaseModel):
    mode: str  # "local", "ai", "online"
    fen: Optional[str] = None

class MoveRequest(BaseModel):
    from_x: int
    from_y: int
    to_x: int
    to_y: int
    promotion: Optional[str] = None # 'q', 'r', 'b', 'n'

class AIMoveRequest(BaseModel):
    ai_type: str = "stockfish"
    elo: int = 1500  
    depth: int = 5


# REST Endpoints

@app.get("/")
async def root():
    return {"message": "Chess API Server", "version": "1.0"}


@app.post("/game/create")
async def create_game(request: CreateGameRequest):
    """Create a new game"""
    game_id = str(uuid.uuid4())
    game = ChessGame(start_fen=request.fen)
    games[game_id] = game
    
    return {
        "game_id": game_id,
        "mode": request.mode,
        "state": game.get_board_state()
    }


@app.get("/game/{game_id}")
async def get_game(game_id: str):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return games[game_id].get_board_state()


@app.post("/game/{game_id}/move")
async def make_move(game_id: str, move: MoveRequest):
    """Make a move in the game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    success = game.make_move(move.from_x, move.from_y, move.to_x, move.to_y, move.promotion)
    
    if success == "promotion_needed":
        return {
            "promotion_needed": True,
            "state": game.get_board_state()
        }
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid move")
    
    return {
        "success": True,
        "state": game.get_board_state()
    }


@app.get("/game/{game_id}/legal_moves")
async def get_legal_moves(game_id: str, x: int, y: int):
    """Get legal moves for a piece"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    moves = game.get_legal_moves(x, y)
    
    return {"legal_moves": [{"x": mx, "y": my} for mx, my in moves]}


@app.post("/game/{game_id}/ai_move")
async def get_ai_move(game_id: str, ai_request: AIMoveRequest):
    """Get AI move from selected AI type"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    try:
        if ai_request.ai_type == "minimax":
            # Use Minimax AI
            print(f"Using Minimax with depth={ai_request.depth}")  # DEBUG
            
            
            ai = MinimaxAI(depth=ai_request.depth)
            move = ai.get_best_move(game)
            
            if move is None:
                print("ERROR: Minimax returned None!")  # DEBUG
                raise HTTPException(status_code=500, detail="Minimax returned no legal moves")
            
            from_x, from_y, to_x, to_y = move
            
        elif ai_request.ai_type == "stockfish":
            # Use Stockfish (your existing code)
            board = chess.Board(game.to_fen())
            transport, engine = await chess.engine.popen_uci(STOCKFISH_PATH)
            skill_level = min(20, max(0, (ai_request.elo - 800) // 100))
            await engine.configure({"Skill Level": skill_level})
            result = await engine.play(board, chess.engine.Limit(time=1.0))
            await engine.quit()
            
            move = result.move
            from_square = chess.square_name(move.from_square)
            to_square = chess.square_name(move.to_square)
            from_x = ord(from_square[0]) - ord('a')
            from_y = 8 - int(from_square[1])
            to_x = ord(to_square[0]) - ord('a')
            to_y = 8 - int(to_square[1])     
        
        else:
            raise HTTPException(status_code=400, detail="Invalid AI type")
        
        # Make the move
        success = game.make_move(from_x, from_y, to_x, to_y)
        
        if not success:
            raise HTTPException(status_code=500, detail="AI generated invalid move")
        
        return {
            "from_x": from_x,
            "from_y": from_y,
            "to_x": to_x,
            "to_y": to_y,
            "state": game.get_board_state()
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@app.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """Delete a game"""
    if game_id in games:
        del games[game_id]
    return {"success": True}


# ===== WebSocket for Multiplayer =====

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def broadcast(self, message: dict, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()


@app.post("/room/create")
async def create_room():
    """Create a multiplayer room"""
    room_id = str(uuid.uuid4())[:8]  # had to shorten ID for easier sharing
    game = ChessGame()
    
    multiplayer_rooms[room_id] = {
        "game": game,
        "players": [],
        "player_colors": {}
    }
    
    return {
        "room_id": room_id,
        "state": game.get_board_state()
    }

@app.get("/room/{room_id}/legal_moves")
async def get_room_legal_moves(room_id: str, x: int, y: int):
    """Get legal moves for a piece in a multiplayer room"""
    if room_id not in multiplayer_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    game = multiplayer_rooms[room_id]["game"]
    moves = game.get_legal_moves(x, y)
    
    return {"legal_moves": [{"x": mx, "y": my} for mx, my in moves]}

@app.websocket("/ws/{room_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    """WebSocket connection for multiplayer"""
    
    if room_id not in multiplayer_rooms:
        await websocket.close(code=404)
        return
    
    await manager.connect(websocket, room_id)
    room = multiplayer_rooms[room_id]
    
    # Assign color to player
    if len(room["players"]) == 0:
        room["player_colors"][player_name] = "w"
    elif len(room["players"]) == 1:
        room["player_colors"][player_name] = "b"
    else:
        await websocket.close(code=403)  # Room full
        return
    
    room["players"].append(player_name)
    
    # Send initial board state to the joining player
    await websocket.send_json({
        "type": "game_state",
        "state": room["game"].get_board_state()
    })
    
    # Notify all players
    await manager.broadcast({
        "type": "player_joined",
        "player": player_name,
        "color": room["player_colors"][player_name],
        "players": room["players"]
    }, room_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "move":
                # Verify it's the player's turn
                game = room["game"]
                player_color = room["player_colors"][player_name]
                
                if game.turn != player_color:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Not your turn"
                    })
                    continue
                
                # Make the move
                promotion = data.get("promotion", None)
                success = game.make_move(
                    data["from_x"], data["from_y"],
                    data["to_x"], data["to_y"],
                    promotion
                )
                
                if success:
                    # Broadcast move to all players
                    await manager.broadcast({
                        "type": "move_made",
                        "player": player_name,
                        "from_x": data["from_x"],
                        "from_y": data["from_y"],
                        "to_x": data["to_x"],
                        "to_y": data["to_y"],
                        "state": game.get_board_state()
                    }, room_id)
                elif success == "promotion_needed":
                    await websocket.send_json({
                        "type": "promotion_needed",
                        "from_x": data["from_x"],
                        "from_y": data["from_y"],
                        "to_x": data["to_x"],
                        "to_y": data["to_y"]
                    })
                    continue
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid move"
                    })
            
            elif data["type"] == "chat":
                await manager.broadcast({
                    "type": "chat",
                    "player": player_name,
                    "message": data["message"]
                }, room_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        room["players"].remove(player_name)
        
        await manager.broadcast({
            "type": "player_left",
            "player": player_name
        }, room_id)
        
        # Clean up empty rooms
        if not room["players"]:
            del multiplayer_rooms[room_id]
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_id)
        if player_name in room["players"]:
            room["players"].remove(player_name)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)