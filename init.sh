#!/bin/bash

# KasmVNC initialization for Home Assistant Addon
# This script prepares the KasmVNC environment to run inside HA

# Ensure X11 directory exists
mkdir -p /tmp/.X11-unix

# We will rely on the base image's startup scripts for the most part
# but we might need to adjust permissions or environment variables here
echo "Initializing AyuGram addon..."
