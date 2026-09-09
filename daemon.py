#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Friend Chat daemon — фоновый приём сообщений.

Подключается к серверу по WebSocket, выводит входящие сообщения в stdout
и дописывает их в ~/.friend/inbox.log. При обрыве — переподключается.

Запуск (в фоне):  python3 ~/code/friend-chat/daemon.py
"""
import asyncio
import json
import os
import sys
import time
import urllib.request

import websockets

CONFIG_DIR = os.path.expanduser("~/.friend")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "inbox.log")
LAST_ID_PATH = os.path.join(CONFIG_DIR, "last_id")
DEFAULT_SERVER = "http://localhost:8001"


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def read_last_id():
    try:
        with open(LAST_ID_PATH) as f:
            return int(f.read().strip())
    except Exception:
        return 0


def write_last_id(msg_id):
    with open(LAST_ID_PATH, "w") as f:
        f.write(str(msg_id))


def log_line(line):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def fetch_catchup(server, token, since):
    """Получить пропущенные сообщения (пока daemon не работал)."""
    url = f"{server.rstrip('/')}/api/messages?since={since}"
    req = urllib.request.Request(url)
    req.add_header("X-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return []


def format_msg(m):
    who = m.get("from_name", m.get("from_id", "?"))
    return f"💬 {who}: {m['text']}"


async def run():
    cfg = load_config()
    if "token" not in cfg:
        print("Нет конфигурации. Сначала: friend.py register <имя>", file=sys.stderr)
        return
    server = cfg.get("server", DEFAULT_SERVER)
    token = cfg["token"]
    ws_url = server.replace("http://", "ws://").replace("https://", "wss://").rstrip("/")
    ws_url += f"/ws?token={token}"

    # catch-up: сообщения, пропущенные пока daemon не работал
    last_id = read_last_id()
    for m in fetch_catchup(server, token, last_id):
        if m.get("incoming"):
            log_line(format_msg(m))
        last_id = max(last_id, m["id"])
    write_last_id(last_id)

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"👂 Слушаю сообщения ({server}). Остановка: Ctrl+C", flush=True)
                while True:
                    raw = await ws.recv()
                    msg = json.loads(raw)
                    if msg.get("type") == "message":
                        log_line(format_msg(msg))
                        write_last_id(msg["id"])
        except websockets.exceptions.InvalidStatus as e:
            if e.response.status_code == 403:
                print("❌ Токен жарамсыз. Қайта тіркеліңіз: friend.py register <имя>", file=sys.stderr)
                return
            print(f"⚠️ Сервер қатесі ({e.response.status_code}). Қайта қосылу 5с...", file=sys.stderr)
            await asyncio.sleep(5)
        except (websockets.ConnectionClosed, OSError) as e:
            print(f"⚠️ Соединение потеряно ({e}). Переподключение через 5с...", file=sys.stderr)
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nОстановлено.")
