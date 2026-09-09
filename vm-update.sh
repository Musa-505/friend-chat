#!/bin/bash
# Friend Chat — VM авто-жаңарту (GitHub-тан тартып алады)
# Cron: */5 * * * * /opt/friend-chat/vm-update.sh
REPO="https://raw.githubusercontent.com/Musa-505/friend-chat/main"
DIR="/opt/friend-chat"
CHANGED=0

cd "$DIR" || exit 1

# server.py
curl -sL -o /tmp/fc-server.py "$REPO/server.py"
if ! cmp -s /tmp/fc-server.py server.py; then
  cp /tmp/fc-server.py server.py
  CHANGED=1
fi

# web/index.html
curl -sL -o /tmp/fc-index.html "$REPO/web/index.html"
if ! cmp -s /tmp/fc-index.html web/index.html; then
  cp /tmp/fc-index.html web/index.html
  CHANGED=1
fi

rm -f /tmp/fc-server.py /tmp/fc-index.html

if [ "$CHANGED" = "1" ]; then
  sudo systemctl restart friend-chat
  echo "$(date '+%Y-%m-%d %H:%M:%S'): Friend Chat жаңартылды" >> "$DIR/update.log"
fi
