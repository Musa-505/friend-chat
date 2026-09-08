#!/bin/bash
# Friend Chat — запуск сервера + cloudflared tunnel
# Достарыңызға сілтеме: cloudflared шығарған https:// URL

cd "$(dirname "$0")"

# 1. Серверді фонда іске қосу
if lsof -nP -iTCP:8001 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "✅ Сервер уже работает на :8001"
else
  echo "🚀 Запуск сервера на :8001..."
  nohup python3 server.py > server.log 2>&1 &
  sleep 2
  echo "✅ Сервер запущен (лог: server.log)"
fi

# 2. cloudflared tunnel — достарға ашық сілтеме
echo ""
echo "🌐 Запуск cloudflared tunnel (Ctrl+C для остановки)..."
echo "   Достарыңызға осы URL-ді жіберіңіз:"
echo ""
cloudflared tunnel --url http://localhost:8001
