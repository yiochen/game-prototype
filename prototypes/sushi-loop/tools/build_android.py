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
import sys
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parents[1] / "godot"
# The same registration contract powers the catalog-copy CLI and release gate.
sys.path.insert(0, str(PROJECT / "tools"))
import catalog_contract
import verify_recipe_variants as recipe_contract
import verify_chef_variants as chef_contract
import verify_feedback_variants as feedback_contract
import verify_editor_ui as editor_ui_contract
import verify_editor_goods as editor_goods_contract
import verify_wood_ui as wood_ui_contract

ROOT_FILES = ("project.godot", "main.tscn", "branding.json", "export_presets.cfg")
RUNTIME_TREES = {
    "scripts": {".gd", ".gdshader", ".gdshaderinc", ".tscn", ".tres", ".res"},
    "content": {".json"},
    "assets/catalog/sprites": {".png"},
    "assets/recipe-variants/sprites": {".png"},
    "assets/chef-variants/sprites": {".png"},
    "assets/feedback-variants/sprites": {".png"},
    "assets/audio": {".wav", ".ogg", ".mp3"},
    "assets/fonts": {".ttf", ".otf", ".txt"},
    "assets/licenses": {".txt"},
    "assets/ui": {".png", ".webp", ".svg"},
}
FORBIDDEN_PARTS = {".local", "review", "tests", "tools", "provenance", "production"}
FORBIDDEN_SUFFIXES = {".keystore", ".jks", ".blend", ".py", ".bak", ".tmp"}
REVIEW_SCENES = {
    "customer-visits": {"issue": 11, "package_suffix": ".review11", "label": "Customer Visits"},
    "restaurant-editor": {"issue": 12, "package_suffix": ".review12", "label": "Restaurant Editor"},
    "conveyor-routes": {"issue": 13, "package_suffix": ".review13", "label": "Conveyor Routes"},
    "customer-rescue": {"issue": 14, "package_suffix": ".review14", "label": "Customer Rescue"},
}


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
    paths.append(source / "assets/recipe-variants/manifest.json")
    paths.append(source / "assets/chef-variants/manifest.json")
    paths.append(source / "assets/feedback-variants/manifest.json")
    paths.append(source / "assets/ui/editor/manifest.json")
    paths.append(source / "assets/ui/wood-editor/manifest.json")
    paths.append(source / "assets/ui/editor-goods/manifest.json")
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
    manifest, references = catalog_contract.verify_catalog(approved, source / "assets/catalog")
    atlases = {name: path for name, path in files.items() if name.startswith("assets/catalog/sprites/")}
    if {Path(name).relative_to("assets/catalog").as_posix() for name in atlases} != references:
        raise ValueError("The staged atlas selection differs from the verified catalog references.")
    meals = recipe_contract.verify_recipe_variants(source)
    chefs = chef_contract.verify_chef_variants(source)
    feedback = feedback_contract.verify_feedback_variants(source)
    editor_ui = editor_ui_contract.verify_editor_ui(source)
    expected_ui_files = {"assets/ui/editor/manifest.json"} | {
        f"assets/ui/editor/{name}" for name in editor_ui["runtime_images"]}
    if {name for name in files if name.startswith("assets/ui/editor/")} != expected_ui_files:
        raise ValueError("The staged editor UI payload differs from the verified coordinated atlas and manifest.")
    editor_goods = editor_goods_contract.verify_editor_goods(source)
    expected_goods_files = {"assets/ui/editor-goods/manifest.json"} | {
        f"assets/ui/editor-goods/{name}" for name in editor_goods["runtime_images"]}
    if {name for name in files if name.startswith("assets/ui/editor-goods/")} != expected_goods_files:
        raise ValueError("The staged editor goods payload differs from the verified Blender atlas and manifest.")
    wood_ui = wood_ui_contract.verify_wood_ui(source)
    expected_wood_files = {"assets/ui/wood-editor/manifest.json"} | {f"assets/ui/wood-editor/{name}" for name in wood_ui["runtime_images"]}
    if {name for name in files if name.startswith("assets/ui/wood-editor/")} != expected_wood_files:
        raise ValueError("The staged wood UI differs from the verified HTML export.")
    return {
        "wood_ui": wood_ui,
        "wood_ui_manifest_sha256": sha(source / "assets/ui/wood-editor/manifest.json"),
        "object_count": len(manifest["objects"]),
        "atlas_count": len(atlases),
        "atlas_source_bytes": sum(path.stat().st_size for path in atlases.values()),
        "approved_library_sha256": sha(approved_manifest),
        "runtime_manifest_sha256": sha(source / "assets/catalog/manifest.json"),
        "recipe_variants": meals,
        "recipe_manifest_sha256": sha(source / "assets/recipe-variants/manifest.json"),
        "chef_variants": chefs,
        "chef_manifest_sha256": sha(source / "assets/chef-variants/manifest.json"),
        "feedback_variants": feedback,
        "feedback_manifest_sha256": sha(source / "assets/feedback-variants/manifest.json"),
        "editor_ui": editor_ui,
        "editor_ui_manifest_sha256": sha(source / "assets/ui/editor/manifest.json"),
        "editor_goods": editor_goods,
        "editor_goods_manifest_sha256": sha(source / "assets/ui/editor-goods/manifest.json"),
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
    catalog_contract.verify_catalog(source.parent / "assets/production", project / "assets/catalog")
    wood_ui_contract.verify_wood_ui(project, source_project=source)
    recipe_contract.verify_recipe_variants(project, source_project=source)
    chef_contract.verify_chef_variants(project, source_project=source)
    feedback_contract.verify_feedback_variants(project, source_project=source)
    editor_ui_contract.verify_editor_ui(project, source_project=source)
    editor_goods_contract.verify_editor_goods(project, source_project=source)
    return hashes, catalog


def replace(config: str, key: str, value) -> str:
    replacement = f"{key}={json.dumps(value, ensure_ascii=False)}"
    result, count = re.subn(r"^" + re.escape(key) + r"=.*$", lambda _: replacement, config, flags=re.M)
    if count != 1:
        raise ValueError(f"Expected one build setting: {key}")
    return result


def resolve_branding(base: dict, *, title=None, version_name=None, version_code=None,
                     package_id=None, review_scene=None) -> tuple[dict, dict]:
    """Review builds get another Android sandbox, never another gameplay path."""
    branding = dict(base)
    for value, key in [(title, "title"), (version_name, "version_name"),
                       (version_code, "version_code"), (package_id, "android_package")]:
        if value is not None:
            branding[key] = value
    variant = {"kind": "normal", "scene": None, "issue": None,
               "normal_package": base["android_package"]}
    if review_scene is not None:
        if review_scene not in REVIEW_SCENES:
            raise ValueError(f"Unknown isolated review scene: {review_scene}")
        if title is not None or package_id is not None:
            raise ValueError("--review-scene controls its isolated title/package; do not combine it with --title or --package-id.")
        review = REVIEW_SCENES[review_scene]
        branding["title"] = f"{base['title']} · {review['label']}"
        branding["android_package"] = base["android_package"] + review["package_suffix"]
        variant.update(kind="review", scene=review_scene, issue=review["issue"])
    variant["staged_branding_overrides"] = {key: value for key, value in branding.items() if value != base.get(key)}
    return branding, variant


def fingerprint(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def stage_build(source: Path, project: Path, branding: dict) -> tuple[dict, dict, dict]:
    """Apply display/package overrides only to an isolated staged copy."""
    if project.resolve() == source.resolve() or project.resolve().is_relative_to(source.resolve()):
        raise ValueError("Android build staging must be outside the source project.")
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
    return source_files, {name: sha(project / name) for name in source_files}, catalog


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


def parse_apk_badging(badging: str, branding: dict, mode: str) -> dict:
    """Read aapt2 metadata without losing permission or release checks."""
    package = re.search(r"^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging, re.M)
    if not package or package.groups() != (branding["android_package"], str(branding["version_code"]), branding["version_name"]):
        raise ValueError("Exported Android package/version differs from the requested branding.")
    label = re.search(r"^application-label:'(.*)'$", badging, re.M)
    if not label or label.group(1) != branding["title"]:
        raise ValueError("Exported Android app label differs from the requested branding.")
    debuggable = bool(re.search(r"^application-debuggable", badging, re.M))
    if mode == "release" and debuggable:
        raise ValueError("Release APK is unexpectedly debuggable.")
    permissions = re.findall(r"^[ \t]*uses-permission: name='([^']+)'", badging, re.M)
    if mode == "release" and "android.permission.INTERNET" in permissions:
        raise ValueError("The offline release unexpectedly requests Internet permission.")
    minimum = re.search(r"^(?:minSdkVersion|sdkVersion):'([^']+)'", badging, re.M)
    target = re.search(r"^targetSdkVersion:'([^']+)'", badging, re.M)
    return {"package": package.group(1), "application_label": label.group(1), "debuggable": debuggable,
            "min_sdk": minimum.group(1) if minimum else None, "target_sdk": target.group(1) if target else None,
            "permissions": permissions}


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
    # aapt1 rejects Godot's generated Vulkan feature declarations. aapt2 is the
    # current Android parser and handles these declarations without patching APKs.
    badging = run([str(build_tools / "aapt2"), "dump", "badging", str(apk_path)], environment)
    metadata = parse_apk_badging(badging, branding, mode)
    with zipfile.ZipFile(apk_path) as apk:
        names = apk.namelist()
        for architecture in ("arm64-v8a", "x86_64"):
            if not any(name.startswith(f"lib/{architecture}/") for name in names):
                raise ValueError(f"Missing Android {architecture} native library.")
        manifest_path = "assets/assets/catalog/manifest.json"
        if manifest_path not in names:
            raise ValueError("The current runtime catalog manifest is missing from the APK.")
        manifest_hash = hashlib.sha256(apk.read(manifest_path)).hexdigest()
        recipe_manifest_path = "assets/assets/recipe-variants/manifest.json"
        if recipe_manifest_path not in names:
            raise ValueError("The verified native meal-variant manifest is missing from the APK.")
        recipe_manifest_hash = hashlib.sha256(apk.read(recipe_manifest_path)).hexdigest()
        chef_manifest_path = "assets/assets/chef-variants/manifest.json"
        if chef_manifest_path not in names:
            raise ValueError("The verified native chef-variant manifest is missing from the APK.")
        chef_manifest_hash = hashlib.sha256(apk.read(chef_manifest_path)).hexdigest()
        feedback_manifest_path = "assets/assets/feedback-variants/manifest.json"
        if feedback_manifest_path not in names:
            raise ValueError("The verified 2D feedback-variant manifest is missing from the APK.")
        feedback_manifest_hash = hashlib.sha256(apk.read(feedback_manifest_path)).hexdigest()
        editor_ui_manifest_path = "assets/assets/ui/editor/manifest.json"
        if editor_ui_manifest_path not in names:
            raise ValueError("The verified ImageGen editor UI manifest is missing from the APK.")
        editor_ui_manifest_hash = hashlib.sha256(apk.read(editor_ui_manifest_path)).hexdigest()
        editor_goods_manifest_path = "assets/assets/ui/editor-goods/manifest.json"
        if editor_goods_manifest_path not in names:
            raise ValueError("The verified Blender editor goods manifest is missing from the APK.")
        editor_goods_manifest_hash = hashlib.sha256(apk.read(editor_goods_manifest_path)).hexdigest()
        wood_manifest_hash = hashlib.sha256(apk.read("assets/assets/ui/wood-editor/manifest.json")).hexdigest()
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
    return {
        "signer_sha256": signer, **metadata, "runtime_manifest_sha256": manifest_hash,
        "recipe_manifest_sha256": recipe_manifest_hash,
        "chef_manifest_sha256": chef_manifest_hash,
        "feedback_manifest_sha256": feedback_manifest_hash,
        "editor_ui_manifest_sha256": editor_ui_manifest_hash,
        "wood_ui_manifest_sha256": wood_manifest_hash,
        "editor_goods_manifest_sha256": editor_goods_manifest_hash,
        "archive_entries": len(names), "excluded_material_check": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["debug", "release"], nargs="?", default="release",
                        help="Build mode (default: release). Debug-signed APKs cannot update release installs.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--version-name")
    parser.add_argument("--version-code", type=int)
    parser.add_argument("--package-id")
    parser.add_argument("--review-scene", choices=sorted(REVIEW_SCENES), help="Build the same runtime in a separate Android package with fresh isolated app data.")
    parser.add_argument("--godot", default=os.environ.get("GODOT_BIN", "godot"))
    parser.add_argument("--check", action="store_true", help="Validate runtime selection/pixels and SDK; do not import, build or install.")
    args = parser.parse_args()
    source = PROJECT.resolve()
    branding, variant = resolve_branding(json.loads((source / "branding.json").read_text()),
        title=args.title, version_name=args.version_name, version_code=args.version_code,
        package_id=args.package_id, review_scene=args.review_scene)
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
    if not candidates or not all((candidates[-1] / tool).is_file() for tool in ("aapt2", "apksigner")):
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
                          "version_code": branding["version_code"], "build_variant": variant, "catalog": catalog}, indent=2))
        return 0
    credentials, keystore = signing_credentials(source, args.mode, environment, keytool)
    if args.mode == "release":
        verify_release_identity(branding, credentials, keystore, environment, keytool)
    prefix = f"GODOT_ANDROID_KEYSTORE_{args.mode.upper()}"
    environment[f"{prefix}_PATH"] = str(keystore)
    environment[f"{prefix}_USER"] = credentials["alias"]
    environment[f"{prefix}_PASSWORD"] = credentials["password"]
    variant_name = f"{args.review_scene}-review-" if args.review_scene else ""
    output = (args.output or source / "build" / f"sushi-loop-{variant_name}{args.mode}-v{branding['version_name']}.apk").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sushi-loop-android-") as temporary:
        project = Path(temporary) / "project"
        source_files, staged_files, catalog = stage_build(source, project, branding)
        print(f"Importing current runtime catalog with Godot {engine}", flush=True)
        run([args.godot, "--headless", "--path", str(project), "--editor", "--import"], environment, [credentials["password"]])
        print(f"Exporting signed Android {args.mode} APK", flush=True)
        run([args.godot, "--headless", "--path", str(project), f"--export-{args.mode}", "Android", str(output)],
            environment, [credentials["password"]])
    verification = audit_apk(output, branding, args.mode, build_tools, environment, credentials["password"])
    if verification["runtime_manifest_sha256"] != catalog["runtime_manifest_sha256"]:
        raise ValueError("The APK catalog differs from the staged approved catalog.")
    if verification["recipe_manifest_sha256"] != catalog["recipe_manifest_sha256"]:
        raise ValueError("The APK native meal variants differ from the verified staged variants.")
    if verification["chef_manifest_sha256"] != catalog["chef_manifest_sha256"]:
        raise ValueError("The APK native chef variants differ from the verified staged variants.")
    if verification["feedback_manifest_sha256"] != catalog["feedback_manifest_sha256"]:
        raise ValueError("The APK 2D feedback variants differ from the verified staged variants.")
    if verification["editor_ui_manifest_sha256"] != catalog["editor_ui_manifest_sha256"]:
        raise ValueError("The APK ImageGen editor UI differs from the verified staged UI manifest.")
    if verification["editor_goods_manifest_sha256"] != catalog["editor_goods_manifest_sha256"]:
        raise ValueError("The APK Blender editor goods differ from the verified staged goods manifest.")
    if verification["wood_ui_manifest_sha256"] != catalog["wood_ui_manifest_sha256"]:
        raise ValueError("The APK wood UI differs from the verified HTML export.")
    digest = sha(output)
    metadata = branding | {
        "mode": args.mode, "engine": engine, "apk_sha256": digest, "bytes": output.stat().st_size,
        "build_variant": variant, "runtime_source_fingerprint": fingerprint(source_files),
        "staged_source_fingerprint": fingerprint(staged_files),
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
