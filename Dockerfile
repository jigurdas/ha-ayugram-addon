FROM kasmweb/telegram:1.18.0

USER root
# Home Assistant Ingress terminates TLS before forwarding requests to the
# add-on. KasmVNC's base startup script unconditionally adds `-sslOnly`, and
# its default YAML configuration also requires SSL. Both reject the internal
# HTTP WebSocket connection. Keep TLS at the Ingress boundary and allow HTTP
# only between the Supervisor and this container.
RUN sed -i 's/[[:space:]]-sslOnly//g' /dockerstartup/vnc_startup.sh \
    && sed -i '/pem_key:/a\    require_ssl: false' /etc/kasmvnc/kasmvnc.yaml

# Install AyuGram Desktop pre-built binary
# This avoids compiling from source, which fails in GitHub Actions due to memory limits and Docker-in-Docker issues.
RUN apt-get update && apt-get install -y wget tar gzip \
    && wget -O /tmp/ayugram.tar.gz \
       https://github.com/AyuGram/AyuGramDesktop/releases/latest/download/AyuGramDesktop-6.7.8-full.tar.gz \
    && tar -xzf /tmp/ayugram.tar.gz -C /opt/ \
    && rm -f /tmp/ayugram.tar.gz \
    && apt-get clean
    
# Copy rootfs overlay
COPY ayugram/root /
RUN chmod +x /dockerstartup/custom_startup.sh \
    && chmod +x /etc/cont-init.d/99-ayugram

LABEL \
    org.opencontainers.image.title="Home Assistant Add-on: AyuGram Webtop" \
    org.opencontainers.image.description="Run AyuGram (Telegram Desktop) in a Docker container and access it via the browser from anywhere." \
    org.opencontainers.image.source="https://github.com/jigurdas/ha-ayugram-addon" \
    org.opencontainers.image.licenses="Apache License 2.0"
