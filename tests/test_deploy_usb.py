import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash') or ('C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else None)


def shellpath(path):
    value = str(path).replace('\\', '/')
    return '/' + value[0].lower() + value[2:] if len(value) > 1 and value[1] == ':' else value


@unittest.skipUnless(BASH and Path(BASH).exists(), 'Bash required')
class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.stage = self.root / 'stage'
        self.stage.mkdir()
        for name in ['bootloader.bin', 'partitions.bin', 'boot_app0.bin', 'firmware.bin']:
            (self.stage / name).write_text('fake image')
        self.serial = self.root / 'serial'
        self.serial.touch()
        self.stub('sudo', 'exec "$@"')
        self.stub('fuser', 'exit "${SERIAL_BUSY:-1}"')
        self.stub('flasher', 'echo flash >> "$FIXTURE/actions"; exit "${FLASH_FAIL:-0}"')
        self.stub('systemctl', '''
command="$1"; shift
unit="${!#}"
if [[ "$command" == show ]]; then
  unit="$1"
  if [[ "$3" == LoadState ]]; then cat "$FIXTURE/$unit.load" 2>/dev/null || echo not-found
  else cat "$FIXTURE/$unit.active" 2>/dev/null || echo inactive; fi
elif [[ "$command" == is-active ]]; then
  [[ "$(cat "$FIXTURE/$unit.active" 2>/dev/null)" == active ]]
elif [[ "$command" == is-enabled ]]; then
  value=$(cat "$FIXTURE/$unit.enabled" 2>/dev/null || echo disabled)
  echo "$value"; [[ "$value" == enabled ]]
elif [[ "$command" == stop ]]; then
  echo "stop $unit" >> "$FIXTURE/actions"
  echo inactive > "$FIXTURE/$unit.active"
  echo inactive > "$FIXTURE/resident.service.active"
elif [[ "$command" == start ]]; then
  echo "start $unit" >> "$FIXTURE/actions"
  test ! -e "$FIXTURE/$unit.fail-start" || exit 1
  echo active > "$FIXTURE/$unit.active"
else exit 99; fi
''')
        self.env = dict(os.environ, FIXTURE=shellpath(self.root),
                        ESPTOOL=shellpath(self.bin / 'flasher'),
                        PATH=shellpath(self.bin) + ':/usr/bin:/bin')

    def stub(self, name, body):
        file = self.bin / name
        file.write_text('#!/usr/bin/env bash\n' + body + '\n', newline='\n')
        file.chmod(0o755)

    def unit(self, name, active='active', enabled='enabled', load='loaded'):
        for suffix, value in [('active', active), ('enabled', enabled), ('load', load)]:
            (self.root / (name + '.' + suffix)).write_text(value)

    def run_flash(self, override=''):
        return subprocess.run([BASH, shellpath(ROOT / 'scripts/flash_usb_on_pi.sh'),
                               shellpath(self.stage), shellpath(self.serial), override],
                              env=self.env, capture_output=True, text=True)

    def actions(self):
        file = self.root / 'actions'
        return file.read_text().splitlines() if file.exists() else []

    def test_old_new_and_rollback(self):
        for name in ['router.service', 'rf-router.service']:
            with self.subTest(name=name):
                self.unit(name)
                other = 'router.service' if name.startswith('rf-') else 'rf-router.service'
                self.unit(other, 'inactive', 'masked', 'masked')
                result = self.run_flash()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.actions()[-3:], ['stop ' + name, 'flash', 'start ' + name])
                self.stage.mkdir()
                for image in ['bootloader.bin', 'partitions.bin', 'boot_app0.bin', 'firmware.bin']:
                    (self.stage / image).touch()

    def test_ambiguous_services_never_stop_or_flash(self):
        self.unit('router.service'); self.unit('rf-router.service')
        self.assertNotEqual(self.run_flash().returncode, 0)
        self.assertEqual(self.actions(), [])

    def test_both_enabled_even_if_only_one_active_rejected(self):
        self.unit('router.service'); self.unit('rf-router.service', 'inactive')
        self.assertNotEqual(self.run_flash('router.service').returncode, 0)
        self.assertEqual(self.actions(), [])

    def test_enabled_service_and_explicit_override(self):
        self.unit('rf-router.service', 'inactive', 'disabled')
        self.assertNotEqual(self.run_flash().returncode, 0)
        result = self.run_flash('rf-router.service')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_masked_override_rejected(self):
        self.unit('rf-router.service', 'inactive', 'masked', 'masked')
        self.assertNotEqual(self.run_flash('rf-router.service').returncode, 0)
        self.assertEqual(self.actions(), [])

    def test_enabled_new_service_selected_when_not_active(self):
        self.unit('rf-router.service', 'inactive', 'enabled')
        result = self.run_flash()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.actions(), ['stop rf-router.service', 'flash', 'start rf-router.service'])

    def test_conflicting_boot_service_and_transition_rejected(self):
        self.unit('rf-router.service', 'active', 'disabled')
        self.unit('router.service', 'inactive', 'enabled')
        self.assertNotEqual(self.run_flash().returncode, 0)
        self.assertEqual(self.actions(), [])
        self.unit('router.service', 'inactive', 'disabled')
        self.unit('rf-router.service', 'activating', 'enabled')
        self.assertNotEqual(self.run_flash().returncode, 0)
        self.assertEqual(self.actions(), [])

    def test_missing_serial_fails_before_stopping_service(self):
        self.unit('rf-router.service')
        self.serial.unlink()
        self.assertNotEqual(self.run_flash().returncode, 0)
        self.assertEqual(self.actions(), [])

    def test_resident_recovery_failure_is_reported(self):
        self.unit('rf-router.service'); self.unit('resident.service')
        (self.root / 'resident.service.fail-start').touch()
        result = self.run_flash()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('RECOVERY FAILED: resident.service', result.stderr)

    def test_flash_failure_restores_router_and_previously_active_resident(self):
        self.unit('rf-router.service'); self.unit('resident.service')
        self.env['FLASH_FAIL'] = '7'
        result = self.run_flash()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(self.actions()[-2:], ['start rf-router.service', 'start resident.service'])

    def test_recovery_failure_is_not_suppressed(self):
        self.unit('rf-router.service')
        (self.root / 'rf-router.service.fail-start').touch()
        result = self.run_flash()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('RECOVERY FAILED', result.stderr)

    def test_busy_serial_never_flashes_and_restores_service(self):
        self.unit('rf-router.service'); self.env['SERIAL_BUSY'] = '0'
        self.assertNotEqual(self.run_flash().returncode, 0)
        self.assertNotIn('flash', self.actions())
        self.assertEqual(self.actions()[-1], 'start rf-router.service')

    def test_host_script_retains_native_paths_and_passes_remote_posix_args(self):
        script = (ROOT / 'scripts/deploy_usb_via_pi.sh').read_text()
        self.assertIn('MSYS_NO_PATHCONV=1 ssh', script)
        self.assertIn('"${ROUTER_SERVICE:-}"', script)
        self.assertIn('penv/Scripts/platformio.exe', script)
        self.assertIn('penv/bin/pio', script)
        for name in ['deploy_usb_via_pi.sh', 'flash_usb_on_pi.sh']:
            result = subprocess.run([BASH, '-n', str(ROOT / 'scripts' / name)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
