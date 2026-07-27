# AyuGram Home Assistant Addon

## What is this?

This addon runs **AyuGram Desktop** (a powerful Telegram client with Ghost mode, deleted messages history, message filters, and more) inside a Docker container on your Home Assistant instance. It uses [KasmVNC](https://github.com/kasmtech/KasmVNC) to stream the desktop interface to your browser, making it accessible from **any device in the world** — including your iPhone.

> AyuGram does not have an official web version. This addon solves that problem by running the full desktop application inside a container and streaming it to your browser.

---

## How it works

The addon is built on top of `kasmweb/telegram` (a KasmVNC-based Docker image that provides Telegram Desktop via browser). We replace the standard Telegram with AyuGram Desktop, so you get all the advanced features (Ghost mode, anti-delete, history, etc.) accessible from any browser.

---

## Files included

| File | Description |
|------|-------------|
| `config.yaml` | Home Assistant addon configuration (ingress, ports, panel settings) |
| `Dockerfile` | Docker build instructions — installs AyuGram on top of kasmweb/telegram |
| `run.sh` | Addon startup script |
| `start.sh` | Container entrypoint — starts KasmVNC and launches AyuGram |
| `init.sh` | Initialization script for the KasmVNC environment |
| `root/etc/cont-init.d/99-ayugram` | Creates a desktop menu entry for AyuGram |
| `DOCS.md` | Addon documentation (shown in HA addon store) |

---

## Installation instructions

### Step 1: Create a GitHub repository

Push these files to a GitHub repository, for example:
```
https://github.com/jigurdas/ha-ayugram-addon
```

### Step 2: Add the repository in Home Assistant

1. Open Home Assistant
2. Go to **Settings** → **Add-ons** → **Add-on Store**
3. Click the three dots (⋮) in the top-right corner → **Repositories**
4. Add your GitHub repository URL
5. Click **Refresh**

### Step 3: Install the addon

1. Search for **"AyuGram Webtop"** in the addon store
2. Click on it → **Install**
3. Wait for the installation to complete

### Step 4: Start the addon

1. After installation, click **Start**
2. Wait 30-60 seconds for AyuGram to launch

### Step 5: Access AyuGram

- **From Home Assistant sidebar:** Click the **AyuGram** tab
- **From iPhone (anywhere):** Open your iPhone's browser and navigate to your Home Assistant URL. Then go to the AyuGram panel in the sidebar.

### Step 6: Log in to Telegram

1. You will see the AyuGram interface
2. Enter your phone number
3. Confirm the login code on your phone
4. Done! AyuGram is now running.

---

## Configuration (optional)

The addon uses these default ports:

| Setting | Value |
|---------|-------|
| Ingress port | 6901 (KasmVNC HTTPS) |
| External port | 6901 |
| Panel title | AyuGram |
| Panel icon | Telegram icon |

---

## Important notes

### AyuGram features included:
- **Ghost mode** — read messages without being seen
- **Anti-delete** — see deleted messages
- **Message history** — restored chat history
- **Message filters** — filter by keywords, users, etc.
- **Self-destructing messages** — view expired messages

### Limitations:
- **No audio/video calls** — the container doesn't support audio pass-through
- **No microphone** — voice messages can be recorded on the container side only
- **Login session** — Telegram login session is stored in the container. If you restart the container, you may need to re-login.

### For iPhone access:
- Use Nabu Casa (https://www.nabucasa.com/) or a reverse proxy (e.g., DuckDNS + Let's Encrypt) to make Home Assistant accessible from outside your network
- Alternatively, use Tailscale for a secure VPN connection

---

## Building the Docker image

If you want to build the image manually:

```bash
docker build -t ha-ayugram-addon .
docker run -d --name ayugram -p 6901:6901 --shm-size=512m ha-ayugram-addon
```

Then access it at: `https://your-server-ip:6901`

Default credentials:
- **User:** `kasm_user`
- **Password:** (set via `VNC_PW` environment variable, or use Home Assistant ingress)

---

## Troubleshooting

### The addon shows a black screen
- Wait 30-60 seconds for the container to fully start
- Check the addon logs for errors

### AyuGram doesn't launch
- Check the addon logs
- Try stopping and restarting the addon
- Ensure the download URL for AyuGram is still valid

### Can't access from iPhone
- Make sure your Home Assistant instance is accessible from outside your network
- Check that the AyuGram panel is visible in the sidebar
- Try clearing your iPhone browser cache

---

## License

This addon is provided as-is. AyuGram is an open-source project maintained by [Radolyn Labs](https://radolyn.com). Use at your own risk.

## References

- [AyuGram Desktop](https://github.com/AyuGram/AyuGramDesktop)
- [KasmVNC](https://github.com/kasmtech/KasmVNC)
- [kasmweb/telegram Docker image](https://hub.docker.com/r/kasmweb/telegram)
- [Home Assistant Ingress](https://developers.home-assistant.io/docs/apps/presentation/)
- [LinuxServer Webtop](https://docs.linuxserver.io/images/docker-webtop/)
