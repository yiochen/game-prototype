#!/usr/bin/env bash
# Build a fresh copy, keeping signing secrets and generated files out of Git.
# Requires Godot 4.7.x with matching export templates, JDK 17 and configured SDK.
set -euo pipefail
script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$script_directory/../godot" "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import zipfile

source = Path(sys.argv.pop(1)).resolve()
parser = argparse.ArgumentParser(description="Build and verify the native starter-restaurant APK.")
parser.add_argument("mode", choices=["debug", "release"], nargs="?", default="debug")
parser.add_argument("--output", type=Path)
parser.add_argument("--title")
parser.add_argument("--version-name")
parser.add_argument("--version-code", type=int)
parser.add_argument("--package-id")
parser.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
args = parser.parse_args()
branding = json.loads((source / "branding.json").read_text())
for argument, key in [("title", "title"), ("version_name", "version_name"), ("version_code", "version_code"), ("package_id", "android_package")]:
    value = getattr(args, argument)
    if value is not None:
        branding[key] = value
if not branding["title"].strip() or not branding["version_name"].strip() or int(branding["version_code"]) < 1:
    parser.error("Title, version name and a positive Android version code are required.")
if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", branding["android_package"]):
    parser.error("The Android package must be a reverse-domain identifier.")
output = (args.output or source / "build" / f"sushi-loop-issue-10-{args.mode}.apk").resolve()
output.parent.mkdir(parents=True, exist_ok=True)
environment = os.environ.copy()
jdk = Path(environment.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"))
keytool = str(jdk / "bin/keytool") if (jdk / "bin/keytool").is_file() else shutil.which("keytool")
if not keytool:
    parser.error("JDK 17 keytool was not found. Set JAVA_HOME to the installed JDK.")
if (jdk / "bin/java").is_file():
    environment["JAVA_HOME"] = str(jdk)
    environment["PATH"] = str(jdk / "bin") + os.pathsep + environment.get("PATH", "")
sdk = Path(environment.get("ANDROID_HOME", environment.get("ANDROID_SDK_ROOT", str(Path.home() / "Library/Android/sdk"))))
build_tools = sorted((sdk / "build-tools").glob("*"), key=lambda p: tuple(int(x) for x in re.findall(r"\d+", p.name)))
if not build_tools or not (build_tools[-1] / "apksigner").is_file():
    parser.error("Android SDK build-tools were not found. Set ANDROID_HOME to the SDK.")
signing = Path(environment.get("SUSHI_LOOP_SIGNING_DIR", str(source / ".local/signing"))).expanduser().resolve()
if signing.is_relative_to(source) and not signing.is_relative_to(source / ".local"):
    parser.error("SUSHI_LOOP_SIGNING_DIR must be outside the project, or inside its ignored .local directory.")
signing.mkdir(parents=True, exist_ok=True, mode=0o700)
signing.chmod(0o700)
credentials_file = signing / f"{args.mode}.json"
keystore = signing / f"{args.mode}.keystore"
if credentials_file.exists() != keystore.exists():
    parser.error(f"Signing files are incomplete in {signing}; restore the matching credentials and keystore.")
if not credentials_file.exists():
    credentials = {"alias": f"sushi-loop-{args.mode}", "password": secrets.token_urlsafe(36)}
    key_environment = environment | {"SUSHI_LOOP_KEY_PASSWORD": credentials["password"]}
    subprocess.run([keytool, "-genkeypair", "-keystore", str(keystore), "-alias", credentials["alias"], "-keyalg", "RSA", "-keysize", "3072", "-validity", "10000", "-storetype", "PKCS12", "-storepass:env", "SUSHI_LOOP_KEY_PASSWORD", "-keypass:env", "SUSHI_LOOP_KEY_PASSWORD", "-dname", "CN=Sushi Loop Native,O=Game Prototypes,C=US"], env=key_environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    descriptor = os.open(credentials_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as file:
        json.dump(credentials, file)
    keystore.chmod(0o600)
else:
    credentials = json.loads(credentials_file.read_text())
prefix = f"GODOT_ANDROID_KEYSTORE_{args.mode.upper()}"
environment[f"{prefix}_PATH"] = str(keystore)
environment[f"{prefix}_USER"] = credentials["alias"]
environment[f"{prefix}_PASSWORD"] = credentials["password"]

def run(command):
    result = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode or re.search(r"(?:^|\n)(?:SCRIPT )?ERROR:", result.stdout):
        print(result.stdout)
        raise SystemExit(result.returncode or 1)
    return result.stdout

def replace(config, key, value):
    replacement = f"{key}={json.dumps(value, ensure_ascii=False)}"
    result, count = re.subn(r"^" + re.escape(key) + r"=.*$", lambda _: replacement, config, flags=re.M)
    if count != 1:
        raise SystemExit(f"Expected one build setting: {key}")
    return result

engine_version = run([args.godot, "--version"]).strip()
if not engine_version.startswith("4.7."):
    parser.error(f"This project targets Godot 4.7.x; installed engine is {engine_version}.")
with tempfile.TemporaryDirectory(prefix="sushi-loop-android-") as temporary:
    project = Path(temporary) / "project"
    shutil.copytree(source, project, ignore=shutil.ignore_patterns(".godot", ".local", "build", "android", "__pycache__", "export_credentials.cfg", "*.keystore", "*.jks"))
    source_files = {
        path.relative_to(project).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(project.rglob("*"))
        if path.is_file() and path.suffix.lower() in (".gd", ".tscn", ".godot", ".cfg", ".json", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ttf", ".otf", ".wav", ".ogg")
        and path.relative_to(project).parts[0] not in ("tests", "tools", "review")
        and "provenance" not in path.relative_to(project).parts
    }
    config_file = project / "project.godot"
    config = config_file.read_text()
    for key, value in [("config/name", branding["title"]), ("config/version", branding["version_name"]), ("config/custom_user_dir_name", branding["save_identity"])]:
        config = replace(config, key, value)
    config_file.write_text(config)
    presets_file = project / "export_presets.cfg"
    presets = presets_file.read_text()
    for key, value in [("package/name", branding["title"]), ("package/unique_name", branding["android_package"]), ("version/name", branding["version_name"]), ("version/code", int(branding["version_code"]))]:
        presets = replace(presets, key, value)
    presets_file.write_text(presets)
    (project / "branding.json").write_text(json.dumps(branding, indent=2) + "\n")
    print(f"Importing fresh native project with Godot {engine_version}", flush=True)
    run([args.godot, "--headless", "--path", str(project), "--editor", "--import"])
    print(f"Exporting signed Android {args.mode} APK", flush=True)
    run([args.godot, "--headless", "--path", str(project), f"--export-{args.mode}", "Android", str(output)])
verification = run([str(build_tools[-1] / "apksigner"), "verify", "--verbose", "--print-certs", str(output)])
with zipfile.ZipFile(output) as apk:
    names = apk.namelist()
    for architecture in ["arm64-v8a", "x86_64"]:
        if not any(name.startswith(f"lib/{architecture}/") for name in names):
            raise SystemExit(f"Missing Android {architecture} native library.")
    for name in names:
        if name.lower().endswith((".keystore", ".jks")) or credentials["password"].encode() in apk.read(name):
            raise SystemExit("The APK contains local signing material; refusing to accept the build.")
digest = hashlib.sha256(output.read_bytes()).hexdigest()
fingerprint = re.search(r"Signer #1 certificate SHA-256 digest: (\S+)", verification)
metadata = branding | {"mode": args.mode, "engine": engine_version, "apk_sha256": digest, "signer_sha256": fingerprint.group(1) if fingerprint else "", "bytes": output.stat().st_size, "source_files": source_files}
output.with_suffix(".build.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(f"Verified APK: {output}\nSHA-256: {digest}")
PY
