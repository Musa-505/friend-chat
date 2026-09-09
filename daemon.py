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
VERSION = "1.1.0"


def fetch_github_file(fname):
    """GitHub API арқылы файлды жүктеу (raw CDN кэшінен сенімді)."""
    url = f"https://api.github.com/repos/Musa-505/friend-chat/contents/{fname}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "friend-chat",
        "Accept": "application/vnd.github.raw",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def check_and_update():
    """GitHub-та жаңа нұсқа болса, friend.py + daemon.py жаңартады."""
    import re
    try:
        content = fetch_github_file("daemon.py").decode()
        m = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
        latest = m.group(1) if m else None
        if latest and latest != VERSION:
            base = os.path.dirname(os.path.abspath(__file__))
            for fname in ("friend.py", "daemon.py"):
                try:
                    data = fetch_github_file(fname)
                    path = os.path.join(base, fname)
                    tmp = path + ".tmp"
                    with open(tmp, "wb") as f:
                        f.write(data)
                    os.replace(tmp, path)
                except Exception as e:
                    print(f"⚠️ {fname} жаңарту сәтсіз: {e}", file=sys.stderr)
            print(f"🔄 Жаңартылды ({VERSION} → {latest}).", file=sys.stderr)
            return True
    except Exception:
        pass
    return False


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
    check_and_update()
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
