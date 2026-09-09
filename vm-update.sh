#!/bin/bash
# Friend Chat — VM авто-жаңарту (GitHub-тан тартып алады)
# Cron: */5 * * * * /opt/friend-chat/vm-update.sh
API="https://api.github.com/repos/Musa-505/friend-chat/contents"
DIR="/opt/friend-chat"
CHANGED=0

cd "$DIR" || exit 1

# server.py
curl -sL -H "Accept: application/vnd.github.raw" -H "User-Agent: friend-chat" -o /tmp/fc-server.py "$API/server.py"
if ! cmp -s /tmp/fc-server.py server.py; then
  cp /tmp/fc-server.py server.py
  CHANGED=1
fi

# web/index.html
curl -sL -H "Accept: application/vnd.github.raw" -H "User-Agent: friend-chat" -o /tmp/fc-index.html "$API/web/index.html"
if ! cmp -s /tmp/fc-index.html web/index.html; then
  cp /tmp/fc-index.html web/index.html
  CHANGED=1
fi

rm -f /tmp/fc-server.py /tmp/fc-index.html

if [ "$CHANGED" = "1" ]; then
  sudo systemctl restart friend-chat
  echo "$(date '+%Y-%m-%d %H:%M:%S'): Friend Chat жаңартылды" >> "$DIR/update.log"
fi
