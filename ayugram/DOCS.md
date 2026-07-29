# AyuGram Webtop Addon Documentation

## Configuration

The addon comes with default settings that should work out of the box.

- **webgui_port**: The port used to access the web interface (Default: 6901).
  When opened from the Home Assistant sidebar, HTTPS is terminated by Home
  Assistant Ingress; the connection from Ingress to the add-on uses HTTP.

## Troubleshooting

### The addon shows a black screen

Wait 30-60 seconds for the container to fully start. Check the addon logs for errors.

### AyuGram doesn't launch

Check the addon logs. Try stopping and restarting the addon. Ensure the download URL for AyuGram is still valid.

### Can't access from iPhone

Make sure your Home Assistant instance is accessible from outside your network. Check that the AyuGram panel is visible in the sidebar. Try clearing your iPhone browser cache.
