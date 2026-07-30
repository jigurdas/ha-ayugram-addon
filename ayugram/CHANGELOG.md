# Changelog

## 1.3.5
### Fixed
- Fixed KasmVNC startup for Home Assistant Ingress.
- Removed forced `-sslOnly` flag from the KasmVNC startup command.
- Fixed internal HTTP/WebSocket support when running behind Home Assistant Ingress.
- Updated KasmVNC configuration for version 1.3.x.
- Improved X11 environment propagation for AyuGram startup.
- Fixed AyuGram display initialization inside the Kasm session.
- Updated Docker image build process.

### Changed
- Switched to the official KasmVNC 1.3 configuration layout.
- Improved container startup sequence.
- Improved compatibility with newer KasmWeb base images.

---

## 1.3.4
### Added
- Automatic AyuGram binary bootstrap system.
- Automatic download of upstream AyuGram releases.
- Automatic release metadata generation.
- GitHub Release based binary distribution.
- Release validation using SHA-256 hashes.
- Build input hashing to detect when a rebuild is required.

### Changed
- Repository no longer stores large AyuGram binaries.
- Build pipeline now downloads binaries from GitHub Releases.
- Improved GitHub Actions workflows.

### Fixed
- Fixed release asset detection.
- Fixed release bootstrap process.
- Fixed metadata generation.

---

## 1.3.3
### Added
- Separate GitHub Actions workflow for building AyuGram binaries.
- Automatic release downloader scripts.
- Bootstrap utility for publishing AyuGram releases.

### Changed
- Refactored CI/CD architecture.
- Improved release management.

---

## 1.3.2
### Fixed
- Fixed KasmVNC configuration for Home Assistant.
- Fixed compatibility with KasmVNC 1.4.x.
- Fixed Ingress configuration.
- Fixed internal WebSocket handling.

### Changed
- Added custom KasmVNC configuration.
- Updated Docker image configuration.

---

## 1.2.0
### Added
- Home Assistant Ingress support.
- Improved Docker image.
- Automatic AyuGram startup.
- Desktop launcher.
- Better Home Assistant integration.

### Fixed
- Various startup issues.
- Container stability improvements.

---

## 1.1.0
### Added
- Browser-based AyuGram desktop.
- Persistent user profile.
- File upload and download support.
- KasmVNC integration.

---

## 1.0.0
### Added
- Initial release.
- AyuGram Desktop running inside a Docker container.
- Home Assistant add-on.
- Home Assistant sidebar panel.
- Home Assistant Ingress support.
- Telegram icon integration.