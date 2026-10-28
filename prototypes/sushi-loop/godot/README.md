# Native Android game

Fresh Godot implementation of the [ticket series](https://github.com/yiochen/game-prototype/issues/7). The React/Vite wireframe studio remains the web entry and design reference. The playable native project and its native component gallery share the same renderer, asset library and controls.

Use Godot 4.7.x with matching export templates. Open `project.godot` in Godot, or run:

```sh
godot --path prototypes/sushi-loop/godot
godot --path prototypes/sushi-loop/godot -- --gallery
```

The game uses Godot's **Mobile** renderer on desktop and Android. Android
explicitly uses **Vulkan**, with automatic fallback to OpenGL/Compatibility
disabled. macOS uses its native Metal driver. GPU capture checks verify the
actual renderer/driver and save `renderer.json` alongside screenshots; headless
engine tests do not establish which graphics backend runs on an Android device.

The restaurant uses square cells, 3/4 front-and-top artwork with feet on tile centers, and a fixed transparent HUD. Its existing selection now uses the independently approved warm, softly lit cartoon refinements, with the two restaurant floor designs preserved. Character actions retain their complete authored frames; the connected conveyor retains its synchronized 24-frame cycle. Fixed roots, sockets, projection and source scale come from the catalog. Smooth mipmapped sampling keeps the high-resolution sprites readable at phone size. Android stays in portrait orientation; tall phones fill their available height.

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
The current ground-shadow trial uses Godot's `DirectionalLight3D` and hidden
shadow-only meshes: raised conveyor/stool decks with legs, a front-edge
blackboard panel/posts/feet, character capsules and simple prop volumes. These
are approximate shadow geometry, independent of the approved color sprites.
A top-down orthographic camera registers the shadow receiver to the same square
floor grid; the receiver stops at the back wall's floor edge. Native shadow-map
attenuation becomes a transparent warm shadow layer between floor and objects.
Both GPU targets use quarter native resolution. Color artwork, animations,
selection geometry and UI stay unchanged. `scripts/ground_shadows.gd` owns the
light and shapes; `ground_shadow_receiver.gdshader` reads native lighting and
`ground_shadow_present.gdshader` controls opacity/color.
`RestaurantView.ground_shadows_enabled` supports A/B review. Previous distorted
sprite-shadow sources and captures are retained under `review/ground-shadows/`.
Shadow shapes now share two MultiMesh draws (boxes and character capsules), with
cached shape templates and bulk instance buffers. Unchanged buffers are not
uploaded again. The native compositor generates only the reduction levels used
at the physical display scale; its sprite resolution and final area filter are
unchanged. Pan profiling and visual comparisons live in
`review/ground-shadows/pan-performance/`.
Run `tools/test_native.py --script tests/capture_ground_shadows.gd --visible
--size 390x844 --output /tmp/sushi-loop-shadows` for matching before/after phone
captures plus wider portrait and landscape checks, all with isolated save data.

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

## Continuous maple editor dock

The approved HTML dock now ships natively through `scripts/wood_editor_presentation.gd`, shared by gameplay and the editor gallery. The active category joins the board; inactive tabs and the independent walnut Shop stay detached. Shop and inactive faces share a 60-unit height. Current HTML-derived PNGs live in `assets/ui/wood-editor/`; `tools/verify_wood_ui.py` verifies their source hashes, dimensions, slice spans and registration before and after staging. The older atlas remains for inherited HUD, contextual controls, modal/recovery panels and historical provenance.

All inventory entries share a horizontally clipped strip, with four complete Layout goods and a continuation hint. Native text and circular quantities reflect actual owned stock. Wheel and keyboard focus reach every entry. A tray touch begins pending: after 10 physical pixels, 1.3× horizontal dominance owns browsing, while clearly upward dominance owns pickup. Ownership stays fixed until release/cancellation. Scroll metadata persists per category without advancing service or changing placement; old paging saves still load. Existing tap selection, staff inspection, invalid-drop handling, Rotate/Return, collapse, Back, pause and save-retry behavior remain.

The native dock retains a 42-unit decorative footer, expands for the physical bottom safe inset, and keeps 44px category hit targets on narrow phones. Its current capture/test entry is `tests/wood_editor_tests.gd`; `tests/capture_editor.gd` also captures the shared gallery. See [wood dock review](review/12/wood-dock/README.md) for the current Android receipt and screenshots.

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

The exporter produces a signed arm64/x86_64 APK, verifies its package/version and certificate, checks that no signing password or excluded files were bundled, and writes a SHA-256 plus nonsecret `.build.json` metadata. The editor UI gate requires the current v6 amendment, its complete composition, two new ImageGen sheets and the unchanged inherited v5 icon sheet; an independent pixel check preserves the approved Floor icon. A separate editor-goods gate verifies five approved refined object captures and the unchanged floor slab, source/recipe/receipt hashes, the three-quarter UI camera, physical floor thickness and exact unresized atlas pixels with transparent gutters. Both atlases and manifests are reverified after staging; their manifest fingerprints are checked again in the APK. Authoring sources remain outside the runtime payload.

The release remains offline and nondebuggable. APKs, Godot caches and signing credentials are ignored. Keep `godot/.local/signing` backed up privately, or set `SUSHI_LOOP_SIGNING_DIR` to an external private directory. Release builds refuse a missing or mismatched original key; they never silently generate a replacement. The public certificate fingerprint is pinned in `branding.json` so an update can retain the installed app's data.

Edit `branding.json` to change the display title and version. The title is not baked into artwork. Keep the Android package and save identity stable to retain installed game data. Equivalent build flags can override display branding without modifying source.

Issue #11 has an isolated customer-visits review APK. `--review-scene customer-visits` builds the same code, content and assets with staged title `Sushi Loop · Customer Visits` and package `com.yiochen.sushilooptickets.review11`. Its separate Android app sandbox starts a fresh demonstration while the normal `com.yiochen.sushilooptickets` package retains the installed restaurant. The original issue #11 builds used version 0.3.0 / code 30. New normal and review builds use the current branding version and the original release signer. The review flag adds no gameplay branch or production UI controls; only the staged title/package differ. It cannot be combined with `--title` or `--package-id`. Source files and subsequent normal builds remain unchanged. Default APK filenames distinguish normal and review builds.

Build receipts record `build_variant`, the original runtime-file hashes, the staged hashes after branding, and a SHA-256 fingerprint of each sorted hash map. Review overrides therefore have an explicit, reproducible fingerprint without altering the source catalog or content.

## Customer layout recovery

Occupied stools now carry their seated customer, unfinished meal and animation frame when moved or rotated. Returning a stool leaves its customer standing at the same position. Live searches for reachable replacement seating; paused edits never advance meals or create sales. A suitable stool placed on that customer reseats them immediately. Another object displaces the customer to a nearest clear floor cell, or rejects atomically if no such cell exists.

In **People**, tap a standing or trapped customer and then drag their rendered body to empty floor or a free seat. Rescue needs no walking route. The visit, preference and meal progress remain intact. Occupied seated customers continue to move with their stool; direct removal from the stool is unavailable. System Back/Escape clears customer selection. Canceled drops, interruption and failed writes preserve the accepted state behind the existing Retry flow.

The original wood dock, production sprites and puzzled/panic feedback are reused in gameplay and Shared. An unfinished carried plate follows the character's authored hand socket. The customer-layout save version migrates old saves with neutral fields and never replays service or revenue. See [issue 14 review and Android builds](review/14/README.md). `--review-scene customer-rescue` exports the same runtime as a separate `com.yiochen.sushilooptickets.review14` app sandbox.

## Rules and saves

`scripts/session.gd` is a public command, elapsed-time, snapshot and save/restore boundary. Its constructor loads `content/starter.json`, which owns starter layout, recipes and balance; the simulation rules use no wall clock or file persistence. `scripts/save_store.gd` writes a validated envelope atomically and recovers a valid backup. The application saves on important events, periodic intervals and Android lifecycle changes. Restoring replaces state without replaying rewards.

`scripts/restaurant_view.gd` renders the public snapshot. `scripts/art_book.gd` supplies identical production textures and anchor math to gameplay and the native gallery. `assets/catalog/manifest.json` retains atlas regions, fixed roots, attachment sockets, animation cadence and approved source identities. The selected 208 base atlases contain 2,332 frames copied exactly from the 34 relevant objects in `../assets/production/`: 32 refined objects and two original floors. Full editable art sources remain outside the runtime for iteration. Only this existing restaurant subset ships on Android; underwater catalog content is not added. The wordless app icon lives in `assets/ui/`.

`assets/recipe-variants/` adds 32 approved native atlases for the same four customers: empty-handed seated waiting and eating the starter's salmon recipe. Their 384 frames use each refined body, its approved animation and fixed registration. `assets/chef-variants/` adds eight approved Omar atlases for holding/loading cucumber maki (96 frames). Editable derivative projects, capture evidence and the original object judges' approvals live in the corresponding `../assets/refinement/objects/<id>/` experiments. Each runtime manifest binds its exact source packet, review, canonical food and complete atlas pixels. `assets/feedback-variants/` provides four approved 12-frame 2D smiling-face clips from the refined happy-bubble experiment. Their original cadence and registration remain intact. The base catalog and these variants total 252 atlases and 2,860 frames. Authoring projects, targets and review evidence stay outside the Android payload.

The complete catalog refinement and final import evidence live in `../assets/refinement/`. Original Blender files and the 258 pre-cutover game PNG/JSON payloads remain backed up there. Thirteen underwater effects are annotated **2D effect · deferred** in the web catalog; their 109 original atlases and all three excluded restaurant-floor objects remain unchanged.

## Licenses

Generated production artwork and original UI icons were authored for this implementation. Nunito and Delius use the SIL Open Font License; the full notices are beside each font. The exported runtime uses Godot under MIT; its full notice is in `assets/licenses/Godot-MIT.txt`. See [Godot's license page](https://godotengine.org/license/) for the engine's third-party notices.

Completed slices and validation evidence are recorded in `review/tickets.md`.

The 0.4.15 diagnostic build displays rolling FPS, average/max frame interval,
CPU process milliseconds and total draw calls in the sky strip. From 0.4.16,
CPU uses the same rolling one-second window as the cadence statistics. Text refreshes
at 4 Hz; max covers the last second and clears after resume. CPU is not GPU
time. See `review/performance-overlay/README.md` for measurement details.

## Applicants in the People tray (#16)

**Edit → People** is the only roster entry. The continuous maple People tray contains the current/maximum chef count, Applicants action and photo inventory; Live has no Staff button or separate roster panel. Applications and Recipes use the same native modals in gameplay and Shared. Tapping any chef photo opens Recipes directly, including for unplaced staff; unplaced Recipes has no Prepare action. Inventory category tabs and the top-right Live action stay visible and interactive throughout Edit, including after either modal closes.

`content/staff_catalog.json` owns six backgrounds, cooking speeds, growth, caps, prices, four-chef capacity and the five-minute absolute Refresh deadline. Offers persist until Hire or free explicit Refresh, with no timed replacement. Hiring commits once, keeps the other offers, then expands the paper, drops the independent wooden stamp, leaves live red Hired ink and flies away. It produces no toast.

Each new photo has a saved unread dot. The tray collects chefs whose photos are at least 85% visible while foreground and unobscured. Dots remain throughout the open People tray, including while Recipes is inspected; they clear for viewed chefs when People closes, another inventory tab is selected, or Edit returns to Live. Offscreen unseen photos remain unread. There is no real-time expiry.

Drag an unassigned photo upward onto an empty workable belt-adjacent cell, using the existing direction-locked drag gesture. The native recipe picker opens idle; only Prepare starts production. Invalid/cancelled drops preserve the roster and arrangement. Unplaced staff can inspect recipe information; the public Prepare command also rejects unplaced chefs. Older saves receive offers and read flags once, retaining existing chefs and payments.

`scripts/staff_presentation.gd` and `staff_resume.gd` serve gameplay and `--staff-gallery`; their approved source paper/stamp images remain independent of live labels. The paper retains 170px source slices and 36-unit corners. Six applicant identities reuse their production world clips and matching illustrated portraits. Android exports retain the original package/save identity/release signer.

`tests/staff_tests.gd` covers pure commands/time/saves; `staff_native_tests.gd` covers integrated hiring, placement and unread behavior. `edit_navigation_tests.gd` exercises repeated Edit/People/Layout/Floor/Live journeys and confirms Applicants belongs inside People. The 0.8.1 navigation amendment and full-scene evidence live in `../review/16/navigation-fix/`.

## Chef development and lifecycle · issue 17

The shared native recipe popup has Recipes / Manage tabs. Only the contents slide;
the portrait and maple frame stay fixed, and Manage's separator touches the crop's
bottom. Manage text sits directly on wood grain. Open the same component with
`godot --path prototypes/sushi-loop/godot -- --chef-gallery`.

Purchased levels preview speed, a plate-tier threshold and the coin cost. Costs
and default growth live in `content/chef_development.json`; configured hired-chef
growth/caps remain in `staff_catalog.json`. Levels change actual preparation time
without changing recipe prices, discoveries or experience. MAX keeps final stats
without a cost. Commands include the previewed level to reject replayed purchases.

Unassign retains development in People; reassignment uses the existing valid
placement rules and opens an idle recipe picker until Prepare. Fire slides up that
chef's named application. Confirm saves removal before the shared physical stamp
lands and leaves live Fired ink until Close, with no toast. Cancel is read-only.

Versioned migration preserves existing levels, speeds, caps, layout, clocks, coins
and random state. It records growth/baselines and permanently dismissed identities
so removing a starter does not resurrect them on reopen. Native rule and viewport
tests, captures and the signed 0.9.0 / 70 build audit are in `../review/17/native/`.
