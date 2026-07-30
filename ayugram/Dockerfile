
FROM kasmweb/telegram:1.18.0

USER root

# KasmVNC configuration is provided via the overlay at ayugram/root/etc/kasmvnc/kasmvnc.yaml.
# This avoids runtime YAML patching and ensures the configuration is valid and explicit.

ARG AYUGRAM_BINARY_PATH
# The binary path is relative to the context (root of repo)
COPY ${AYUGRAM_BINARY_PATH} /opt/AyuGram/AyuGram
RUN chmod +x /opt/AyuGram/AyuGram

# Remove the base image's forced KasmVNC SSL-only flag.
RUN sed -i 's/ -sslOnly//g' /dockerstartup/vnc_startup.sh

# Copy rootfs overlay
COPY ayugram/root /
RUN chmod +x /dockerstartup/custom_startup.sh \
    && chmod +x /etc/cont-init.d/99-ayugram

# Set environment variables for KasmVNC
ENV VNC_PORT=6901 \
    VNC_COL_DEPTH=24 \
    VNC_RESOLUTION=1280x720

LABEL \
    org.opencontainers.image.title="Home Assistant Add-on: AyuGram Webtop" \
    org.opencontainers.image.description="Run AyuGram (Telegram Desktop) in a Docker container and access it via the browser from anywhere." \
    org.opencontainers.image.source="https://github.com/jigurdas/ha-ayugram-addon" \
    org.opencontainers.image.licenses="Apache License 2.0"
