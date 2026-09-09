#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Friend Chat CLI — Claude Code ішінен шақырылады.

Usage:
  friend.py register <имя>            — создать аккаунт
  friend.py add <user_id> [имя]       — добавить друга
  friend.py list                      — список друзей
  friend.py send <имя> <текст>        — отправить сообщение
  friend.py inbox                     — прочитать новые сообщения
  friend.py whoami                    — мой user_id
  friend.py config [url]              — показать/сменить адрес сервера
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

CONFIG_DIR = os.path.expanduser("~/.friend")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_SERVER = "http://localhost:8001"
VERSION = "1.1.0"
REPO_RAW = "https://raw.githubusercontent.com/Musa-505/friend-chat/main"
UPDATE_CACHE = os.path.join(CONFIG_DIR, ".update_check")


# ---------------------------------------------------------------- config
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def server_url():
    cfg = load_config()
    return cfg.get("server", DEFAULT_SERVER)


# ---------------------------------------------------------------- http
def api(method, path, data=None, token=None):
    url = server_url().rstrip("/") + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("X-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode()).get("detail", str(e))
        except Exception:
            detail = str(e)
        if e.code == 401:
            sys.exit(f"Ошибка: {detail}\nҚайта тіркеліңіз: friend.py register <имя>")
        sys.exit(f"Ошибка: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Не удалось подключиться к серверу ({server_url()}). "
                 f"Запустите: ~/code/friend-chat/run.sh\n{e.reason}")


# ---------------------------------------------------------------- update
def check_update(force=False):
    """GitHub-та жаңа нұсқа бар ма? (сағатына бір рет тексереді)"""
    if not force and os.path.exists(UPDATE_CACHE):
        try:
            if time.time() - os.path.getmtime(UPDATE_CACHE) < 3600:
                return None
        except Exception:
            pass
    try:
        with urllib.request.urlopen(REPO_RAW + "/friend.py", timeout=10) as resp:
            content = resp.read().decode()
        m = re.search(r'VERSION\s*=\s*"([^"]+)"', content)
        latest = m.group(1) if m else None
    except Exception:
        return None
    try:
        with open(UPDATE_CACHE, "w") as f:
            f.write(latest or "")
    except Exception:
        pass
    if latest and latest != VERSION:
        return latest
    return None


def do_update():
    """friend.py + daemon.py жаңа нұсқасын жүктеп, ауыстырады."""
    base = os.path.dirname(os.path.abspath(__file__))
    ok = True
    for fname in ("friend.py", "daemon.py"):
        try:
            with urllib.request.urlopen(REPO_RAW + "/" + fname, timeout=15) as resp:
                data = resp.read()
            path = os.path.join(base, fname)
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        except Exception as e:
            print(f"⚠️ {fname} жаңарту сәтсіз: {e}")
            ok = False
    return ok


def cmd_update():
    latest = check_update(force=True)
    if not latest:
        print(f"Сізде ең жаңа нұсқа бар ({VERSION}).")
        return
    print(f"🔄 Жаңа нұсқа табылды: {VERSION} → {latest}")
    if do_update():
        print("✅ Жаңартылды! Команданы қайта орындаңыз.")
    else:
        sys.exit("Жаңарту сәтсіз аяқталды.")


# ---------------------------------------------------------------- commands
def cmd_register(name):
    res = api("POST", "/api/register", {"name": name})
    cfg = load_config()
    cfg["server"] = cfg.get("server", DEFAULT_SERVER)
    cfg["user_id"] = res["user_id"]
    cfg["token"] = res["token"]
    cfg["name"] = res["name"]
    cfg.setdefault("friends", {})
    cfg.setdefault("last_seen_id", 0)
    save_config(cfg)
    print(f"✅ Аккаунт создан: {res['name']}")
    print(f"   Ваш user_id: {res['user_id']}")
    print(f"   Поделитесь этим ID с друзьями, чтобы они могли вас добавить.")


def cmd_add(friend_id, name=""):
    cfg = load_config()
    if "token" not in cfg:
        sys.exit("Сначала зарегистрируйтесь: friend.py register <имя>")
    res = api("POST", "/api/friends", {"friend_id": friend_id, "name": name}, cfg["token"])
    cfg.setdefault("friends", {})[res["name"]] = res["friend_id"]
    save_config(cfg)
    print(f"✅ Друг добавлен: {res['name']} ({res['friend_id']})")


def cmd_list():
    cfg = load_config()
    if "token" not in cfg:
        sys.exit("Сначала зарегистрируйтесь: friend.py register <имя>")
    res = api("GET", "/api/friends", token=cfg["token"])
    if not res:
        print("Друзей пока нет. Добавьте: friend.py add <user_id> <имя>")
        return
    print("Ваши друзья:")
    for f in res:
        print(f"  • {f['name']}  ({f['friend_id']})")


def cmd_send(name, text):
    cfg = load_config()
    if "token" not in cfg:
        sys.exit("Сначала зарегистрируйтесь: friend.py register <имя>")
    friends = cfg.get("friends", {})
    friend_id = friends.get(name)
    if not friend_id:
        sys.exit(f"Друг '{name}' не найден. Список: friend.py list")
    res = api("POST", "/api/messages", {"to_id": friend_id, "text": text}, cfg["token"])
    print(f"✅ Отправлено {name}: {res['text']}")


def cmd_inbox():
    cfg = load_config()
    if "token" not in cfg:
        sys.exit("Сначала зарегистрируйтесь: friend.py register <имя>")
    since = cfg.get("last_seen_id", 0)
    res = api("GET", f"/api/messages?since={since}", token=cfg["token"])
    if not res:
        print("Новых сообщений нет.")
        return
    for m in res:
        if m["incoming"]:
            print(f"[{m['id']}] {m['from_name']}: {m['text']}")
        else:
            print(f"[{m['id']}] Вы: {m['text']}")
    cfg["last_seen_id"] = max(m["id"] for m in res)
    save_config(cfg)


def cmd_whoami():
    cfg = load_config()
    if "user_id" not in cfg:
        sys.exit("Сначала зарегистрируйтесь: friend.py register <имя>")
    print(f"Имя: {cfg.get('name', '?')}")
    print(f"user_id: {cfg['user_id']}")
    print(f"Сервер: {cfg.get('server', DEFAULT_SERVER)}")


def cmd_config(url=None):
    cfg = load_config()
    if url:
        cfg["server"] = url.rstrip("/")
        save_config(cfg)
        print(f"Сервер изменён: {cfg['server']}")
    else:
        print(f"Сервер: {cfg.get('server', DEFAULT_SERVER)}")


# ---------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    # авто-жаңарту тексеру (update командасынан басқасында)
    if cmd != "update":
        try:
            if check_update():
                if do_update():
                    print("🔄 Жаңа нұсқа орнатылды! Команданы қайта орындаңыз.")
                    return
        except Exception:
            pass
    if cmd == "register":
        if len(args) < 2:
            sys.exit("Использование: friend.py register <имя>")
        cmd_register(" ".join(args[1:]))
    elif cmd == "add":
        if len(args) < 2:
            sys.exit("Использование: friend.py add <user_id> [имя]")
        cmd_add(args[1], " ".join(args[2:]))
    elif cmd == "list":
        cmd_list()
    elif cmd == "send":
        if len(args) < 3:
            sys.exit("Использование: friend.py send <имя> <текст>")
        cmd_send(args[1], " ".join(args[2:]))
    elif cmd == "inbox":
        cmd_inbox()
    elif cmd == "whoami":
        cmd_whoami()
    elif cmd == "config":
        cmd_config(args[1] if len(args) > 1 else None)
    elif cmd == "update":
        cmd_update()
    else:
        sys.exit(f"Неизвестная команда: {cmd}\n\n{__doc__}")


if __name__ == "__main__":
    main()
