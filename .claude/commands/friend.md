Управление друзьями в Friend Chat.

Выполни команду и покажи результат пользователю:

```bash
FRIEND_PY=""
for p in "$HOME/friend-chat/friend.py" "$HOME/code/friend-chat/friend.py"; do
  [ -f "$p" ] && FRIEND_PY="$p" && break
done
python3 "$FRIEND_PY" $ARGUMENTS
```

Доступные подкоманды:
- `register <имя>` — создать аккаунт (выполняется один раз)
- `add <user_id> [имя]` — добавить друга по его user_id
- `list` — список друзей
- `whoami` — показать мой user_id (поделиться с другом)

Если пользователь ещё не зарегистрирован (нет файла ~/.friend/config.json) — предложи сначала выполнить `register`.
