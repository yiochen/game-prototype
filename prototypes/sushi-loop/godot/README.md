# Native Android game

Fresh Godot implementation of the [ticket series](https://github.com/yiochen/game-prototype/issues/7). The React/Vite wireframe studio remains the web entry and design reference. The playable native project and its native component gallery share the same renderer, asset library and controls.

Use Godot 4.7.x with matching export templates. Open `project.godot` in Godot, or run:

```sh
godot --path prototypes/sushi-loop/godot
godot --path prototypes/sushi-loop/godot -- --gallery
```

The restaurant uses square cells, 3/4 front-and-top artwork with feet on tile centers, and a fixed transparent HUD. The runtime uses the approved issue #33 Faceted sprites: C125 characters, 70% environment projection, matte crate wood and muted-clay conveyor rails. Character actions retain their complete authored frames; the connected conveyor retains its 24-frame cycle. Smooth mipmapped sampling keeps the high-resolution sprites readable at phone size. Android stays in portrait orientation; tall phones fill their available height.

## Validate and build

From the repository root:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/native_app_tests.gd --visible --size 390x844
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/capture_starter.gd --visible --size 320x720 --output /tmp/restaurant-review
python3 prototypes/sushi-loop/godot/tools/sync_catalog.py --check
python3 prototypes/sushi-loop/tools/test_android_packaging.py
prototypes/sushi-loop/tools/build_android.sh release --check
prototypes/sushi-loop/tools/build_android.sh debug
prototypes/sushi-loop/tools/build_android.sh release
```

The isolated test runner imports a disposable project and uses a unique save directory. `--size 1440x1000` exercises wide-window containment. Captures come from Godot's actual rendered viewport with a controlled public simulation clock.

Android builds require matching Godot export templates, SDK build tools and JDK 17. Set `ANDROID_HOME`, `JAVA_HOME` or `GODOT_BIN` when your tools are installed elsewhere. `--check` validates tool availability and the complete runtime catalog against the approved selection: objects, logical roots, sockets, clips, frame regions, source identities and every referenced atlas. The copy CLI and packaging gate use the same `tools/catalog_contract.py` verifier. The separate `tools/verify_recipe_variants.py` also verifies the starter's native meal clips against their authored Blender source, capture receipts and complete atlas registration. These checks run before import/export and again on the staged assets. `--check` does not import, export or install anything. The build stages an allowlisted temporary project containing current scripts, content, catalog sprites, native recipe variants, UI, sound and license files. Legacy artwork, Blender sources, prompts, provenance, reviews, tests, tools and private signing files never enter the staged importer.

The exporter produces a signed arm64/x86_64 APK, verifies its package/version and certificate, checks that no signing password or excluded files were bundled, and writes a SHA-256 plus nonsecret `.build.json` metadata. The release remains offline and nondebuggable. APKs, Godot caches and signing credentials are ignored. Keep `godot/.local/signing` backed up privately, or set `SUSHI_LOOP_SIGNING_DIR` to an external private directory. Release builds refuse a missing or mismatched original key; they never silently generate a replacement. The public certificate fingerprint is pinned in `branding.json` so an update can retain the installed app's data.

Edit `branding.json` to change the display title and version. The title is not baked into artwork. Keep the Android package and save identity stable to retain installed game data. Equivalent build flags can override display branding without modifying source.

## Rules and saves

`scripts/session.gd` is a public command, elapsed-time, snapshot and save/restore boundary. Its constructor loads `content/starter.json`, which owns starter layout, recipes and balance; the simulation rules use no wall clock or file persistence. `scripts/save_store.gd` writes a validated envelope atomically and recovers a valid backup. The application saves on important events, periodic intervals and Android lifecycle changes. Restoring replaces state without replaying rewards.

`scripts/restaurant_view.gd` renders the public snapshot. `scripts/art_book.gd` supplies identical production textures and anchor math to gameplay and the native gallery. `assets/catalog/manifest.json` retains atlas regions, fixed roots, attachment sockets, animation cadence and approved source identities. The selected 139 atlases are exact byte copies from the 28 relevant objects in `../assets/production/`; full editable art sources remain there for iteration. Only this runtime subset ships on Android. The wordless app icon lives in `assets/ui/`.

`assets/recipe-variants/` adds 32 native atlases for the same four customers: empty-handed seated waiting and eating the starter's salmon recipe. Their 384 frames preserve the approved body geometry, actions, camera, lighting and registration; only the hand-attached food image and empty-state visibility differ. The approved base catalog stays unchanged. Editable derivative projects and authored capture evidence live in `../assets/production/source/variants/starter-meals/`, outside the Android runtime.

## Licenses

Generated production artwork and original UI icons were authored for this implementation. Nunito and Delius use the SIL Open Font License; the full notices are beside each font. The exported runtime uses Godot under MIT; its full notice is in `assets/licenses/Godot-MIT.txt`. See [Godot's license page](https://godotengine.org/license/) for the engine's third-party notices.

Completed slices and validation evidence are recorded in `review/tickets.md`.
