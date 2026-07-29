# --- Stage 1: Build AyuGram Desktop ---
FROM ghcr.io/telegramdesktop/tdesktop/centos_env:latest AS builder

# Set API credentials (using defaults from documentation)
ARG TDESKTOP_API_ID=2040
ARG TDESKTOP_API_HASH=b18441a1ff607e10a989891a5462e627

WORKDIR /usr/src/tdesktop

# Clone source code and prepare libraries
RUN git clone --recursive https://github.com/AyuGram/AyuGramDesktop.git . \
    && ./Telegram/build/prepare/linux.sh

# Build the project
RUN ./Telegram/build/docker/centos_env/build.sh \
    -D TDESKTOP_API_ID=${TDESKTOP_API_ID} \
    -D TDESKTOP_API_HASH=${TDESKTOP_API_HASH}

# --- Stage 2: Final Addon Image ---
FROM kasmweb/telegram:1.18.0

# Set environment variables for Home Assistant
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_WAIT_FOR_SERVICES=1 \
    VNC_PW=password \
    KASM_USER=kasm_user \
    KASM_PORT=6901

USER root

# Install runtime dependencies for the built binary
RUN apt-get update && apt-get install -y \
    libxcb-keysyms1 libxcb-image0 libxcb-shm0 libxcb-icccm4 libxcb-sync1 libxcb-render-util0 libxcb-xfixes0 libxcb-randr0 libxcb-shape0 libxcb-xinerama0 libxkbcommon-x11-0 libxcb-xinput0 \
    libfontconfig1 libdbus-1-3 libpulse0 libasound2 libnss3 libnspr4 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy built binary from builder stage
RUN mkdir -p /opt/AyuGram /opt/Telegram
COPY --from=builder /usr/src/tdesktop/out/AyuGram /opt/AyuGram/AyuGram

# Link Telegram executable and set permissions
RUN ln -sf /opt/AyuGram/AyuGram /opt/Telegram/Telegram \
    && chmod -R 777 /opt/AyuGram /opt/Telegram

# Create a launcher script with display check
RUN echo '#!/bin/bash' > /usr/local/bin/launch-ayugram.sh \
    && echo 'export DISPLAY=:1' >> /usr/local/bin/launch-ayugram.sh \
    && echo 'for i in {1..30}; do if xset q > /dev/null 2>&1; then break; fi; sleep 1; done' >> /usr/local/bin/launch-ayugram.sh \
    && echo 'sudo -u kasm_user /opt/AyuGram/AyuGram &' >> /usr/local/bin/launch-ayugram.sh \
    && chmod +x /usr/local/bin/launch-ayugram.sh

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

COPY init.sh /etc/cont-init.d/99-ayugram-init
RUN chmod +x /etc/cont-init.d/99-ayugram-init

COPY root /
RUN chmod +x /etc/cont-init.d/99-ayugram 2>/dev/null || true

CMD ["bash", "/usr/local/bin/start.sh"]
