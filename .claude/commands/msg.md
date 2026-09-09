Отправка сообщения другу в Friend Chat.

Формат: `/msg <имя друга> <текст сообщения>`

Выполни команду и покажи результат:

```bash
FRIEND_PY=""
for p in "$HOME/friend-chat/friend.py" "$HOME/code/friend-chat/friend.py"; do
  [ -f "$p" ] && FRIEND_PY="$p" && break
done
python3 "$FRIEND_PY" send $ARGUMENTS
```

Если друг не найден — подскажи пользователю посмотреть список: `/friend list`.
