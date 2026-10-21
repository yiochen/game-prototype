# Native Android game

Fresh Godot implementation of the [ticket series](https://github.com/yiochen/game-prototype/issues/7). The React/Vite wireframe studio remains the web entry and design reference. The playable native project and its native component gallery share the same renderer, asset library and controls.

Use Godot 4.7.x with matching export templates. Open `project.godot` in Godot, or run:

```sh
godot --path prototypes/sushi-loop/godot
godot --path prototypes/sushi-loop/godot -- --gallery
```

The restaurant uses square cells, 3/4 front-and-top artwork with feet on tile centers, and a fixed transparent HUD. The runtime uses the approved issue #33 Faceted sprites: C125 characters, 70% environment projection, matte crate wood and muted-clay conveyor rails. Character actions retain their complete authored frames; the connected conveyor retains its 24-frame cycle. Smooth mipmapped sampling keeps the high-resolution sprites readable at phone size. Android stays in portrait orientation; tall phones fill their available height.

## Approved restaurant backdrop

The top three projected tile rows contain the uniformly lit wood backdrop.
The twenty-one-column world uses three one-tile blank walls, the four-tile
entrance at x=3, then blank walls from x=7 onward. The two-tile clear opening
covers columns four and five. The full wall and gate include their roof and
baseboard and retain the native 35° character camera with square pixels.

`backdrop-entrance` and `backdrop-wall` are the same approved, complete 3× PNGs
shown in the wireframe catalog. The old `entry-finished` exports and model are
removed from the active catalog and current editable library. The backdrop is
painted before ordinary depth-sorted sprites and follows both camera axes.
The game uses even lighting without runtime lantern lights or baked cast shadows.

The room fills the portrait phone scene to both side edges. An ImageGen night
sky reserves the top 80 logical units at a 720-unit scene width for camera
clearance. Android/iOS safe-area information and Android camera cutouts can
enlarge it, with 12 logical units of extra clearance. Coins, Editing, Live and
Shop start below the strip and may overlap the shingles. The sky stays fixed
while the room pans, rejects scene input, and adds no saved rows or furniture.
Bottom controls retain their position. Wider desktop windows retain the centered
portrait composition. The complete sky output and exact prompt are preserved in
`../assets/restaurant-backdrop/night-sky/`; the runtime PNG is an identical copy
scaled and cropped uniformly.

New sessions reserve rows 0–2 for the backdrop and admit guests at (4,3).
Legacy shipped saves retain money, furniture, dishes, meal clocks and visits.
Layouts that used the old top rows move down together and gain three floor rows;
other furniture keeps its position. Existing guests crossing the retired doorway
move to clear floor and replan, with no rewards or elapsed time replayed.

Native phone/landscape captures and validation are in `review/33/backdrop/`.

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
prototypes/sushi-loop/tools/build_android.sh release --review-scene customer-visits
```

The isolated test runner imports a disposable project and uses a unique save directory. `--size 1440x1000` exercises wide-window containment. Captures come from Godot's actual rendered viewport with a controlled public simulation clock.

Android builds require matching Godot export templates, SDK build tools and JDK 17. Set `ANDROID_HOME`, `JAVA_HOME` or `GODOT_BIN` when your tools are installed elsewhere. `--check` validates tool availability and the complete runtime catalog against the approved selection: objects, logical roots, sockets, clips, frame regions, source identities and every referenced atlas. The copy CLI and packaging gate use the same `tools/catalog_contract.py` verifier. The separate recipe, chef and feedback variant verifiers check authored Blender or ImageGen sources, capture/generation receipts and complete atlas registration. These checks run before import/export and again on the staged assets. `--check` does not import, export or install anything. The build stages an allowlisted temporary project containing current scripts, content, catalog sprites, native recipe variants, UI, sound and license files. Legacy artwork, Blender sources, prompts, provenance, reviews, tests, tools and private signing files never enter the staged importer.

The exporter produces a signed arm64/x86_64 APK, verifies its package/version and certificate, checks that no signing password or excluded files were bundled, and writes a SHA-256 plus nonsecret `.build.json` metadata. The editor UI gate requires the current v6 amendment, its complete composition, two new ImageGen sheets and the unchanged inherited v5 icon sheet; an independent pixel check preserves the approved Floor icon. A separate editor-goods gate verifies six editable Blender captures, source/recipe/receipt hashes, the three-quarter UI camera, physical floor thickness and exact unresized atlas pixels with transparent gutters. Both atlases and manifests are reverified after staging; their manifest fingerprints are checked again in the APK. Authoring sources remain outside the runtime payload.

The release remains offline and nondebuggable. APKs, Godot caches and signing credentials are ignored. Keep `godot/.local/signing` backed up privately, or set `SUSHI_LOOP_SIGNING_DIR` to an external private directory. Release builds refuse a missing or mismatched original key; they never silently generate a replacement. The public certificate fingerprint is pinned in `branding.json` so an update can retain the installed app's data.

Edit `branding.json` to change the display title and version. The title is not baked into artwork. Keep the Android package and save identity stable to retain installed game data. Equivalent build flags can override display branding without modifying source.

Issue #11 has an isolated customer-visits review APK. `--review-scene customer-visits` builds the same code, content and assets with staged title `Sushi Loop · Customer Visits` and package `com.yiochen.sushilooptickets.review11`. Its separate Android app sandbox starts a fresh demonstration while the normal `com.yiochen.sushilooptickets` package retains the installed restaurant. Both use version 0.3.0 / code 30 and the original release signer. The review flag adds no gameplay branch or production UI controls; only the staged title/package differ. It cannot be combined with `--title` or `--package-id`. Source files and subsequent normal builds remain unchanged. Default APK filenames distinguish normal and review builds.

Build receipts record `build_variant`, the original runtime-file hashes, the staged hashes after branding, and a SHA-256 fingerprint of each sorted hash map. Review overrides therefore have an explicit, reproducible fingerprint without altering the source catalog or content.

## Rules and saves

`scripts/session.gd` is a public command, elapsed-time, snapshot and save/restore boundary. Its constructor loads `content/starter.json`, which owns starter layout, recipes and balance; the simulation rules use no wall clock or file persistence. `scripts/save_store.gd` writes a validated envelope atomically and recovers a valid backup. The application saves on important events, periodic intervals and Android lifecycle changes. Restoring replaces state without replaying rewards.

`scripts/restaurant_view.gd` renders the public snapshot. `scripts/art_book.gd` supplies identical production textures and anchor math to gameplay and the native gallery. `assets/catalog/manifest.json` retains atlas regions, fixed roots, attachment sockets, animation cadence and approved source identities. The selected 208 atlases are exact byte copies from the 34 relevant objects in `../assets/production/`; full editable art sources remain there for iteration. Only this runtime subset ships on Android. The wordless app icon lives in `assets/ui/`.

`assets/recipe-variants/` adds 32 native atlases for the same four customers: empty-handed seated waiting and eating the starter's salmon recipe. Their 384 frames preserve the approved body geometry, actions, camera, lighting and registration; only the hand-attached food image and empty-state visibility differ. The approved base catalog stays unchanged. Editable derivative projects and authored capture evidence live in `../assets/production/source/variants/starter-meals/`, outside the Android runtime. `assets/chef-variants/` adds eight native Omar atlases for holding/loading cucumber maki (96 frames); its separate editable source and audit live in `../assets/production/source/variants/chef-cucumber/`. Both derivative families preserve the approved base body, animation, camera, lighting and fixed registration. `assets/feedback-variants/` provides four 12-frame 2D smiling-face feedback clips, edited with ImageGen from the approved happy bubble. Its generation/reference/output hashes and fixed registration are verified against `../assets/production/source/variants/customer-feedback/`.

## Licenses

Generated production artwork and original UI icons were authored for this implementation. Nunito and Delius use the SIL Open Font License; the full notices are beside each font. The exported runtime uses Godot under MIT; its full notice is in `assets/licenses/Godot-MIT.txt`. See [Godot's license page](https://godotengine.org/license/) for the engine's third-party notices.

Completed slices and validation evidence are recorded in `review/tickets.md`.
