#!/bin/bash
set -e

# vnc_startup.sh invokes this hook after the Xfce session has started. Match
# Kasm's application startup sequence so the client does not start before the
# desktop is ready, and restart it if the user closes it.
export DISPLAY=:1
export MAXIMIZE=true

/usr/bin/filter_ready
/usr/bin/desktop_ready
bash "${STARTUPDIR}/maximize_window.sh" &

while true; do
    if ! pgrep -x AyuGram > /dev/null; then
        sudo -u kasm-user /opt/AyuGram/AyuGram --no-sandbox || true
    fi
    sleep 1
done
