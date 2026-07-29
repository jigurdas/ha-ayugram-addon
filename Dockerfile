FROM kasmweb/telegram:1.18.0

# Install AyuGram Desktop pre-built binary
# This avoids compiling from source, which fails in GitHub Actions due to memory limits and Docker-in-Docker issues.
RUN apt-get update && apt-get install -y wget tar xz-utils \
    && wget -O /tmp/ayugram.tar.xz https://github.com/AyuGram/AyuGramDesktop/releases/latest/download/AyuGram-Setup.tar.xz \
    && tar -xf /tmp/ayugram.tar.xz -C /opt/ \
    && rm -f /tmp/ayugram.tar.xz \
    && apt-get clean

# Create a launcher script
RUN echo '#!/bin/bash' > /usr/local/bin/launch-ayugram.sh \
    && echo 'export DISPLAY=:1' >> /usr/local/bin/launch-ayugram.sh \
    && echo 'sudo -u kasm_user /opt/AyuGram/AyuGram &' >> /usr/local/bin/launch-ayugram.sh \
    && chmod +x /usr/local/bin/launch-ayugram.sh

# Copy rootfs overlay
COPY rootfs /

LABEL \
    org.opencontainers.image.title="Home Assistant Add-on: AyuGram Webtop" \
    org.opencontainers.image.description="Run AyuGram (Telegram Desktop) in a Docker container and access it via the browser from anywhere." \
    org.opencontainers.image.source="https://github.com/jigurdas/ha-ayugram-addon" \
    org.opencontainers.image.licenses="Apache License 2.0"
