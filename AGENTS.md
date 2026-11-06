# Indoor Sky firmware

Read README.md, docs/deployment.md and docs/usb-protocol.md before firmware work.
Preserve node IDs, USB/OSC contracts, hardware settings and both Windows/Mac host
workflows. Keep secrets.py, .pio and binaries out of Git and public artifacts.
Build-only validation never requires opening serial or restarting router. Deploy
only when requested, and verify router recovery and live USB status afterward.
Firmware identity must come from this repository's committed HEAD.
For live flashing, fetch the approved remote revision into a separate clean
deployment checkout, provision ignored secrets there and build there. Do not
flash artifacts or transfer code directly from the development workspace.
