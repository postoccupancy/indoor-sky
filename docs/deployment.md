# Build and Pi-assisted USB deployment

The PlatformIO project is this repository root, not `weather-brain/device`.
Use the build-only commands in README to validate without touching hardware.
Both original environments, partition layout, USB CDC and octal PSRAM remain intact.

The Pi needs `/home/pi/.venvs/esptool/bin/esptool`, passwordless sudo for router
service control and serial access. Default host: `pi@adrian-pi`; default device:
`/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:EC:4A:0E:B1:DC-if00`.
Use each computer's existing SSH identity; no private keys belong in this repo.

Safe preflight (does not open serial or interrupt router):

```bash
bash -n scripts/deploy_usb_via_pi.sh
ssh -o BatchMode=yes pi@adrian-pi 'hostname; /home/pi/.venvs/esptool/bin/esptool version; ls -l /dev/serial/by-id/; systemctl is-active router; sudo -n -l'
```

Also copy a harmless temporary text file with SCP to/from a dedicated Pi `/tmp`
path, compare hashes, then remove that probe. On Windows, use native OpenSSH/SCP.
In Codex a restricted execution sandbox may deny networking before authentication;
use approved outside-sandbox execution, reusing existing Windows credentials.

Only when a flash and brief router interruption are intended:

```bash
# macOS, from repository root
bash scripts/deploy_usb_via_pi.sh
```

```powershell
# Windows PowerShell, from repository root
& 'C:/Program Files/Git/bin/bash.exe' scripts/deploy_usb_via_pi.sh
```

The script builds, copies all four images to `/tmp/indoor-sky-flash`, stops router,
flashes via the Pi's USB port, resets the ESP32, removes remote staging and starts
router via an EXIT trap. Flash addresses: bootloader 0x0, partitions 0x8000,
boot_app0 0xe000, application 0x10000. Do not run concurrently.

`PIO`, `PI_HOST`, `PIO_ENV` and `INDOOR_SKY_SERIAL_DEVICE` remain overrides. PIO_ENV
must retain the same flash/partition layout. BOOT_APP0 assumes packages under
`$HOME/.platformio`; a custom PlatformIO core/package directory needs corresponding
path adjustment. Windows uses native SSH/SCP, `penv/Scripts/platformio.exe` and
`MSYS_NO_PATHCONV=1` for remote POSIX arguments. macOS keeps `penv/bin/pio` and its
normal PATH; the MSYS variable has no effect there. Scripts use LF line endings.

After flashing, check esptool verified every image and router actually recovered:

```bash
ssh pi@adrian-pi 'systemctl is-active router; NO_PROXY=127.0.0.1 curl -kfsS https://127.0.0.1:3000/indoor-sky/status'
```

Check identity against this repo HEAD/build UTC, healthy BME/mic (~100/250 Hz), USB
packet progression, stable gap counts and no growing send failures or drops. Open
`https://adrian-pi:3000/indoor-sky/` and verify live data and optional PCM controls.
`-k` above is for the address-based TLS check; certificates are unchanged.

The existing trap suppresses router start errors. If deployment fails, explicitly
check service state/logs and, when necessary, restore with `sudo systemctl start router`.
Retain a private known-good build for recovery; do not publish credential-bearing
artifacts. Flashing erases/replaces image regions, not the complete NVS partition.

Extraction validation is build/preflight only. A real macOS build and deployment
still require validation on a Mac; Windows checks cannot establish macOS execution.
