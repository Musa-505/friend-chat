Запуск фонового прослушивания входящих сообщений Friend Chat.

Сделай следующее:

1. Запусти daemon в фоне (Bash с run_in_background):
   ```bash
   DAEMON_PY=""
   for p in "$HOME/friend-chat/daemon.py" "$HOME/code/friend-chat/daemon.py"; do
     [ -f "$p" ] && DAEMON_PY="$p" && break
   done
   python3 "$DAEMON_PY"
   ```
2. Настрой Monitor для отслеживания новых сообщений:
   ```
   tail -f ~/.friend/inbox.log
   ```
   (каждая новая строка — входящее сообщение, показывай его пользователю)

3. Сообщи пользователю: «👂 Слушаю сообщения. Новые сообщения буду показывать автоматически.»
