# AyuGram Webtop Addon

## Description
This Home Assistant addon allows you to run **AyuGram Desktop** (a modified Telegram client with Ghost mode, deleted messages history, etc.) inside a Docker container. 

It uses [KasmVNC](https://github.com/kasmtech/KasmVNC) (via the `kasmweb/telegram` base image) to provide a browser-accessible desktop environment.

## Features
- **Run AyuGram anywhere:** Access your Telegram account from any device (iPhone, iPad, Android, PC) via a browser.
- **Sidebar Integration:** Easily accessible from the Home Assistant sidebar.
- **Full Desktop Environment:** Includes a full Linux desktop if you need to run other apps.

## Installation
1. Go to the **Add-on Store** in Home Assistant.
2. Add this repository: `[YOUR_REPO_URL]`
3. Search for "AyuGram Webtop".
4. Click **Install**.

## Configuration
The addon comes with default settings that should work out of the box.
- **webgui_port**: The port used to access the web interface (Default: 6901).

## Usage
1. Start the addon.
2. Go to the **AyuGram** tab in your Home Assistant sidebar.
3. You will see the AyuGram interface. Log in to your Telegram account using your phone number.

## Notes
- AyuGram is not officially supported by Telegram and may violate their Terms of Service. Use at your own risk.
- Since this runs in a container, audio features (like Telegram calls) will not work.
- Ensure your Home Assistant instance is accessible from the outside (e.g., via Nabu Casa, Tailscale, or a reverse proxy) to access it from your iPhone.
