# AyuGram Webtop Addon

Run AyuGram (Telegram Desktop) in a Docker container and access it via the browser from anywhere.

[![Open your Home Assistant instance and show the add-on store with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/?repository_url=https%3A%2F%2Fgithub.com%2Fjigurdas%2Fha-ayugram-addon)

## About

This Home Assistant addon allows you to run **AyuGram Desktop** (a modified Telegram client with Ghost mode, deleted messages history, message filters, and more) inside a Docker container.

It uses [KasmVNC](https://github.com/kasmtech/KasmVNC) to stream the desktop interface to your browser, making it accessible from **any device in the world** — including your iPhone.

AyuGram does not have an official web version. This addon solves that problem by running the full desktop application inside a container and streaming it to your browser.

## Features

- **Run AyuGram anywhere:** Access your Telegram account from any device (iPhone, iPad, Android, PC) via a browser.
- **Sidebar Integration:** Easily accessible from the Home Assistant sidebar.
- **Full Desktop Environment:** Includes a full Linux desktop if you need to run other apps.
- **Persistent Data:** Your AyuGram settings and downloads are saved.

## Usage

1. Start the addon.
2. Go to the **AyuGram** tab in your Home Assistant sidebar.
3. You will see the AyuGram interface. Log in to your Telegram account using your phone number.

## Notes

AyuGram is not officially supported by Telegram and may violate their Terms of Service. Use at your own risk. Since this runs in a container, audio features (like Telegram calls) will not work. Ensure your Home Assistant instance is accessible from the outside (e.g., via Nabu Casa, Tailscale, or a reverse proxy) to access it from your iPhone.
