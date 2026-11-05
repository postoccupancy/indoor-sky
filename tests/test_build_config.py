import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_config.py'


class BuildConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.git('init', '-q')
        self.secrets(self.root)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def secrets(self, project):
        (project / 'secrets.py').write_text('WIFI_SSID = "test-network"\nWIFI_PASS = "test-password"\n')

    def commit(self):
        (self.root / 'tracked.txt').write_text('baseline')
        self.git('add', 'tracked.txt')
        self.git('-c', 'user.name=Build Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def build(self, project=None):
        project = project or self.root
        class Env:
            def subst(self, value):
                return str(project)

            def Append(self, **kwargs):
                pass
        runpy.run_path(str(SCRIPT), init_globals={'env': Env(), 'Import': lambda name: None})
        return (project / '.pio/generated/build_config.h').read_text()

    def test_identity_and_tracked_dirty_state(self):
        self.commit()
        header = self.build()
        self.assertIn(self.git('rev-parse', '--short=12', 'HEAD'), header)
        self.assertIn('#define FIRMWARE_GIT_DIRTY false', header)
        self.assertRegex(header, r'FIRMWARE_BUILD_UTC "\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"')
        (self.root / 'tracked.txt').write_text('changed')
        self.assertIn('#define FIRMWARE_GIT_DIRTY true', self.build())

    def test_missing_committed_head(self):
        with self.assertRaisesRegex(RuntimeError, 'committed HEAD'):
            self.build()

    def test_rejects_parent_git_repository(self):
        self.commit()
        nested = self.root / 'nested'
        nested.mkdir()
        self.secrets(nested)
        with self.assertRaisesRegex(RuntimeError, 'repository root'):
            self.build(nested)

    def test_missing_secrets(self):
        (self.root / 'secrets.py').unlink()
        with self.assertRaisesRegex(RuntimeError, 'secrets.example.py'):
            self.build()


if __name__ == '__main__':
    unittest.main()
