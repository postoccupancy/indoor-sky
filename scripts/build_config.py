Import("env")

import ast
import datetime
import json
import subprocess
from pathlib import Path


project_dir = Path(env.subst("$PROJECT_DIR")).resolve()
repo_dir = project_dir
generated_dir = project_dir / ".pio" / "generated"
generated_dir.mkdir(parents=True, exist_ok=True)


def read_assignments(path):
    values = {}
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name):
            try:
                values[target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return values


secrets_path = project_dir / "secrets.py"
if not secrets_path.exists():
    raise RuntimeError("Copy secrets.example.py to secrets.py and add Wi-Fi credentials")

secrets = read_assignments(secrets_path)
for key in ("WIFI_SSID", "WIFI_PASS"):
    if not secrets.get(key):
        raise RuntimeError(f"Missing {key} in {secrets_path}")


def git(*args):
    return subprocess.check_output(
        ["git", "-C", str(repo_dir), *args], text=True
    ).strip()


try:
    git_root = Path(git("rev-parse", "--show-toplevel")).resolve()
    if git_root != project_dir:
        raise RuntimeError("PlatformIO project must be the Indoor Sky Git repository root")
    sha = git("rev-parse", "--short=12", "HEAD")
except subprocess.CalledProcessError as exc:
    raise RuntimeError("Build from the Indoor Sky repository with a committed HEAD") from exc
dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
build_utc = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

header = generated_dir / "build_config.h"
header.write_text(
    "#pragma once\n"
    f"#define WIFI_SSID {json.dumps(str(secrets['WIFI_SSID']))}\n"
    f"#define WIFI_PASSWORD {json.dumps(str(secrets['WIFI_PASS']))}\n"
    f"#define FIRMWARE_GIT_SHA {json.dumps(sha)}\n"
    f"#define FIRMWARE_GIT_DIRTY {'true' if dirty else 'false'}\n"
    f"#define FIRMWARE_BUILD_UTC {json.dumps(build_utc)}\n"
)

env.Append(CPPPATH=[str(generated_dir)])
