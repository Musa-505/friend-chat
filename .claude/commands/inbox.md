Чтение входящих сообщений Friend Chat.

Выполни команду и покажи сообщения пользователю:

```bash
FRIEND_PY=""
for p in "$HOME/friend-chat/friend.py" "$HOME/code/friend-chat/friend.py"; do
  [ -f "$p" ] && FRIEND_PY="$p" && break
done
python3 "$FRIEND_PY" inbox
```

Если сообщений нет — так и скажи. Если есть — покажи их в удобном виде (от кого и текст).
