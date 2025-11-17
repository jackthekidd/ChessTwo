# ChessTwo
The long awaited sequel to the board game "Chess."
A web-based chess platform inspired by Chess.com and Lichess, except my version hasn't implemented en passant because I don't like it.
Supports local play, online multiplayer (work in progress), and AI opponents powered by Stockfish and minimax algorithms. 

---

## Overview
ChessTwo:
- **Frontend:** React + Vite + Tailwind CSS  
- **Backend:** Python (Flask or FastAPI planned)  
- **Planned Features:** AI play, matchmaking, rating system, and FEN-based board state tracking.

---

## Stack
| Layer | Technology |
|-------|-------------|
| Frontend | React, Vite, TailwindCSS, chess.js |
| Backend | Python (Flask / FastAPI), Socket.IO |
| Database (future) | PostgreSQL |
| Engine (future) | Stockfish (UCI protocol) |

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/jackthekidd/ChessTwo.git
cd ChessTwo

### 2. Frontend Setup
cd frontend
npm install
npm run dev

---

## 3. Backend Setup
cd backend
pip install -r requirements.txt
python main.py



### License
This project is open source under the MIT License.

### Author
Jack Seastrom
