import React, { useState, useEffect } from 'react';
import { Crown, Swords, Globe, Bot, Users } from 'lucide-react';

const PIECE_IMAGES = {
  w: {
    k: '/pieces/white-king.png',
    q: '/pieces/white-queen.png',
    r: '/pieces/white-rook.png',
    b: '/pieces/white-bishop.png',
    n: '/pieces/white-knight.png',
    p: '/pieces/white-pawn.png'
  },
  b: {
    k: '/pieces/black-king.png',
    q: '/pieces/black-queen.png',
    r: '/pieces/black-rook.png',
    b: '/pieces/black-bishop.png',
    n: '/pieces/black-knight.png',
    p: '/pieces/black-pawn.png'
  }
};

const API_URL = 'http://localhost:8000';

function ChessApp() {
  const [gameMode, setGameMode] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [boardState, setBoardState] = useState(null);
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [legalMoves, setLegalMoves] = useState([]);
  const [aiElo, setAiElo] = useState(1500);
  const [aiType, setAiType] = useState('minimax');
  const [roomId, setRoomId] = useState('');
  const [ws, setWs] = useState(null);
  const [playerColor, setPlayerColor] = useState(null);
  const [playerName, setPlayerName] = useState('');
  const [showPromotionMenu, setShowPromotionMenu] = useState(false);
  const [pendingMove, setPendingMove] = useState(null);
  const [opponentJoined, setOpponentJoined] = useState(false);

  const createGame = async (mode) => {
    try {
      const response = await fetch(`${API_URL}/game/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      const data = await response.json();
      setGameId(data.game_id);
      setBoardState(data.state);
      setGameMode(mode);
    } catch (error) {
      console.error('Error creating game:', error);
    }
  };

  const getLegalMoves = async (x, y) => {
    try {
      let response;
      if (gameMode === 'online') {
        response = await fetch(`${API_URL}/room/${roomId}/legal_moves?x=${x}&y=${y}`);
      } else {
        response = await fetch(`${API_URL}/game/${gameId}/legal_moves?x=${x}&y=${y}`);
      }
      const data = await response.json();
      setLegalMoves(data.legal_moves);
    } catch (error) {
      console.error('Error getting legal moves:', error);
      setLegalMoves([]);
    }
  };

  const makeMove = async (fromX, fromY, toX, toY, promotion = null) => {
    try {
      const response = await fetch(`${API_URL}/game/${gameId}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_x: fromX, from_y: fromY, to_x: toX, to_y: toY, promotion })
      });
      const data = await response.json();
      
      if (data.promotion_needed) {
        setPendingMove({ fromX, fromY, toX, toY });
        setShowPromotionMenu(true);
        return;
      }

      setBoardState(data.state);
      setSelectedSquare(null);
      setLegalMoves([]);

      if (gameMode === 'ai' && data.state.turn === 'b') {
        setTimeout(() => getAIMove(), 500);
      }
    } catch (error) {
      console.error('Error making move:', error);
    }
  };

  const handlePromotion = async (piece) => {
    setShowPromotionMenu(false);
    if (pendingMove) {
      if (gameMode === 'online' && ws) {
        ws.send(JSON.stringify({
          type: 'move',
          from_x: pendingMove.fromX,
          from_y: pendingMove.fromY,
          to_x: pendingMove.toX,
          to_y: pendingMove.toY,
          promotion: piece
        }));
      } else {
        await makeMove(pendingMove.fromX, pendingMove.fromY, pendingMove.toX, pendingMove.toY, piece);
      }
      setPendingMove(null);
    }
  };

  const getAIMove = async () => {
    try {
      const response = await fetch(`${API_URL}/game/${gameId}/ai_move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ai_type: aiType,
          elo: aiElo,
          depth: aiType === 'minimax' ? aiElo : undefined 
        })
      });
      const data = await response.json();
      setBoardState(data.state);
    } catch (error) {
      console.error('Error getting AI move:', error);
    }
  };

  const handleSquareClick = (x, y) => {
    if (gameMode === 'online' && boardState?.turn !== playerColor) {
      return;
    }

    const piece = boardState?.board[y][x];

    if (selectedSquare) {
      const isLegalMove = legalMoves.some(move => move.x === x && move.y === y);
      if (isLegalMove) {
        if (gameMode === 'online' && ws) {
          ws.send(JSON.stringify({
            type: 'move',
            from_x: selectedSquare.x,
            from_y: selectedSquare.y,
            to_x: x,
            to_y: y,
            promotion: null
          }));
          setSelectedSquare(null);
          setLegalMoves([]);
        } else {
          makeMove(selectedSquare.x, selectedSquare.y, x, y);
        }
      } else if (piece && piece.color === boardState.turn) {
        setSelectedSquare({ x, y });
        getLegalMoves(x, y);
      } else {
        setSelectedSquare(null);
        setLegalMoves([]);
      }
    } else if (piece && piece.color === boardState?.turn) {
      setSelectedSquare({ x, y });
      getLegalMoves(x, y);
    }
  };

  const createRoom = async () => {
    try {
      const response = await fetch(`${API_URL}/room/create`, {
        method: 'POST'
      });
      const data = await response.json();
      setRoomId(data.room_id);
      setBoardState(data.state);
    } catch (error) {
      console.error('Error creating room:', error);
    }
  };

  const joinRoom = (name) => {
    const socket = new WebSocket(`ws://localhost:8000/ws/${roomId}/${name}`);
    
    socket.onopen = () => {
      console.log('Connected to room');
      setPlayerName(name);
      setGameMode('online');
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data);
      
      if (data.type === 'game_state') {
        // Receive initial board state
        setBoardState(data.state);
      } else if (data.type === 'player_joined') {
        if (data.player === name) {
          setPlayerColor(data.color);
        }
        // Check if both players are now in the room
        if (data.players && data.players.length === 2) {
          setOpponentJoined(true);
        }
      } else if (data.type === 'move_made') {
        setBoardState(data.state);
        setSelectedSquare(null);
        setLegalMoves([]);
      } else if (data.type === 'promotion_needed') {
        setPendingMove({ 
          fromX: data.from_x, 
          fromY: data.from_y, 
          toX: data.to_x, 
          toY: data.to_y 
        });
        setShowPromotionMenu(true);
      } else if (data.type === 'player_left') {
        setOpponentJoined(false);
        alert(`${data.player} has left the game`);
      }
    };

    socket.onclose = () => {
      console.log('Disconnected from room');
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(socket);
  };

  const renderSquare = (x, y) => {
    const piece = boardState?.board[y][x];
    const isLight = (x + y) % 2 === 0;
    const isSelected = selectedSquare?.x === x && selectedSquare?.y === y;
    const isLegalMove = legalMoves.some(move => move.x === x && move.y === y);

    return (
      <div
        key={`${x}-${y}`}
        onClick={() => handleSquareClick(x, y)}
        className={`
          aspect-square flex items-center justify-center cursor-pointer
          transition-all duration-200 relative
          ${isLight ? 'bg-white' : 'bg-[#00ffb3]'}
          ${isSelected ? 'ring-4 ring-yellow-400' : ''}
          hover:brightness-95
        `}
      >
        {piece && (
          <img
            src={PIECE_IMAGES[piece.color][piece.type]}
            alt={`${piece.color} ${piece.type}`}
            className="select-none w-5/6 h-5/6 object-contain pointer-events-none"
          />
        )}
        {isLegalMove && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className={`rounded-full ${piece ? 'w-14 h-14 border-4 border-blue-500' : 'w-3 h-3 bg-blue-500 bg-opacity-70'}`} />
          </div>
        )}
      </div>
    );
  };

  // Main menu
  if (!gameMode && !roomId) {
    return (
      <div className="h-screen overflow-hidden bg-black flex flex-col items-center justify-center">
        <h1 className="text-7xl font-bold text-white mb-16 select-none tracking-tight">
          Chess<span className="text-[#00ffb3]">2</span>
        </h1>

        <div className="flex flex-col gap-6">
          <button
            onClick={() => createGame('local')}
            className="text-white text-2xl hover:text-[#00ffb3] transition-colors duration-300 py-2"
          >
            Local Multiplayer
          </button>

          <button
            onClick={() => setGameMode('ai-setup')}
            className="text-white text-2xl hover:text-[#00ffb3] transition-colors duration-300 py-2"
          >
            Play vs AI
          </button>

          <button
            onClick={() => setGameMode('online-setup')}
            className="text-white text-2xl hover:text-[#00ffb3] transition-colors duration-300 py-2"
          >
            Online Multiplayer
          </button>
        </div>

        <p className="text-gray-600 text-xs mt-20 tracking-wide select-none">
          © 2025 Built with FastAPI + React
        </p>
      </div>
    );
  }

  // AI Setup
  if (gameMode === 'ai-setup') {
    return (
      <div className="h-screen overflow-hidden bg-black flex items-center justify-center">
        <div className="max-w-md w-full bg-gray-900 rounded-lg p-8 border border-gray-800">
          <h2 className="text-3xl font-bold text-white mb-6">Play vs AI</h2>
          
          {/* AI Type Selection */}
          <div className="mb-6">
            <label className="text-white text-lg mb-3 block">Choose AI Type:</label>
            <div className="space-y-2">
              <button
                onClick={() => {setAiType('minimax'); setAiElo(3); }}
                className={`w-full p-3 rounded-lg text-left transition-colors ${
                  aiType === 'minimax' 
                    ? 'bg-[#00ffb3] text-black' 
                    : 'bg-gray-800 text-white hover:bg-gray-700'
                }`}
              >
                <div className="font-bold">Minimax Algorithm</div>
                <div className="text-sm opacity-75">Classic algorithm. "Stockfish at home."</div>
              </button>
              
              <button
                onClick={() => { setAiType('stockfish'); setAiElo(1500); }}
                className={`w-full p-3 rounded-lg text-left transition-colors ${
                  aiType === 'stockfish' 
                    ? 'bg-[#00ffb3] text-black' 
                    : 'bg-gray-800 text-white hover:bg-gray-700'
                }`}
              >
                <div className="font-bold">Stockfish Engine</div>
                <div className="text-sm opacity-75">World-class chess engine</div>
              </button>
            </div>
          </div>

          {/* Difficulty Settings */}
          {aiType === 'stockfish' && (
            <div className="mb-6">
              <label className="text-white text-lg mb-2 block">ELO Rating: {aiElo}</label>
              <input
                type="range"
                min="800"
                max="2800"
                step="10"
                value={aiElo}
                onChange={(e) => setAiElo(parseInt(e.target.value))}
                className="w-full accent-[#00ffb3]"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>Beginner</span>
                <span>Intermediate</span>
                <span>Expert</span>
                <span>Master</span>
              </div>
            </div>
          )}
          
          {aiType === 'minimax' && (
            <div className="mb-6">
              <label className="text-white text-lg mb-2 block">Difficulty</label>
              <select
                value={aiElo}
                onChange={(e) => setAiElo(parseInt(e.target.value))}
                className="w-full bg-gray-800 text-white p-3 rounded-lg border border-gray-700 focus:border-[#00ffb3] focus:outline-none"
              >
                <option value="2">Easy (Depth 2)</option>
                <option value="3">Medium (Depth 3)</option>
                <option value="4">Hard (Depth 4)</option>
              </select>
            </div>
          )}

          <button
            onClick={() => createGame('ai')}
            className="w-full bg-[#00ffb3] hover:bg-[#00dd9a] text-black py-3 rounded-lg font-bold transition-colors"
          >
            Start Game
          </button>
          <button
            onClick={() => setGameMode(null)}
            className="w-full mt-3 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg transition-colors"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  // Online Setup
  if (gameMode === 'online-setup') {
    return (
      <div className="h-screen overflow-hidden bg-black flex items-center justify-center">
        <div className="max-w-md w-full bg-gray-900 rounded-lg p-8 border border-gray-800">
          <h2 className="text-3xl font-bold text-white mb-6">Online Multiplayer</h2>
          
          {!roomId ? (
            <>
              <button
                onClick={createRoom}
                className="w-full bg-[#00ffb3] hover:bg-[#00dd9a] text-black py-3 rounded-lg font-bold mb-4 transition-colors"
              >
                Create Room
              </button>
              <div className="text-center text-gray-500 my-4 text-sm">or</div>
              <input
                type="text"
                placeholder="Enter Room ID"
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg mb-4 border border-gray-700 focus:border-[#00ffb3] focus:outline-none"
              />
            </>
          ) : (
            <div className="text-center">
              <div className="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
                <div className="text-gray-500 text-sm mb-2">Room ID</div>
                <div className="text-2xl font-mono font-bold text-[#00ffb3]">{roomId}</div>
              </div>
              <input
                type="text"
                placeholder="Your Name"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                className="w-full bg-gray-800 text-white px-4 py-3 rounded-lg mb-4 border border-gray-700 focus:border-[#00ffb3] focus:outline-none"
              />
              <button
                onClick={() => joinRoom(playerName)}
                disabled={!playerName}
                className="w-full bg-[#00ffb3] hover:bg-[#00dd9a] text-black py-3 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Join Room
              </button>
            </div>
          )}
          
          <button
            onClick={() => { setGameMode(null); setRoomId(''); }}
            className="w-full mt-4 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg transition-colors"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  // Game board
  return (
    <div className="h-screen overflow-hidden bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-5xl">
        <div className="bg-gray-900 rounded-lg p-4 shadow-2xl border border-gray-800">
          {/* Header */}
          <div className="flex justify-between items-center mb-3">
            <div className="text-white">
              <div className="text-xl font-bold">
                {gameMode === 'ai' ? `🤖 AI (${aiElo} ELO)` : gameMode === 'online' ? `🌐 ${playerName}` : '♟️ Local Game'}
              </div>
              {gameMode === 'online' && (
                <div className="text-xs text-gray-500">
                  Playing as {playerColor === 'w' ? 'White' : 'Black'} • Room: {roomId}
                </div>
              )}
            </div>
            <div className="text-right">
              <div className={`text-lg font-bold ${boardState?.turn === 'w' ? 'text-white' : 'text-gray-400'}`}>
                {boardState?.turn === 'w' ? "White's Turn" : "Black's Turn"}
              </div>
              {boardState?.check && <div className="text-[#00ffb3] font-bold text-sm">CHECK!</div>}
              {boardState?.checkmate && <div className="text-[#00ffb3] font-bold text-xl">CHECKMATE!</div>}
            </div>
          </div>

          {/* Chess Board */}
          <div className="relative">
            <div className="grid grid-cols-8 border-4 border-black shadow-2xl aspect-square max-h-[70vh]">
              {Array.from({ length: 8 }, (_, y) =>
                Array.from({ length: 8 }, (_, x) => renderSquare(x, y))
              )}
            </div>
            
            {/* Waiting for Opponent Overlay */}
            {gameMode === 'online' && !opponentJoined && (
              <div className="absolute inset-0 bg-black bg-opacity-90 flex items-center justify-center rounded">
                <div className="text-center">
                  <div className="text-white text-2xl font-bold mb-4">Waiting for opponent...</div>
                  <div className="text-gray-400 text-sm mb-6">Share room code: <span className="text-[#00ffb3] font-mono text-lg">{roomId}</span></div>
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#00ffb3]"></div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Promotion Menu */}
            {showPromotionMenu && pendingMove && (
              <div className="absolute inset-0 bg-black bg-opacity-80 flex items-center justify-center rounded">
                <div className="bg-gray-900 rounded-lg p-6 shadow-2xl border-2 border-[#00ffb3]">
                  <h3 className="text-white text-xl font-bold mb-4 text-center">Promote Pawn</h3>
                  <div className="grid grid-cols-4 gap-4">
                    {['q', 'r', 'b', 'n'].map(piece => (
                      <button
                        key={piece}
                        onClick={() => handlePromotion(piece)}
                        className="bg-gray-800 hover:bg-gray-700 border-2 border-gray-700 hover:border-[#00ffb3] p-3 rounded-lg transition-all transform hover:scale-110 w-16 h-16 flex items-center justify-center"
                      >
                        <img
                          src={PIECE_IMAGES[boardState.turn][piece]}
                          alt={piece}
                          className="w-full h-full object-contain"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-3 flex gap-2 items-center">
            <button
              onClick={() => { setGameMode(null); setGameId(null); setBoardState(null); if (ws) ws.close(); }}
              className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              New Game
            </button>
            <div className="flex-1 text-right text-gray-500 text-sm">
              Move {boardState?.move_count || 1}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChessApp;