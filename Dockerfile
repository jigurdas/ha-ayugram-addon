
FROM kasmweb/telegram:1.18.0

USER root
# Home Assistant Ingress terminates TLS before forwarding requests to the
# add-on. KasmVNC's base startup script unconditionally adds `-sslOnly`, and
# its default YAML configuration also requires SSL. Both reject the internal
# HTTP WebSocket connection. Keep TLS at the Ingress boundary and allow HTTP
# only between the Supervisor and this container.
RUN sed -i 's/[[:space:]]-sslOnly//g' /dockerstartup/vnc_startup.sh \
    && sed -i '/pem_key:/a\    require_ssl: false' /etc/kasmvnc/kasmvnc.yaml \
    && sed -i 's/port: 8444/port: 6901/g' /etc/kasmvnc/kasmvnc.yaml

ARG AYUGRAM_BINARY_PATH
COPY ${AYUGRAM_BINARY_PATH} /opt/AyuGram/AyuGram
RUN chmod +x /opt/AyuGram/AyuGram

# Copy rootfs overlay
COPY ayugram/root /
RUN chmod +x /dockerstartup/custom_startup.sh \
    && chmod +x /etc/cont-init.d/99-ayugram

LABEL \
    org.opencontainers.image.title="Home Assistant Add-on: AyuGram Webtop" \
    org.opencontainers.image.description="Run AyuGram (Telegram Desktop) in a Docker container and access it via the browser from anywhere." \
    org.opencontainers.image.source="https://github.com/jigurdas/ha-ayugram-addon" \
    org.opencontainers.image.licenses="Apache License 2.0"
