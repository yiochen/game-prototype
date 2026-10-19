#!/usr/bin/env python3
"""Stage only current runtime files, export Android, and audit the signed APK."""
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
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parents[1] / "godot"
ROOT_FILES = ("project.godot", "main.tscn", "branding.json", "export_presets.cfg")
RUNTIME_TREES = {
    "scripts": {".gd", ".gdshader", ".gdshaderinc", ".tscn", ".tres", ".res"},
    "content": {".json"},
    "assets/catalog/sprites": {".png"},
    "assets/audio": {".wav", ".ogg", ".mp3"},
    "assets/fonts": {".ttf", ".otf", ".txt"},
    "assets/licenses": {".txt"},
    "assets/ui": {".png", ".webp", ".svg"},
}
FORBIDDEN_PARTS = {".local", "review", "tests", "tools", "provenance", "production"}
FORBIDDEN_SUFFIXES = {".keystore", ".jks", ".blend", ".py", ".bak", ".tmp"}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    return digest.hexdigest()


def runtime_sources(source: Path) -> dict[str, Path]:
    """An allowlist prevents old artwork/authoring files entering the importer."""
    source = source.resolve()
    paths = [source / name for name in ROOT_FILES]
    paths.append(source / "assets/catalog/manifest.json")
    for directory, suffixes in RUNTIME_TREES.items():
        paths.extend(path for path in (source / directory).rglob("*")
                     if path.is_file() and path.suffix.lower() in suffixes)
    result = {}
    for path in sorted(set(paths)):
        if not path.is_file():
            raise ValueError(f"Required runtime file is missing: {path.relative_to(source)}")
        relative = path.relative_to(source).as_posix()
        if not path.resolve().is_relative_to(source):
            raise ValueError(f"Runtime file points outside the project: {relative}")
        if set(Path(relative).parts) & FORBIDDEN_PARTS or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ValueError(f"Authoring/private file selected for runtime: {relative}")
        result[relative] = path
    if not any(name.startswith("assets/catalog/sprites/") for name in result):
        raise ValueError("Import the approved issue #33 runtime catalog before building Android.")
    if "assets/ui/app_icon.png" not in result:
        raise ValueError("The wordless runtime app icon is missing.")
    for name, path in result.items():
        if path.suffix in {".gd", ".tscn", ".godot", ".tres"}:
            if re.search(r"res://(?:assets/(?:production|provenance)/|(?:review|tests|tools)/)", path.read_text()):
                raise ValueError(f"Runtime still references excluded old art/authoring files: {name}")
    return result


def validate_catalog(source: Path, files: dict[str, Path]) -> dict:
    approved = source.parent / "assets/production"
    approved_manifest = approved / "library.json"
    library = json.loads(approved_manifest.read_text())
    if library.get("approval", {}).get("finalAssets") != "approved":
        raise ValueError("The source scene-art catalog is not approved.")
    atlases = {name: path for name, path in files.items() if name.startswith("assets/catalog/sprites/")}
    for name, path in atlases.items():
        original = approved / Path(name).relative_to("assets/catalog")
        if not original.is_file() or sha(path) != sha(original):
            raise ValueError(f"Runtime atlas differs from approved source pixels: {name}")
    return {
        "atlas_count": len(atlases),
        "atlas_source_bytes": sum(path.stat().st_size for path in atlases.values()),
        "approved_library_sha256": sha(approved_manifest),
        "runtime_manifest_sha256": sha(source / "assets/catalog/manifest.json"),
    }


def stage_runtime(source: Path, project: Path) -> tuple[dict[str, str], dict]:
    files = runtime_sources(source)
    catalog = validate_catalog(source, files)
    hashes = {}
    for relative, path in files.items():
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        hashes[relative] = sha(destination)
        if hashes[relative] != sha(path):
            raise ValueError(f"Runtime source changed while staging: {relative}")
    return hashes, catalog


def replace(config: str, key: str, value) -> str:
    replacement = f"{key}={json.dumps(value, ensure_ascii=False)}"
    result, count = re.subn(r"^" + re.escape(key) + r"=.*$", lambda _: replacement, config, flags=re.M)
    if count != 1:
        raise ValueError(f"Expected one build setting: {key}")
    return result


def run(command: list[str], environment: dict[str, str], private_values=()) -> str:
    result = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout)
    for value in private_values:
        if value:
            output = output.replace(value, "<redacted>")
    if result.returncode or re.search(r"(?:^|\n)(?:SCRIPT )?ERROR:", output):
        raise RuntimeError(output.strip() or f"Build command failed with exit {result.returncode}")
    return output


def signing_credentials(source: Path, mode: str, environment: dict[str, str], keytool: str) -> tuple[dict, Path]:
    directory = Path(environment.get("SUSHI_LOOP_SIGNING_DIR", str(source / ".local/signing"))).expanduser().resolve()
    if directory.is_relative_to(source) and not directory.is_relative_to(source / ".local"):
        raise ValueError("Signing material must be outside the project or inside its ignored .local directory.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    credential_file = directory / f"{mode}.json"
    keystore = directory / f"{mode}.keystore"
    if credential_file.exists() != keystore.exists():
        raise ValueError("Signing files are incomplete; restore the matching private credentials and keystore.")
    if not credential_file.exists():
        if mode == "release":
            raise ValueError("Restore the original release signing files. A new key cannot update the existing app or preserve its installed data.")
        credentials = {"alias": "sushi-loop-debug", "password": secrets.token_urlsafe(36)}
        key_environment = environment | {"SUSHI_LOOP_KEY_PASSWORD": credentials["password"]}
        run([keytool, "-genkeypair", "-keystore", str(keystore), "-alias", credentials["alias"],
             "-keyalg", "RSA", "-keysize", "3072", "-validity", "10000", "-storetype", "PKCS12",
             "-storepass:env", "SUSHI_LOOP_KEY_PASSWORD", "-keypass:env", "SUSHI_LOOP_KEY_PASSWORD",
             "-dname", "CN=Sushi Loop Native,O=Game Prototypes,C=US"], key_environment, [credentials["password"]])
        descriptor = os.open(credential_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(credentials, stream)
        keystore.chmod(0o600)
    else:
        try:
            credentials = json.loads(credential_file.read_text())
        except (ValueError, OSError):
            raise ValueError("Cannot read the private signing credentials.") from None
    if not all(isinstance(credentials.get(key), str) and credentials[key] for key in ("alias", "password")):
        raise ValueError("Private signing credentials must contain a nonempty alias and password.")
    return credentials, keystore


def verify_release_identity(branding: dict, credentials: dict, keystore: Path,
                            environment: dict[str, str], keytool: str) -> None:
    """Refuse an incompatible key before importing the complete sprite catalog."""
    key_environment = environment | {"SUSHI_LOOP_KEY_PASSWORD": credentials["password"]}
    certificate = run([keytool, "-J-Duser.language=en", "-list", "-v", "-keystore", str(keystore),
                       "-alias", credentials["alias"], "-storepass:env", "SUSHI_LOOP_KEY_PASSWORD"],
                      key_environment, [credentials["password"]])
    match = re.search(r"SHA256:\s*([A-Fa-f0-9:]+)", certificate)
    expected = branding.get("release_signer_sha256", "").lower()
    if not match or not re.fullmatch(r"[a-f0-9]{64}", expected) or match.group(1).replace(":", "").lower() != expected:
        raise ValueError("The private release key differs from the pinned update identity.")


def audit_apk(apk_path: Path, branding: dict, mode: str, build_tools: Path,
              environment: dict[str, str], password: str) -> dict:
    verification = run([str(build_tools / "apksigner"), "verify", "--verbose", "--print-certs", str(apk_path)],
                       environment, [password])
    fingerprint = re.search(r"Signer #1 certificate SHA-256 digest: (\S+)", verification)
    if not fingerprint:
        raise ValueError("The APK signer certificate could not be verified.")
    signer = fingerprint.group(1).lower()
    expected_signer = branding.get("release_signer_sha256", "").lower()
    if mode == "release" and (not re.fullmatch(r"[a-f0-9]{64}", expected_signer) or signer != expected_signer):
        raise ValueError("Release certificate differs from the pinned update identity.")
    badging = run([str(build_tools / "aapt"), "dump", "badging", str(apk_path)], environment)
    package = re.search(r"^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging, re.M)
    if not package or package.groups() != (branding["android_package"], str(branding["version_code"]), branding["version_name"]):
        raise ValueError("Exported Android package/version differs from the requested branding.")
    debuggable = bool(re.search(r"^application-debuggable", badging, re.M))
    if mode == "release" and debuggable:
        raise ValueError("Release APK is unexpectedly debuggable.")
    with zipfile.ZipFile(apk_path) as apk:
        names = apk.namelist()
        for architecture in ("arm64-v8a", "x86_64"):
            if not any(name.startswith(f"lib/{architecture}/") for name in names):
                raise ValueError(f"Missing Android {architecture} native library.")
        manifest_path = "assets/assets/catalog/manifest.json"
        if manifest_path not in names:
            raise ValueError("The current runtime catalog manifest is missing from the APK.")
        manifest_hash = hashlib.sha256(apk.read(manifest_path)).hexdigest()
        needle = password.encode()
        for name in names:
            parts = set(Path(name).parts)
            if parts & FORBIDDEN_PARTS or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES:
                raise ValueError(f"APK contains excluded authoring/private/legacy material: {name}")
            with apk.open(name) as stream:
                previous = b""
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    data = previous + chunk
                    if needle and needle in data:
                        raise ValueError("The APK contains signing credentials.")
                    previous = data[-max(1, len(needle) - 1):]
    permissions = re.findall(r"^uses-permission: name='([^']+)'", badging, re.M)
    if mode == "release" and "android.permission.INTERNET" in permissions:
        raise ValueError("The offline release unexpectedly requests Internet permission.")
    minimum = re.search(r"^sdkVersion:'([^']+)'", badging, re.M)
    target = re.search(r"^targetSdkVersion:'([^']+)'", badging, re.M)
    return {
        "signer_sha256": signer, "package": package.group(1), "debuggable": debuggable,
        "min_sdk": minimum.group(1) if minimum else None, "target_sdk": target.group(1) if target else None,
        "permissions": permissions, "runtime_manifest_sha256": manifest_hash,
        "archive_entries": len(names), "excluded_material_check": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["debug", "release"], nargs="?", default="debug")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--version-name")
    parser.add_argument("--version-code", type=int)
    parser.add_argument("--package-id")
    parser.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    parser.add_argument("--check", action="store_true", help="Validate runtime selection/pixels and SDK; do not import, build or install.")
    args = parser.parse_args()
    source = PROJECT.resolve()
    branding = json.loads((source / "branding.json").read_text())
    for argument, key in [("title", "title"), ("version_name", "version_name"), ("version_code", "version_code"), ("package_id", "android_package")]:
        if (value := getattr(args, argument)) is not None:
            branding[key] = value
    if not branding["title"].strip() or not branding["version_name"].strip() or int(branding["version_code"]) < 1:
        parser.error("Title, version name and a positive version code are required.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+", branding["android_package"]):
        parser.error("The Android package must be a reverse-domain identifier.")
    environment = os.environ.copy()
    jdk = Path(environment.get("JAVA_HOME", "/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"))
    keytool = str(jdk / "bin/keytool")
    if not Path(keytool).is_file():
        parser.error("JDK17 keytool was not found; configure JAVA_HOME.")
    environment["JAVA_HOME"] = str(jdk)
    environment["PATH"] = str(jdk / "bin") + os.pathsep + environment.get("PATH", "")
    sdk = Path(environment.get("ANDROID_HOME", environment.get("ANDROID_SDK_ROOT", str(Path.home() / "Library/Android/sdk"))))
    candidates = sorted((sdk / "build-tools").glob("*"), key=lambda p: tuple(int(x) for x in re.findall(r"\d+", p.name)))
    if not candidates or not all((candidates[-1] / tool).is_file() for tool in ("aapt", "apksigner")):
        parser.error("Android SDK build-tools were not found; configure ANDROID_HOME.")
    build_tools = candidates[-1]
    engine = run([args.godot, "--version"], environment).strip()
    if not engine.startswith("4.7."):
        parser.error(f"This project targets Godot4.7.x; installed engine is {engine}.")
    files = runtime_sources(source)
    catalog = validate_catalog(source, files)
    if args.check:
        print(json.dumps({"mode": "runtime-preflight-only", "engine": engine, "runtime_files": len(files),
                          "android_package": branding["android_package"], "version_name": branding["version_name"],
                          "version_code": branding["version_code"], "catalog": catalog}, indent=2))
        return 0
    credentials, keystore = signing_credentials(source, args.mode, environment, keytool)
    if args.mode == "release":
        verify_release_identity(branding, credentials, keystore, environment, keytool)
    prefix = f"GODOT_ANDROID_KEYSTORE_{args.mode.upper()}"
    environment[f"{prefix}_PATH"] = str(keystore)
    environment[f"{prefix}_USER"] = credentials["alias"]
    environment[f"{prefix}_PASSWORD"] = credentials["password"]
    output = (args.output or source / "build" / f"sushi-loop-issue-10-{args.mode}.apk").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sushi-loop-android-") as temporary:
        project = Path(temporary) / "project"
        source_files, catalog = stage_runtime(source, project)
        config_file = project / "project.godot"
        config = config_file.read_text()
        for key, value in [("config/name", branding["title"]), ("config/version", branding["version_name"]),
                           ("config/custom_user_dir_name", branding["save_identity"])]:
            config = replace(config, key, value)
        config_file.write_text(config)
        presets_file = project / "export_presets.cfg"
        presets = presets_file.read_text()
        for key, value in [("package/name", branding["title"]), ("package/unique_name", branding["android_package"]),
                           ("version/name", branding["version_name"]), ("version/code", int(branding["version_code"]))]:
            presets = replace(presets, key, value)
        presets_file.write_text(presets)
        (project / "branding.json").write_text(json.dumps(branding, indent=2) + "\n")
        staged_files = {name: sha(project / name) for name in source_files}
        print(f"Importing current runtime catalog with Godot {engine}", flush=True)
        run([args.godot, "--headless", "--path", str(project), "--editor", "--import"], environment, [credentials["password"]])
        print(f"Exporting signed Android {args.mode} APK", flush=True)
        run([args.godot, "--headless", "--path", str(project), f"--export-{args.mode}", "Android", str(output)],
            environment, [credentials["password"]])
    verification = audit_apk(output, branding, args.mode, build_tools, environment, credentials["password"])
    if verification["runtime_manifest_sha256"] != catalog["runtime_manifest_sha256"]:
        raise ValueError("The APK catalog differs from the staged approved catalog.")
    digest = sha(output)
    metadata = branding | {
        "mode": args.mode, "engine": engine, "apk_sha256": digest, "bytes": output.stat().st_size,
        "source_files": source_files, "staged_source_files": staged_files, "catalog": catalog, **verification,
    }
    output.with_suffix(".build.json").write_text(json.dumps(metadata, indent=2) + "\n")
    output.with_suffix(".apk.sha256").write_text(f"{digest}  {output.name}\n")
    print(f"Verified APK: {output}\nSHA-256: {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error)) from None
