# Native Android game

Fresh Godot implementation of the [ticket series](https://github.com/yiochen/game-prototype/issues/7). The React/Vite wireframe studio remains the web entry and design reference. The playable native project and its native component gallery share the same renderer, asset library and controls.

Use Godot 4.7.x with matching export templates. Open `project.godot` in Godot, or run:

```sh
godot --path prototypes/sushi-loop/godot
godot --path prototypes/sushi-loop/godot -- --gallery
```

The restaurant uses square cells, 3/4 front-and-top artwork with feet on tile centers, and a fixed transparent HUD. Characters and the connected conveyor use six-frame loops with high-resolution sources and smooth mipmapped sampling. On a wider window the portrait world is clipped to a centered play area. Android stays in portrait orientation; tall phones fill their available height.

## Validate and build

From the repository root:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/native_app_tests.gd --visible --size 390x844
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/capture_starter.gd --visible --size 320x720 --output /tmp/restaurant-review
prototypes/sushi-loop/tools/build_android.sh debug
prototypes/sushi-loop/tools/build_android.sh release
```

The isolated test runner imports a disposable project and uses a unique save directory. `--size 1440x1000` exercises wide-window containment. Captures come from Godot's actual rendered viewport with a controlled public simulation clock.

Android builds require the SDK build tools and JDK 17. Set `ANDROID_HOME`, `JAVA_HOME` or `GODOT_BIN` when your tools are installed elsewhere. Builds stage a temporary project, export arm64/x86_64 APKs, verify their signature, and write a SHA-256 plus nonsecret build metadata. APKs, Godot caches and signing credentials are ignored. Keep `godot/.local/signing` backed up privately to sign compatible updates.

Edit `branding.json` to change the display title and version. The title is not baked into artwork. Keep the Android package and save identity stable to retain installed game data. Equivalent build flags can override display branding without modifying source.

## Rules and saves

`scripts/session.gd` is a public command, elapsed-time, snapshot and save/restore boundary. It has no file I/O or wall clock. `content/starter.json` owns starter layout, recipes and balance. `scripts/save_store.gd` writes a validated envelope atomically and recovers a valid backup. The application saves on important events, periodic intervals and Android lifecycle changes. Restoring replaces state without replaying rewards.

`scripts/restaurant_view.gd` renders the public snapshot. `scripts/art_book.gd` supplies identical production textures and anchor math to gameplay and the native gallery. `assets/production/manifest.json` records atlas regions; exact image-generation prompts, source hashes and alpha inspection are in `assets/provenance/`. These are newly authored assets, independent of the archived Android prototype.

## Licenses

Generated production artwork and original UI icons were authored for this implementation. Nunito and Delius use the SIL Open Font License; the full notices are beside each font. The exported runtime uses Godot under MIT; its full notice is in `assets/licenses/Godot-MIT.txt`. See [Godot's license page](https://godotengine.org/license/) for the engine's third-party notices.

Completed slices and validation evidence are recorded in `review/tickets.md`.
