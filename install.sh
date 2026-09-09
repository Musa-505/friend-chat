#!/bin/bash
# Friend Chat — бір командамен орнату
# Қолдану: curl -sL https://raw.githubusercontent.com/Musa-505/friend-chat/main/install.sh | bash
set -e

SERVER="http://34.63.224.169:8001"
DIR="$HOME/friend-chat"
REPO="https://raw.githubusercontent.com/Musa-505/friend-chat/main"

echo "🚀 Friend Chat орнатылуда..."

# 1. Python тексеру
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 табылмады. Python 3 орнатыңыз: https://python.org"
  exit 1
fi

# 2. friend.py жүктеу
mkdir -p "$DIR"
curl -sL -o "$DIR/friend.py" "$REPO/friend.py"
chmod +x "$DIR/friend.py"

# 3. Сервер адресін орнату
python3 "$DIR/friend.py" config "$SERVER" >/dev/null

# 4. 'friend' командасын қосу
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
if ! grep -q "alias friend=" "$SHELL_RC" 2>/dev/null; then
  echo 'alias friend="python3 ~/friend-chat/friend.py"' >> "$SHELL_RC"
  echo "✅ 'friend' командасы қосылды ($SHELL_RC)"
fi

# 5. Тіркелу
echo ""
echo "Атыңызды жазыңыз (мысалы: Айбек):"
read -r NAME < /dev/tty
python3 "$DIR/friend.py" register "$NAME"

echo ""
echo "=============================================="
echo "✅ Дайын! Сіздің user_id:"
python3 "$DIR/friend.py" whoami
echo ""
echo "Осы user_id-ді досыңызға жіберіңіз — ол сізді қосады."
echo ""
echo "Қолдану (жаңа терминал ашыңыз немесе: source $SHELL_RC):"
echo "  friend add <user_id> <имя>   — дос қосу"
echo "  friend send <имя> <текст>    — хабар жіберу"
echo "  friend inbox                 — кіріс хабарлар"
echo "  friend list                  — достар тізімі"
echo "=============================================="
