#!/bin/bash
set -e

# vnc_startup.sh invokes this hook after the Xfce session is ready. Run the
# desktop client as Kasm's unprivileged Linux user, not as the VNC account.
export DISPLAY=:1
exec sudo -u kasm-user /opt/AyuGram/AyuGram
