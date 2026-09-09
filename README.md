# Friend Chat 💬

Claude Code терминалынан шықпай-ақ достармен хат жазысу құралы.

- **Сервер**: өз серверіңіз (FastAPI + WebSocket + SQLite), жергілікті машинада
- **Достар**: браузерден кіреді (cloudflared tunnel сілтемесі)
- **Интеграция**: Claude Code slash command-дары

## Құрылымы

```
friend-chat/
├── server.py          # FastAPI + WebSocket + SQLite сервер
├── friend.py          # CLI клиент (Claude Code шақырады)
├── daemon.py          # фондық хабар қабылдағыш
├── web/index.html     # достарға арналған браузер чаты
├── run.sh             # сервер + cloudflared tunnel
└── requirements.txt
```

## Іске қосу

```bash
cd ~/code/friend-chat
./run.sh
```

`run.sh` серверді :8001-де іске қосады және cloudflared tunnel ашады.
Терминалда шыққан **https://** URL-ді достарыңызға жіберіңіз — олар браузерден кіреді.

## Claude Code ішінде қолдану

| Команда | Сипаттама |
|---|---|
| `/friend register <имя>` | аккаунт құру (бір рет) |
| `/friend add <user_id> [имя]` | дос қосу |
| `/friend list` | достар тізімі |
| `/friend whoami` | менің user_id-ім |
| `/msg <имя> <текст>` | хабар жіберу |
| `/inbox` | кіріс хабарларды оқу |
| `/listen` | фондық тыңдауды іске қосу (жаңа хабарлар автоматты көрсетіледі) |

## Қолмен (CLI)

```bash
python3 ~/code/friend-chat/friend.py register Айбек
python3 ~/code/friend-chat/friend.py add u_xxxxxxxx Дос
python3 ~/code/friend-chat/friend.py send Дос "Сәлем!"
python3 ~/code/friend-chat/friend.py inbox
```

## Дос қосу ағыны

1. Сіз тіркелесіз → `user_id` аласыз (мысалы `u_8f3a2b`)
2. Досыңыз сілтеме бойынша браузерден кіреді, тіркеледі → өз `user_id`-ін алады
3. Сіз `/friend add <дос_id>` арқылы, досыңыз сізді өз браузерінде қосады
4. Хат жазысасыздар

## Онлайн сервер (gcloud)

Сервер **https://github.com/Musa-505/friend-chat** жобасынан gcloud Compute Engine-ге орнатылған:

- **Адрес**: `http://34.63.224.169:8001` (статикалық IP)
- **VM**: `friend-chat` (e2-micro, us-central1-a, free tier)
- **Сервис**: systemd `friend-chat.service`, автоматты қайта іске қосу
- **Деректер**: SQLite `/opt/friend-chat/friendchat.db` (тұрақты диск)

Достарға сілтеме: **http://34.63.224.169:8001** — браузерден ашылады, тіркеледі, хат жазысады.

### Клиентті онлайн серверге бағыттау

```bash
python3 ~/code/friend-chat/friend.py config http://34.63.224.169:8001
python3 ~/code/friend-chat/friend.py register <имя>
```

### Серверді басқа машинаға көшіру

Сервер кез келген жерде жұмыс істей алады (VDS, Docker, gcloud). Тек:
- `server.py`-ді іске қосыңыз (порт 8001)
- Клиенттерде сервер адресін өзгертіңіз: `friend.py config https://your-server`
- Веб-чат сол адресте ашылады
