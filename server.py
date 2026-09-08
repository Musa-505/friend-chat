#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Friend Chat server — FastAPI + WebSocket + SQLite.

REST API + real-time push. Run:  python3 server.py  (uvicorn on :8000)
"""
import asyncio
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "friendchat.db"
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="Friend Chat")


# ---------------------------------------------------------------- DB helpers
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS friends (
                user_id TEXT NOT NULL,
                friend_id TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, friend_id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_id, id);
            """
        )


def get_user_by_token(token: str):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: str):
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------- WebSocket
# user_id -> WebSocket
connections: dict[str, WebSocket] = {}


async def push_to_user(user_id: str, payload: dict):
    ws = connections.get(user_id)
    if ws is not None:
        try:
            await ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            connections.pop(user_id, None)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, token: str = ""):
    user = get_user_by_token(token)
    if not user:
        await websocket.close(code=4001, reason="invalid token")
        return
    await websocket.accept()
    connections[user["id"]] = websocket
    try:
        while True:
            # keep alive; client may send ping
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections.pop(user["id"], None)


# ---------------------------------------------------------------- Models
class RegisterIn(BaseModel):
    name: str


class FriendIn(BaseModel):
    friend_id: str
    name: str = ""


class MessageIn(BaseModel):
    to_id: str
    text: str


# ---------------------------------------------------------------- Auth dep
def require_user(x_token: str = Header(default="")):
    user = get_user_by_token(x_token)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный токен. Сначала зарегистрируйтесь.")
    return user


# ---------------------------------------------------------------- REST API
@app.post("/api/register")
def register(body: RegisterIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")
    user_id = "u_" + secrets.token_hex(4)
    token = secrets.token_hex(16)
    with db() as conn:
        conn.execute(
            "INSERT INTO users (id, name, token, created_at) VALUES (?,?,?,?)",
            (user_id, name, token, int(time.time())),
        )
    return {"user_id": user_id, "token": token, "name": name}


@app.get("/api/me")
def me(user=Depends(require_user)):
    return {"user_id": user["id"], "name": user["name"]}


@app.post("/api/friends")
def add_friend(body: FriendIn, user=Depends(require_user)):
    friend = get_user_by_id(body.friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Пользователь с таким ID не найден")
    if friend["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="Нельзя добавить самого себя")
    name = body.name.strip() or friend["name"]
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO friends (user_id, friend_id, name, created_at) VALUES (?,?,?,?)",
            (user["id"], friend["id"], name, int(time.time())),
        )
    return {"friend_id": friend["id"], "name": name}


@app.get("/api/friends")
def list_friends(user=Depends(require_user)):
    with db() as conn:
        rows = conn.execute(
            "SELECT f.friend_id, f.name, u.name AS real_name FROM friends f "
            "JOIN users u ON u.id = f.friend_id WHERE f.user_id=? ORDER BY f.name",
            (user["id"],),
        ).fetchall()
    return [{"friend_id": r["friend_id"], "name": r["name"] or r["real_name"]} for r in rows]


@app.post("/api/messages")
async def send_message(body: MessageIn, user=Depends(require_user)):
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    if not get_user_by_id(body.to_id):
        raise HTTPException(status_code=404, detail="Получатель не найден")
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (from_id, to_id, text, created_at) VALUES (?,?,?,?)",
            (user["id"], body.to_id, text, int(time.time())),
        )
        msg_id = cur.lastrowid
    payload = {
        "type": "message",
        "id": msg_id,
        "from_id": user["id"],
        "from_name": user["name"],
        "to_id": body.to_id,
        "text": text,
        "created_at": int(time.time()),
    }
    await push_to_user(body.to_id, payload)
    return payload


@app.get("/api/messages")
def get_messages(since: int = 0, user=Depends(require_user)):
    with db() as conn:
        rows = conn.execute(
            "SELECT m.*, u.name AS from_name FROM messages m "
            "JOIN users u ON u.id = m.from_id "
            "WHERE m.id > ? AND (m.from_id=? OR m.to_id=?) "
            "ORDER BY m.id",
            (since, user["id"], user["id"]),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "from_id": r["from_id"],
            "from_name": r["from_name"],
            "to_id": r["to_id"],
            "text": r["text"],
            "created_at": r["created_at"],
            "incoming": r["to_id"] == user["id"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------- Static web
@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


# ---------------------------------------------------------------- Main
def main():
    init_db()
    import uvicorn

    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
