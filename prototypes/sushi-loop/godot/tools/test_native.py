#!/usr/bin/env python3
"""Run native tests/captures in a disposable project and a unique save identity.

Examples:
  python3 tools/test_native.py
  python3 tools/test_native.py --script tests/capture.gd --visible --resolution 390x844 -- --output /tmp/review
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", help="Project-relative SceneTree script; default: tests/*_tests.gd")
    parser.add_argument("--visible", action="store_true", help="Use native graphics for captures/input checks")
    parser.add_argument("--size", "--resolution", dest="resolution", default="450x800")
    parser.add_argument("--output", type=Path, help="Capture destination passed to the native script")
    parser.add_argument("--gallery", action="store_true", help="Open the production-component gallery")
    parser.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*x[1-9][0-9]*", args.resolution):
        parser.error("The viewport size must be WIDTHxHEIGHT in positive pixels.")
    environment = os.environ.copy()
    # Godot's headless display ignores --resolution, so SceneTree UI tests use
    # this to configure their root Window before adding the production scene.
    environment["SUSHI_LOOP_TEST_SIZE"] = args.resolution
    if args.output:
        args.output = args.output.resolve()
        args.output.mkdir(parents=True, exist_ok=True)
        environment["SUSHI_LOOP_CAPTURE_OUTPUT"] = str(args.output)
    source = Path(__file__).resolve().parents[1]
    scripts = [args.script] if args.script else [p.relative_to(source).as_posix() for p in sorted((source / "tests").glob("*_tests.gd"))]
    if not scripts:
        parser.error("No native test scripts found.")
    for script in scripts:
        resolved = (source / script).resolve()
        if not resolved.is_relative_to(source) or not resolved.is_file():
            parser.error(f"Test script is not a project file: {script}")
    identity = f"SushiLoopTicketsTest-{uuid.uuid4().hex}"
    # Godot custom data roots are platform-specific; cleanup is restricted to
    # this unpredictable test identity and never the real game's save folder.
    if sys.platform == "darwin":
        data = Path.home() / "Library/Application Support" / identity
    elif sys.platform == "win32":
        data = Path(os.environ["APPDATA"]) / identity
    else:
        data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / identity
    try:
        with tempfile.TemporaryDirectory(prefix="sushi-loop-native-test-") as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(source, project, ignore=shutil.ignore_patterns(".godot", ".local", "build", "android", "__pycache__", "export_credentials.cfg", "*.keystore", "*.jks"))
            config_file = project / "project.godot"
            config = config_file.read_text()
            config = re.sub(r"^config/(?:use_custom_user_dir|custom_user_dir_name)=.*\n?", "", config, flags=re.M)
            config = config.replace("[application]\n", f'[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="{identity}"\n', 1)
            config_file.write_text(config)
            run([args.godot, "--headless", "--path", str(project), "--editor", "--import"], args.timeout, environment)
            for script in scripts:
                command = [args.godot, "--path", str(project), "--resolution", args.resolution]
                command += ["--windowed", "--audio-driver", "Dummy"] if args.visible else ["--headless"]
                command += ["--script", f"res://{script}"]
                extra = args.args[1:] if args.args[:1] == ["--"] else args.args
                if args.output:
                    extra += ["--output", str(args.output)]
                if args.gallery:
                    extra += ["--gallery"]
                if extra:
                    command += ["--", *extra]
                print(f"Running {script} in isolated native session", flush=True)
                run(command, args.timeout, environment)
    finally:
        if data.name == identity:
            shutil.rmtree(data, ignore_errors=True)
    return 0


def run(command: list[str], timeout: int, environment: dict[str, str]) -> None:
    result = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    print(result.stdout, end="", flush=True)
    if result.returncode or re.search(r"(?:^|\n)(?:SCRIPT )?ERROR:", result.stdout):
        raise SystemExit(result.returncode or 1)


if __name__ == "__main__":
    raise SystemExit(main())
