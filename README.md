# Indoor Sky

ESP32-S3 DevKitC-1 Arduino/PlatformIO firmware for the Indoor Sky sensor node.
Hardware: ESP32-S3-WROOM-1-N8R8, 8 MB flash and 8 MB octal PSRAM. BME280 SDA/SCL:
GPIO10/9. INMP441 SD/BCLK/WS: GPIO16/17/18, L/R grounded.

Repository ownership:

- [indoor-sky](https://github.com/postoccupancy/indoor-sky): this firmware, USB
  contract and Windows/Mac Pi-assisted flashing.
- [electric-sky](https://github.com/postoccupancy/electric-sky): separate outdoor
  ESP32-S3 CAM firmware.
- [electric-sea](https://github.com/postoccupancy/electric-sea): Raspberry Pi Node.js
  router, serial parser and browser interfaces.
- [weather-brain](https://github.com/postoccupancy/weather-brain): Windows Python
  API, PostgreSQL, archives and analysis.

Extracted from Weather Brain `device/` at
`fa5d79cc5b575cca6fc69510db6205004e62658f` on 2026-11-05. C++ source, wire protocols,
board settings and uploader behavior are preserved. Electric Sea rf-router now owns the canonical dashboard and USB controls. Firmware
Dashboard.h remains only for compatibility with older routers during rollback.
Historical MicroPython code is isolated under `legacy/micropython/`.

Install PlatformIO Core, Git and SSH/SCP. Windows additionally needs Git Bash and
native Windows OpenSSH; macOS uses its existing Bash and SSH credentials.
Copy `secrets.example.py` to ignored `secrets.py` and supply local Wi-Fi credentials.
Both USB and OTA builds currently require those credentials. Never publish `.pio/`
or firmware binaries: the generated header and images contain credentials.

From this repository root, build without uploading:

```bash
# macOS
~/.platformio/penv/bin/pio run -d . -e esp32_s3_devkit_usb
```

```powershell
# Windows PowerShell
& "$env:USERPROFILE/.platformio/penv/Scripts/platformio.exe" run -d . -e esp32_s3_devkit_usb
```

The optional environment `esp32_s3_devkit_ota` preserves the extended-timeout OTA
uploader. A plain `pio run` builds; adding `-t upload` flashes. See
[deployment](docs/deployment.md) before deploying, and [USB protocol](docs/usb-protocol.md).

The known Windows baseline uses espressif32 7.1.3; dependencies retain the original
constraints. New machines should verify resolved versions rather than upgrading
the toolchain during migration. Identity fields retain their names: firmware_git_sha
now identifies this repository's HEAD; firmware_git_dirty reports tracked changes
(untracked files are excluded); firmware_build_utc records the UTC build time.
Builds require a committed HEAD and reject a parent repository as the Git root.

No new blanket license is asserted by this extraction. Original uploader attribution
is retained; consult source provenance before redistributing third-party code.
