#!/usr/bin/env bash
# Build a non-debug exhibition APK with a persistent, local-only test signer.
# Signing material stays in ignored builds/signing; this is not a Play Store key.
set -euo pipefail
umask 077

prototype_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_dir="$prototype_dir/godot"
build_dir="$prototype_dir/builds"
signing_dir="$build_dir/signing"
godot_bin="${GODOT_BIN:-godot}"
android_sdk="${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}"
java_sdk="${JDK17_HOME:-/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home}"

command -v rg >/dev/null || { echo 'ripgrep is required for build validation.' >&2; exit 1; }
command -v "$godot_bin" >/dev/null || { echo 'Godot CLI is required.' >&2; exit 1; }
[[ -x "$java_sdk/bin/keytool" ]] || { echo 'JDK 17 is required; set JDK17_HOME.' >&2; exit 1; }
[[ -d "$android_sdk/build-tools" ]] || { echo 'Android SDK is required; set ANDROID_SDK_ROOT.' >&2; exit 1; }
export JAVA_HOME="$java_sdk"
export ANDROID_HOME="$android_sdk"
export PATH="$java_sdk/bin:$android_sdk/platform-tools:$PATH"
mkdir -p "$signing_dir"

# The visible title and APK filename are separate from the stable Android ID.
apk_basename="$(python3 - "$project_dir" <<'PY'
import json, pathlib, re, sys
project = pathlib.Path(sys.argv[1])
brand = json.loads((project / 'branding.json').read_text())
title = brand['title']
version = brand['version']
if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
    raise SystemExit('branding.json version must use major.minor.patch')
config = project / 'project.godot'
config.write_text(re.sub(r'^config/name=.*$', lambda _: 'config/name=' + json.dumps(title), config.read_text(), flags=re.M))
presets = project / 'export_presets.cfg'
presets.write_text(re.sub(r'^version/name=.*$', lambda _: 'version/name=' + json.dumps(version), presets.read_text(), flags=re.M))
slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'paper-harbor'
print(f'{slug}-{version}-android.apk')
PY
)"
apk_path="$build_dir/$apk_basename"
password_file="$signing_dir/exhibition.password"
keystore_file="$signing_dir/exhibition.keystore"
if [[ ! -f "$keystore_file" ]]; then
  [[ -f "$password_file" ]] || python3 - "$password_file" <<'PY'
import pathlib, secrets, sys
pathlib.Path(sys.argv[1]).write_text(secrets.token_hex(32))
PY
  "$java_sdk/bin/keytool" -genkeypair -noprompt \
    -keystore "$keystore_file" -alias exhibition \
    -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass:file "$password_file" -keypass:file "$password_file" \
    -dname 'CN=Local Exhibition, OU=Game Prototypes, O=Local Development, C=US' \
    >"$signing_dir/key-generation.log" 2>&1
fi
[[ -f "$password_file" ]] || { echo 'Existing local signer has no password file; restore builds/signing backup.' >&2; exit 1; }
export GODOT_ANDROID_KEYSTORE_RELEASE_PATH="$keystore_file"
export GODOT_ANDROID_KEYSTORE_RELEASE_USER='exhibition'
export GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD="$(<"$password_file")"

# Godot reads the installed SDK locations from its editor settings. Configure
# these once in Editor > Editor Settings > Export > Android on other machines.
echo 'Importing Godot resources…'
"$godot_bin" --headless --path "$project_dir" --import >"$build_dir/import.log" 2>&1
if rg -n '^SCRIPT ERROR:|^ERROR:' "$build_dir/import.log"; then
  echo 'Godot import failed; see builds/import.log.' >&2
  exit 1
fi
echo 'Exporting signed Android release…'
"$godot_bin" --headless --path "$project_dir" --export-release Android "$apk_path" >"$build_dir/export.log" 2>&1
if rg -n '^SCRIPT ERROR:|^ERROR:' "$build_dir/export.log"; then
  echo 'Android export failed; see builds/export.log.' >&2
  exit 1
fi
[[ -s "$apk_path" ]] || { echo 'Export did not create an APK.' >&2; exit 1; }

build_tools="$(python3 - "$android_sdk/build-tools" <<'PY'
import pathlib, re, sys
roots = [p for p in pathlib.Path(sys.argv[1]).iterdir() if (p / 'apksigner').exists()]
if not roots:
    raise SystemExit('apksigner is missing from the Android SDK')
print(max(roots, key=lambda p: tuple(int(x) for x in re.findall(r'\d+', p.name))))
PY
)"
"$build_tools/apksigner" verify --verbose "$apk_path" >"$build_dir/signature-verification.txt"
"$build_tools/zipalign" -c -P 16 4 "$apk_path" >"$build_dir/alignment-verification.txt"
"$build_tools/aapt" dump badging "$apk_path" >"$build_dir/apk-metadata.txt"
python3 - "$apk_path" "$build_dir/apk-metadata.txt" <<'PY'
import hashlib, pathlib, sys
apk, metadata = map(pathlib.Path, sys.argv[1:])
text = metadata.read_text()
if "name='com.yiou.paperharbor'" not in text:
    raise SystemExit('Unexpected Android application identifier')
if 'application-debuggable' in text:
    raise SystemExit('Export unexpectedly enables Android debugging')
digest = hashlib.sha256(apk.read_bytes()).hexdigest()
apk.with_suffix('.apk.sha256').write_text(f'{digest}  {apk.name}\n')
print(f'Created: {apk}')
print(f'Size: {apk.stat().st_size / 1024 / 1024:.1f} MiB; signature verified; release mode')
PY
unset GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
