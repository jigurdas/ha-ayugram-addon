#!/bin/bash

# Start the VNC server
echo "Starting KasmVNC..."
bash /kasm/start_default.sh

# Launch AyuGram
echo "Launching AyuGram..."
launch-ayugram.sh

# Keep container alive
tail -f /dev/null
