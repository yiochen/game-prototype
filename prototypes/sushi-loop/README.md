# Sushi Loop — Android exhibition

A native Godot game combining an autonomous sushi restaurant with three short submarine expeditions. **Sushi Loop is a replaceable working title.** This is a polished, playable three-route exhibition, not a full commercial production or a store release. It contains no paid ads, real-money purchases, account system or network dependency.

The repository homepage links to the accompanying web introduction; the playable game is the Android APK.

**Current exhibition version: 0.1.1.** The V2 visual pass uses original AI-generated painted artwork guided by the repository’s accepted [doodle reference](design/art-directions/01-doodle.png), with larger characters, a continuous conveyor, illustrated environments and hand-inked interface surfaces. The original synthesized music and sound effects remain in use.

## Playable scope

- **Restaurant:** chefs prepare dishes, conveyors transport them, and customers find seats and pay for meals. Coins buy belts, seats, a preset chef hire and one floor expansion. Arrange mode pauses service while placing, moving, rotating or storing objects. Chef levels improve preparation speed and unlock higher recipe tiers.
- **Expeditions:** drag sideways to steer, collect salvage, avoid rocks and currents, and use boosts or bonus passages. Aim a harpoon, then follow the creature to complete a catch. The first voyage includes protected lessons. Pause, resume and confirmed early return are supported.
- **Three charts:** Sunlit Shallows / salmon; Coral Current / shrimp; Lantern Trench / eel. The four recipes are Garden Maki, Sunrise Nigiri, Coral Tempura and Midnight Unagi.
- **Progression:** salvage upgrades hull, harpoon and collector. Coins remain the restaurant currency. The submarine takes **150 seconds** to recharge outside an active voyage; opening preparation does not consume charge.
- **Presentation:** loading screen, opening sequence, animated characters and water, short catch celebration, recipe award, distinct outcome illustrations, original music and sound effects. Settings include music, effects, haptics, reduced motion and a confirmed progress reset.

The game is **portrait**, with a minimum 720 × 1280 design canvas that expands to fill taller Android phones. Backgrounds cover the screen, the restaurant uses the extra floor height, and the dock and editing controls stay near the bottom. Larger menu cards remain centered. A uniform width scale keeps fonts, characters and submarine controls in proportion instead of stretching them. This follows the accepted [art direction](docs/art-direction.md).

## Run and build

Commands below run from the repository root. Development uses **Godot 4.7.2 stable**, its matching export templates and the Compatibility renderer.

```sh
godot --editor --path prototypes/sushi-loop/godot
godot --path prototypes/sushi-loop/godot
```

Desktop mouse input emulates touch. Android uses direct touch controls, including a separate harpoon finger while steering.

The Android build requires Python 3, ripgrep, JDK 17 and an Android SDK with build tools. Configure Godot's **Editor Settings → Export → Android** SDK and Java locations once. The build script accepts `GODOT_BIN`, `ANDROID_SDK_ROOT` and `JDK17_HOME`; its defaults match the current macOS development environment.

```sh
bash prototypes/sushi-loop/tools/build_android.sh
```

The 0.1.1 build writes `builds/sushi-loop-0.1.1-android.apk`: version **0.1.1**, Android **7.0 / API 24+**, ARMv7 and ARM64, package **`com.yiou.paperharbor`**. The script imports resources, exports a non-debug APK, verifies its signature and alignment, inspects package metadata and writes a SHA-256 file. Build and verification logs are in `builds/`.

Signing uses a persistent local exhibition key in ignored `builds/signing/`. Preserve that directory and its password file for future updates to the installed app. It is separate from source and from the APK handoff; it is not a store publishing key. Build outputs and signing material are excluded from Git.

## Saves and renaming

Progress is local. The app saves every three seconds, after important actions and when backgrounded. Saves use a temporary file, flush and atomic replacement, with a previous-save backup. An interrupted expedition restores paused with its encounter state; rewards are saved before their celebration and credited once.

Offline income estimates the saved restaurant's actual layout by simulating up to 180 seconds and extrapolating across the absence, **without an absence-time cap**. Disconnected layouts do not receive a generic allowance. Service earnings during an expedition remain pending until return; the submarine does not recharge during that expedition.

Edit `godot/branding.json` to change the visible title, tagline, edition or version. The title screen and web introduction read it directly; the Android build synchronizes the project title, release version and APK filename. Update the shared `prototypes.json` catalog title when renaming the homepage listing. No title is baked into backgrounds or illustrations.

Keep the Android package ID and `project.godot`'s custom save directory, **`PaperHarborExhibition`**, stable when changing the display name. These preserve application and save identity independently of the working title.

## Source map

| File | Responsibility |
| --- | --- |
| `godot/scripts/main.gd` | Screens, touch interface, restaurant rendering and cross-mode progression |
| `godot/scripts/restaurant_model.gd` | Deterministic service simulation, placement, pathing, recipes and economy |
| `godot/scripts/expedition.gd` | Authored-route simulation, steering, encounters, capture and pause state |
| `godot/scripts/save_store.gd` | Atomic local saves and backup recovery |
| `godot/scripts/sound.gd` | Music loops, effect voices and sound settings |
| `godot/balance.json` | Recipe prices/times/tiers, recharge and equipment tuning |
| `godot/expedition_routes.json` | Route timing, salvage lanes, hazards, boosts and portals |
| `godot/tools/generate_assets.py` | Original SVG fallback assets and deterministic synthesized WAV generation |
| `godot/assets/v2/` | Painted production environments, character/prop PNGs, prompt provenance and sprite extraction records |

This game owns its assets, rules and tests; it has no imports from sibling prototypes. Some simulation defaults remain alongside the rules; the JSON files expose the current exhibition tuning.

## Verification

```sh
godot --headless --path prototypes/sushi-loop/godot --script tests/restaurant_tests.gd
godot --headless --path prototypes/sushi-loop/godot --script tests/expedition_tests.gd
python3 prototypes/sushi-loop/godot/tools/test_app.py --size 720x1280
python3 prototypes/sushi-loop/godot/tools/test_app.py --size 720x1600
python3 prototypes/sushi-loop/godot/tools/test_app.py --size 1080x2400
python3 prototypes/sushi-loop/godot/tools/test_app.py --capture --size 720x1280 --output /tmp/sushi-loop-responsive-standard
python3 prototypes/sushi-loop/godot/tools/test_app.py --capture --size 720x1600 --output /tmp/sushi-loop-responsive-tall
npm run check
```

Restaurant checks cover autonomous service, local backpressure, full loops, recipe eligibility, editing preservation, purchasing, pathing, save round trips and layout-dependent offline income. Expedition checks cover multi-touch steering/shooting, cooldown, capture, pause/restoration, protected lessons, collision immunity, bonus passages, early-return receipts and all three routes with base equipment and bounded simulated steering.

Application integration checks exercise scene transitions, touch selection and cancellation, edit pause/resume, live recipe browsing and tier eligibility, charge, upgrades, pending service income, one-time rewards, reopening and backup recovery. Responsive checks use actual screen touch events at control centers and edges, with both same-frame taps and presses held across redraws. They verify settings, the bottom editing tray, dock and preparation navigation at standard and tall phone proportions. **Use `test_app.py` for application tests and screenshots**: it creates a disposable save identity and cleans it up. Each native capture pass writes 32 screenshots and a state manifest to the chosen `--output` directory (default `/tmp/sushi-loop-captures`). The `--size WIDTHxHEIGHT` option sets the real window size; the manifest records both the screenshot dimensions and actual game canvas dimensions. It preserves an honest starter restaurant after 20 simulated seconds and a separately labeled service frame at 22 seconds. Each of the three routes is simulated through its real travel schedule, aiming window and a successful harpoon hit followed by four seconds of pursuit. `npm run check` runs the repository's JavaScript tests, web build and browser checks; those web checks do not exercise the Android runtime.

Automated route completion establishes simulation reachability, while native screenshots and Android play checks establish presentation and touch behavior. It is not a comprehensive commercial device certification matrix.

Latest validation (2026-10-09): **185 Godot checks passed: 53 restaurant, 75 expedition and 57 application checks**. The application checks pass at 720 × 1280, 720 × 1600 and 1080 × 2400, including physical-pixel input dispatch at the scaled resolution. The responsive native screenshot passes captured **64 screens with no errors or off-screen touch targets**: 32 each at 720 × 1280 and 720 × 1600, in `/tmp/sushi-loop-responsive-standard` and `/tmp/sushi-loop-responsive-tall`. Image and actual game canvas dimensions match at both sizes, with no letterbox bars. The shared repository's **129 engine checks**, the web build and **3 relevant catalog browser checks** passed. The final signed **0.1.1 APK** (74.1 MiB, version code 2) passed signature and alignment verification and was installed over the preceding version on a Pixel 8 / Android 15 emulator. Existing progress was preserved. The final 1080 × 2400 Android captures show the title, live restaurant and expedition filling the display with no letterbox bars; native navigation, route launch and touch input were exercised with no script errors or crashes. The uploaded APK's byte count and MD5 checksum match the local release. The software-rendered Android emulator showed delayed frame presentation: touch tracing confirmed that the intended controls activated while screenshots could still show an earlier frame. This does not establish physical-device rendering performance. Physical-device playtesting remains unverified.

## Exhibition boundaries and provenance

The planning documents contain a broader product design. This build deliberately uses one curated species per chart instead of a randomized tier catalog, one compact floor expansion and a preset chef hire. Its four recipe boards fit without scrolling. The floor cosmetic changes the room as a whole rather than painting individual cells. There is no rotating shop or refreshed recruitment application system.

V2 production illustrations are original AI-generated painted artwork guided by the accepted repository doodle study. Generated atlases are mechanically cropped into sprites while retaining alpha transparency; the original atlases and prompt provenance are preserved. Earlier SVG assets remain as fallbacks and supporting assets. Music and sound effects are original deterministic synthesis. Delius and Nunito are bundled under the SIL Open Font License with their notices. See [asset provenance](godot/assets/README.md), the [V2 sprite manifest](godot/assets/v2/SPRITES.md), and the [restaurant generation record](godot/assets/v2/restaurant-art-provenance.json). Exact prompts and author-confirmed summaries are explicitly distinguished. Production artwork contains no baked-in game name.
