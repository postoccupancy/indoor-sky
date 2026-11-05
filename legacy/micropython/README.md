# Historical MicroPython prototype

Archived from Weather Brain device/main.py, not part of the PlatformIO build.
This prototype reads an AM2320, imports an LCD module absent from the repository,
and posts authenticated readings directly to Weather Brain /ingest. It is not a
complete runnable distribution and does not implement the current Indoor Sky USB
transport. Do not deploy it as the ESP32-S3 BME280/INMP441 firmware.

The adjacent secrets.example.py preserves historical placeholder settings and the
old DEVICE_ID. That ID is not the current indoor-sky node; no stored identities,
API compatibility or database records are changed by archiving these files.
