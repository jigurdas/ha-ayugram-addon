FROM kasmweb/telegram:1.18.0

# Set environment variables for Home Assistant
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_WAIT_FOR_SERVICES=1 \
    VNC_PW=password \
    KASM_USER=kasm_user \
    KASM_PORT=6901

# Install AyuGram Desktop
# Note: We download the official Ayugram release for Linux
USER root

RUN apt-get update && apt-get install -y wget tar xz-utils curl jq unzip \
    && AYUGRAM_URL=$(curl -s https://api.github.com/repos/AyuGram/AyuGramDesktop/releases/latest | jq -r '.assets[].browser_download_url | select(test("Linux|linux|tar|zip"))' | head -n 1) \
    && echo "Downloading from: $AYUGRAM_URL" \
    && wget -O /tmp/ayugram_archive "$AYUGRAM_URL" \
    && (tar -xf /tmp/ayugram_archive -C /opt/ 2>/dev/null || unzip /tmp/ayugram_archive -d /opt/) \
    && rm -f /tmp/ayugram_archive \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a launcher script
RUN echo '#!/bin/bash' > /usr/local/bin/launch-ayugram.sh \
    && echo 'export DISPLAY=:1' >> /usr/local/bin/launch-ayugram.sh \
    && echo 'sudo -u kasm_user /opt/AyuGram/AyuGram &' >> /usr/local/bin/launch-ayugram.sh \
    && chmod +x /usr/local/bin/launch-ayugram.sh

# Override the default telegram launch to launch AyuGram instead
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

COPY init.sh /etc/cont-init.d/99-ayugram-init
RUN chmod +x /etc/cont-init.d/99-ayugram-init

COPY root /
RUN chmod +x /etc/cont-init.d/99-ayugram \
    && chown -R kasm_user:kasm_user /opt/AyuGram || true

CMD ["bash", "/usr/local/bin/start.sh"]

