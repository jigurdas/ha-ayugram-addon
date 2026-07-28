#!/bin/bash
# run.sh

# We don't need a custom run.sh if we use the Dockerfile CMD, 
# but Home Assistant addon requires a run.sh if it's not a standard image.
# Actually, for ingress to work properly with KasmVNC, we need to make sure
# the VNC server is accessible to the HA ingress proxy.

# KasmVNC listens on 6901 by default. HA ingress connects to it.

echo "Starting AyuGram Addon..."
