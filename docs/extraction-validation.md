# Extraction validation, 2026-11-05

Imported an allowlisted snapshot from Weather Brain fa5d79c into a new history;
no backend history, generated files, binaries or real secrets were imported.
The destination remote had no refs before import.

- Compared all seven unchanged runtime/config/uploader files against Weather
  Brain with only line endings normalized: exact matches. Original legacy source
  and example preserved; active example contains only Wi-Fi placeholders.
- Scanned staged import content for known local password/token values and common
  private-key/GitHub/AWS credential signatures. No matches. This bounded scan is
  not a claim of exhaustive secret detection. Real secrets and generated header
  are ignored; the retained old source artifacts remain private for rollback.
- Windows PlatformIO USB and OTA build-only environments passed with espressif32
  7.1.3, 8 MB flash/octal PSRAM configuration and original partition layout.
- Four isolated build-config tests passed: committed identity/UTC and tracked
  dirty state, missing HEAD, wrong parent Git root, and missing secrets.
- Bash syntax passed; LF checkout policy and executable script mode retained.
  Native Windows SSH/SCP reused existing credentials. Harmless SCP round trip
  matched SHA256; remote probe removed. Pi esptool 5.3.1, serial by-id read/write
  permissions and passwordless sudo confirmed without opening serial.
- Electric Sea's existing 121 router tests passed; no parser or runtime changes.
- The existing VS Code multi-root workspace already includes sibling indoor-sky.
- Router PID 3510 and start time 2026-11-05 12:44:50 PST remained unchanged.

No firmware flash, service restart, API/database change or outdoor Electric Sky
change was performed for extraction. A real macOS build/SSH/deployment validation
remains outstanding; Darwin retains original Unix tool paths and Windows-only
tool selection is conditional. Hardware deployment from the new checkout is a
separate requested action, not part of this source migration.

Run build-config tests with `python -m unittest discover -s tests -v`.
The imported upstream uploader and historical MicroPython file retain their
existing whitespace and attribution; runtime source was not reformatted.
