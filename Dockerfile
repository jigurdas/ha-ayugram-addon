FROM kasmweb/telegram:1.18.0

# Set environment variables for Home Assistant
ENV S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_WAIT_FOR_SERVICES=1 \
    VNC_PW=password \
    KASM_USER=kasm_user \
    KASM_PORT=6901

USER root

# Install dependencies, download AyuGram, create target directory and link Telegram executable
RUN apt-get update && apt-get install -y wget tar xz-utils curl jq unzip \
    && AYUGRAM_URL=$(curl -s https://api.github.com/repos/AyuGram/AyuGramDesktop/releases/latest | jq -r '.assets[].browser_download_url | select(test("Linux|linux|tar|zip"))' | head -n 1) \
    && echo "Downloading from: $AYUGRAM_URL" \
    && mkdir -p /tmp/ayugram_extract /opt/AyuGram \
    && wget -O /tmp/ayugram_archive "$AYUGRAM_URL" \
    && (tar -xf /tmp/ayugram_archive -C /tmp/ayugram_extract 2>/dev/null || unzip /tmp/ayugram_archive -d /tmp/ayugram_extract) \
    && cp -r /tmp/ayugram_extract/*/* /opt/AyuGram/ 2>/dev/null || cp -r /tmp/ayugram_extract/* /opt/AyuGram/ \
    && rm -rf /tmp/ayugram_archive /tmp/ayugram_extract \
    # Створюємо симлінк замість стандартного Telegram, щоб Kasm автоматично підхопив AyuGram
    && mkdir -p /opt/Telegram \
    && ln -sf /opt/AyuGram/AyuGram /opt/Telegram/Telegram \
    && chown -R kasm_user:kasm_user /opt/AyuGram /opt/Telegram \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a launcher script
RUN echo '#!/bin/bash' > /usr/local/bin/launch-ayugram.sh \
    && echo 'export DISPLAY=:1' >> /usr/local/bin/launch-ayugram.sh \
    && echo 'sudo -u kasm_user /opt/AyuGram/AyuGram &' >> /usr/local/bin/launch-ayugram.sh \
    && chmod +x /usr/local/bin/launch-ayugram.sh

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

COPY init.sh /etc/cont-init.d/99-ayugram-init
RUN chmod +x /etc/cont-init.d/99-ayugram-init

COPY root /
RUN chmod +x /etc/cont-init.d/99-ayugram 2>/dev/null || true

CMD ["bash", "/usr/local/bin/start.sh"]
