#!/usr/bin/env bash
set -Eeuo pipefail

remote_dir="$1"
serial_device="$2"
requested_service="${3:-}"
esptool="${ESPTOOL:-/home/pi/.venvs/esptool/bin/esptool}"
active=()
enabled=()
for unit in rf-router.service router.service; do
  state=$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)
  case "$state" in activating|deactivating|reloading) echo "Service transition in progress: $unit" >&2; exit 1;; esac
  if systemctl is-active --quiet "$unit"; then active+=("$unit"); fi
  enabled_state=$(systemctl is-enabled "$unit" 2>/dev/null || true)
  case "$enabled_state" in enabled|enabled-runtime) enabled+=("$unit");; esac
done
if (( ${#active[@]} > 1 || ${#enabled[@]} > 1 )); then
  echo 'Ambiguous router services; finish migration or rollback before flashing' >&2
  exit 1
fi
if (( ${#active[@]} == 1 && ${#enabled[@]} == 1 )) && [[ "${active[0]}" != "${enabled[0]}" ]]; then
  echo 'Active and boot-enabled router services differ' >&2; exit 1
fi
service="${requested_service:-${active[0]:-${enabled[0]:-}}}"
case "$service" in rf-router.service|router.service) ;; *) echo 'No valid router service selected' >&2; exit 1;; esac
if [[ "$(systemctl show "$service" -p LoadState --value)" != loaded ]] ||
   [[ "$(systemctl is-enabled "$service" 2>/dev/null || true)" == masked* ]]; then
  echo "Router service unavailable: $service" >&2; exit 1
fi
if (( ${#active[@]} == 1 )) && [[ "${active[0]}" != "$service" ]]; then
  echo 'Selected service conflicts with the active router' >&2; exit 1
fi
if [[ ! -e "$serial_device" || ! -x "$esptool" ]]; then
  echo 'USB device or Pi esptool unavailable' >&2; exit 1
fi
for image in bootloader.bin partitions.bin boot_app0.bin firmware.bin; do
  test -f "$remote_dir/$image"
done
command -v fuser >/dev/null
resident_active=0
if systemctl is-active --quiet resident.service; then resident_active=1; fi

restore_services() {
  result=$?
  trap - EXIT
  set +e
  sudo systemctl start "$service"
  if [[ $? != 0 ]] || ! systemctl is-active --quiet "$service"; then
    echo "RECOVERY FAILED: sudo systemctl start $service" >&2
    result=1
  elif [[ "$resident_active" == 1 ]]; then
    sudo systemctl start resident.service
    if [[ $? != 0 ]] || ! systemctl is-active --quiet resident.service; then
      echo 'RECOVERY FAILED: resident.service' >&2; result=1
    fi
  fi
  exit "$result"
}
trap restore_services EXIT
echo "Flashing with $service temporarily stopped"
sudo systemctl stop "$service"
if sudo fuser "$serial_device" >/dev/null 2>&1; then
  echo 'USB serial is still owned by another process' >&2; exit 1
fi
"$esptool" --chip esp32s3 --port "$serial_device" --baud 460800 \
  --before default-reset --after hard-reset write-flash \
  0x0 "$remote_dir/bootloader.bin" 0x8000 "$remote_dir/partitions.bin" \
  0xe000 "$remote_dir/boot_app0.bin" 0x10000 "$remote_dir/firmware.bin"
rm -f -- "$remote_dir/bootloader.bin" "$remote_dir/partitions.bin" \
  "$remote_dir/boot_app0.bin" "$remote_dir/firmware.bin"
rmdir -- "$remote_dir"
