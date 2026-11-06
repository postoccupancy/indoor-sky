#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIO_DEFAULT="$HOME/.platformio/penv/bin/pio"
case "${OSTYPE:-}" in
  msys*|cygwin*)
    # Reuse Windows OpenSSH credentials instead of Git's bundled SSH.
    WINDOWS_SSH="$(cygpath -u "$PROGRAMFILES")/OpenSSH"
    if [[ ! -x "$WINDOWS_SSH/ssh.exe" ]]; then
      WINDOWS_SSH="$(cygpath -u "$WINDIR")/System32/OpenSSH"
    fi
    export PATH="$WINDOWS_SSH:$PATH"
    PIO_DEFAULT="$HOME/.platformio/penv/Scripts/platformio.exe"
    ;;
esac
PIO="${PIO:-$PIO_DEFAULT}"
PI_HOST="${PI_HOST:-pi@adrian-pi}"
ENVIRONMENT="${PIO_ENV:-esp32_s3_devkit_usb}"
SERIAL_DEVICE="${INDOOR_SKY_SERIAL_DEVICE:-/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_24:EC:4A:0E:B1:DC-if00}"
BUILD="$ROOT/.pio/build/$ENVIRONMENT"
BOOT_APP0="$HOME/.platformio/packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin"
REMOTE_DIR="/tmp/indoor-sky-flash"

case "${ROUTER_SERVICE:-}" in
  ''|rf-router.service|router.service) ;;
  *) echo 'ROUTER_SERVICE must be rf-router.service or router.service' >&2; exit 1 ;;
esac

echo "Building indoor-sky firmware..."
"$PIO" run -d "$ROOT" -e "$ENVIRONMENT"

for image in "$BUILD/bootloader.bin" "$BUILD/partitions.bin" "$BUILD/firmware.bin" "$BOOT_APP0"; do
  if [[ ! -f "$image" ]]; then
    echo "Missing flash image: $image" >&2
    exit 1
  fi
done

echo "Copying flash images to $PI_HOST..."
ssh "$PI_HOST" "mkdir -p '$REMOTE_DIR'"
scp "$BUILD/bootloader.bin" "$BUILD/partitions.bin" "$BUILD/firmware.bin" "$BOOT_APP0" "$PI_HOST:$REMOTE_DIR/"

echo "Flashing indoor-sky through the Pi USB connection..."
MSYS_NO_PATHCONV=1 ssh "$PI_HOST" bash -s -- "$REMOTE_DIR" "$SERIAL_DEVICE" "${ROUTER_SERVICE:-}" < "$ROOT/scripts/flash_usb_on_pi.sh"

echo "Indoor-sky USB deployment complete; router service recovery verified."
