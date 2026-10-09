#!/usr/bin/env python3
"""Run application integration checks with a unique, disposable Godot user directory."""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import tempfile
import uuid

source = Path(__file__).resolve().parents[1]


def window_size(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\s*[xX×]\s*(\d+)", value.strip())
    if not match or min(map(int, match.groups())) <= 0:
        raise argparse.ArgumentTypeError("Use a positive width and height, such as 720x1600")
    return tuple(map(int, match.groups()))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", action="store_true", help="Capture native application screens instead of running integration assertions")
parser.add_argument("--output", type=Path, default=Path("/tmp/sushi-loop-captures"), help="Screenshot directory when --capture is selected")
parser.add_argument("--size", type=window_size, default=(720, 1280), metavar="WIDTHxHEIGHT", help="Actual window size for aspect-ratio and touch checks (default: 720x1280)")
options = parser.parse_args()
identity = "SushiLoopIntegrationTests-" + uuid.uuid4().hex
with tempfile.TemporaryDirectory(prefix="sushi-loop-test-") as scratch:
    project = Path(scratch)
    for child in source.iterdir():
        if child.name != "project.godot":
            (project / child.name).symlink_to(child, target_is_directory=child.is_dir())
    config = (source / "project.godot").read_text()
    config = re.sub(r"^config/(?:use_custom_user_dir|custom_user_dir_name)=.*\n", "", config, flags=re.MULTILINE)
    config = config.replace("[application]", '[application]\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir_name="' + identity + '"')
    (project / "project.godot").write_text(config)
    report = project / "integration-report.json"
    try:
        width, height = options.size
        command = [shutil.which("godot") or "godot", "--path", str(project), "--resolution", f"{width}x{height}"]
        command += ["--rendering-method", "gl_compatibility"] if options.capture else ["--headless"]
        script = "tests/capture_screens.gd" if options.capture else "tests/app_tests.gd"
        command += ["--script", script, "--", str(report), identity, str(options.output.resolve()), str(width), str(height)]
        completed = subprocess.run(command, timeout=180, check=False, capture_output=True, text=True)
        print(completed.stdout, end="")
        print(completed.stderr, end="")
        error_output = "SCRIPT ERROR:" in completed.stdout + completed.stderr or "ERROR:" in completed.stdout + completed.stderr
        marker = "Captured " if options.capture else "App integration:"
        raise SystemExit(completed.returncode or int(error_output or marker not in completed.stdout))
    finally:
        if report.exists():
            user_directory = Path(json.loads(report.read_text())["user_directory"])
            if user_directory.name == identity:
                shutil.rmtree(user_directory, ignore_errors=True)
