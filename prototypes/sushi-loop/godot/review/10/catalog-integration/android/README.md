# Android release validation · issue #10 / approved catalog integration

The signed release uses the exact runtime inputs committed in `d07856aa6c46c7dba5f020179595326b10862b14`: version **0.2.0**, code **20**, package `com.yiochen.sushilooptickets`. The APK is **181,656,801 bytes**; SHA-256 `bef1ffae2d8593a760503919c4906272a47f72e48da9590b35f0886c83a54518`.

- [Build receipt](release-build.json): all 202 runtime-source hashes match the committed input, including 139 exact approved base atlases and 32 verified native meal variants. Release retains the original certificate, supports arm64/x86_64, targets SDK 36 with minimum SDK 24, requests no permissions, and is nondebuggable. Private, legacy and authoring files are absent.
- [Update proof](update-verification.json): the installed version 11 updated to 20. Its primary 3,409-byte and backup 3,420-byte saves remained byte-identical before the new app launched. Installed APK hashes match both the previously published release and this new build.
- [Lifecycle proof](android-verification.json): migration uses seven visible columns while preserving the 27-column world, camera and service state. A real touch gesture panned 3.769 tiles. Background save bytes stayed unchanged for 4 seconds; Android Back left the activity, saved valid state and kept bytes stable while closed. Back/reopen and force-stop/reopen kept the camera and resumed service.
- [Restored seven-column Android release](release-restored.png), [touch-panned world](touch-panned.png), [Back/reopened world](after-back-reopened.png), [force-stop/reopened world](release-reopened.png), and [runtime log](runtime-logcat.txt).

All three comparisons—migration from the real version 11 save, reopening after Android Back, and reopening after force-stop—matched uninterrupted production `GameSession` simulation, including complete saved state, configuration, random state and fractional remainder. Numeric tolerance is 1e-7. The combined SHA-256 of the sorted runtime-file hash map is `aed968115b6a90025ad363f33235eaaa096a9be84eaa85dad013f4946090cdb5`; the staged input has the identical fingerprint.

Checks used the existing Pixel 8 / API 35 AVD at 1080 × 2400 with `-read-only -no-snapshot-save`. Its original userdata and all physical devices were untouched. Actual post-update rendering was inspected after the loading splash cleared. Two existing GLES shader-cache entries were rejected and automatically recompiled on reopened processes; these recovered warnings remain in the log and report. No script errors or crashes occurred.

The six save fixtures are actual synthetic exhibition-game saves from the disposable emulator copy; each envelope includes a byte-level payload checksum. `verify-continuation.gd` restores two through the production `GameSession`, advances the earlier state by their measured simulation-clock difference, and compares the complete save. It runs as a custom SceneTree and never opens the application's real save directory. To reproduce the force-stop comparison from the repository root after importing the native project:

```sh
godot --headless --path prototypes/sushi-loop/godot --script res://review/10/catalog-integration/android/verify-continuation.gd -- "$PWD/prototypes/sushi-loop/godot/review/10/catalog-integration/android/lifecycle-before-save.json" "$PWD/prototypes/sushi-loop/godot/review/10/catalog-integration/android/lifecycle-after-save.json"
```

Use `legacy-v11-save.json` / `legacy-migrated-save.json` for migration, or `android-back-before-save.json` / `android-back-after-save.json` for Android Back. These final receipts replace the earlier pilot APK evidence.
