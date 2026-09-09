#!/bin/bash
# Friend Chat — бір командамен орнату (macOS / Linux / Windows Git Bash)
# Қолдану: curl -sL https://raw.githubusercontent.com/Musa-505/friend-chat/main/install.sh | bash
set -e

SERVER="http://34.63.224.169:8001"
DIR="$HOME/friend-chat"
REPO="https://raw.githubusercontent.com/Musa-505/friend-chat/main"

echo "🚀 Friend Chat орнатылуда..."

# 1. Python табу (Windows-та python3 жоқ — python/py бар)
PY=""
for cmd in python3 python py; do
  if command -v "$cmd" >/dev/null 2>&1; then
    if "$cmd" --version >/dev/null 2>&1; then
      PY="$cmd"
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  echo "❌ Python табылмады. Python 3 орнатыңыз: https://www.python.org/downloads/"
  echo "   Орнату кезінде «Add Python to PATH» белгісін қойыңыз."
  exit 1
fi
echo "✅ Python: $($PY --version 2>&1)"

# 2. friend.py жүктеу
mkdir -p "$DIR"
curl -sL -o "$DIR/friend.py" "$REPO/friend.py"

# 3. Сервер адресін орнату
"$PY" "$DIR/friend.py" config "$SERVER" >/dev/null

# 4. 'friend' командасын қосу (bash/zsh болса)
SHELL_RC=""
[ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
if [ -n "$SHELL_RC" ] && ! grep -q "alias friend=" "$SHELL_RC" 2>/dev/null; then
  echo "alias friend=\"$PY ~/friend-chat/friend.py\"" >> "$SHELL_RC"
  echo "✅ 'friend' командасы қосылды ($SHELL_RC)"
fi

# 5. Тіркелу
echo ""
echo "Атыңызды жазыңыз (мысалы: Айбек):"
read -r NAME < /dev/tty
"$PY" "$DIR/friend.py" register "$NAME"

echo ""
echo "=============================================="
echo "✅ Дайын! Сіздің user_id:"
"$PY" "$DIR/friend.py" whoami
echo ""
echo "Осы user_id-ді досыңызға жіберіңіз — ол сізді қосады."
echo ""
if [ -n "$SHELL_RC" ]; then
  echo "Қолдану (жаңа терминал ашыңыз немесе: source $SHELL_RC):"
  echo "  friend add <user_id> <имя>   — дос қосу"
  echo "  friend send <имя> <текст>    — хабар жіберу"
  echo "  friend inbox                 — кіріс хабарлар"
  echo "  friend list                  — достар тізімі"
else
  echo "Қолдану:"
  echo "  $PY ~/friend-chat/friend.py add <user_id> <имя>"
  echo "  $PY ~/friend-chat/friend.py send <имя> <текст>"
  echo "  $PY ~/friend-chat/friend.py inbox"
fi
echo "=============================================="
