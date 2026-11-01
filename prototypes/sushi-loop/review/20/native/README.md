# Issue 20 · Approved floor painting in Godot

The user approved the deployed `design/floor-paint-preview/` composition on 2026-10-31 and requested native implementation. The subsequent instruction-persistence amendment is included: palette touches and scrolling never hide the centered prompt.

## Native behavior

- Floor opens without an armed brush. Its caption-free horizontal strip uses accessible style names, 2×2 previews, newest purchases first and Original Cream last. Touch/wheel scrolling and keyboard focus reach every owned style; scrolling never paints, selects a brush or pans the scene. Keyboard activation also works immediately after a touch-scroll. Backgrounding cancels a held brush-exit X without an orphan release action.
- The centered prompt says exactly **select a tile pattern** or **paint the floor**. Touching outside the palette hides it until release/cancellation. The shared round cream X clears the brush and retains Floor/the palette. Palette collapse and scene panning retain the brush.
- Scene-edge carets pan with press/hold or keyboard activation; unavailable directions are disabled. Vertical Floor panning reveals the last rows above the dock. Actual native targets retain at least 44px bounds.
- Tap paints one cell; a stroke traverses every crossed cell interior, including tiny crossings near a tile corner. Furniture never intercepts the brush. Scene furniture, chefs, sushi and the dock become 28% opaque while painting; trash stays identifiable at 65%. Brush exit restores opacity. Shop suspends translucency while retaining the brush, and return restores it.
- Actual registered trash footprints block painting; strokes skip those cells. Clearing the trash makes its floor paintable. Painting applies beneath furniture and the covered dock, costs no coins/items and does not rebuild navigation or change service clocks/preferences/access.
- Styles unlock once through the persistent Edit-only Shop. A single optional rotating offer uses configured weighted price bands; all unowned styles are eligible immediately. Purchased offers stay **Owned** until rotation and are excluded from future pools. Purchases save before the brief named toast near the Shop balance; they do not use finite-goods flight/quantity behavior. Shop stays open. The optional-offer chance is 70%. Offers persist through ordinary elapsed time. The replay-safe `floor_refresh` command is provided for the ended-expedition lifecycle; expedition gameplay/return integration remains owned by its separate ticket. There is no added timer or manual refresh button. Costs/odds/bands are in `godot/content/floor_styles.json`.
- Owned styles, painted cells, rotation and purchase tokens survive save/reload. A legacy restaurant receives only Original Cream and an empty painted map. Migration derives the isolated cosmetic seed from saved RNG state rather than the caller's constructor seed; it does not advance restaurant RNG, service or coins. Restores clear the transient brush. Failed persistence uses the existing Retry contract without replaying a debit.

## Shared presentation and provenance

`floor_pattern.gd` draws the same native preview in Floor and Shop. `floor_presentation.gd` provides instructions, brush exit and scene panning for gameplay and `--floor-gallery`. The gallery uses a valid isolated collection fixture and the same renderer/dock controls. Native screenshots include normal, held/pressed, selected and disabled-caret states over the complete scene.

The seven 256×256 native pattern tiles are exact deterministic exports of the approved CSS/production texture family. Editable source and measurements: `design/floor-paint-preview/style.css`, `patterns.js` and `export-patterns.mjs`; hashes and export settings: `pattern-export.json`. No new ImageGen surfaces or altered world sprites were needed. Existing maple assets, calibrated corners, font, registered roots, native pixel compositor and production provenance remain reused. Translucency is a view property; the detached session snapshot stays unchanged and native compositor/picking share the same frame.

## Validation

Actual **Mobile / Metal** GPU captures on Apple M4 at **320×720, 390×844, 844×390 and 1440×1000** each pass **55 native checks**. Each size includes `checks.json` with the actual driver/adapter and the corresponding full-scene PNGs. `03b-selected-palette-scrolling.png` proves the painting instruction stays visible during an active palette swipe. `12`–`15` cover the shared normal, pressed, selected and unavailable-direction states.

- Floor command/time/save rules: **35 checks pass**, including optional/all-style stock eligibility, atomic/replayed/poor purchases, trash masks, painting under objects/dock, clearing trash, original restoration, save migration/corruption and diagonal traversal.
- Existing Shop rules: **34 pass**; Shop native **53 pass**; wood dock **38 pass**; general native app **146 pass**; edit navigation **35 pass**; clearance native **55 pass**; clearance feedback **21 pass**; Exhibition Unlocked **41 pass**.
- The existing one-snapshot-per-Live-frame check passes. Cosmetic presentation does not add session snapshot calls to normal frames.
- Existing engine checks for editor, staff, chef development, save/store validation, expansion/capacity, customer layout/rescue, conveyor routes and guest exit recovery pass.
- Two existing historical migration assertions still fail: one in `session_tests.gd` and one in `customer_visit_tests.gd`. Both were reproduced using the unchanged HEAD `session.gd` in the same isolated project; baseline outputs are retained under `validation/`. New floor migration and continuation checks pass. The older broad failures are not presented as new floor regressions.
- Vite production build passes with its existing chunk-size advisory. No sibling prototype code changed.

Reproduce one native family with the existing isolated harness (initial artwork import can take several minutes):

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py \
  --script tests/floor_native_tests.gd --visible --resolution 390x844 \
  --timeout 900 --output prototypes/sushi-loop/review/20/native/390x844
```

Headless rules use `--script tests/floor_tests.gd`. The captures in this directory were run sequentially from the same allowlisted runtime staging project with a `SushiLoopTicketsTest-` save identity; the installed/real restaurant was never loaded or changed.

## Android delivery

Release **0.12.0 / version code 80**, package `com.yiochen.sushilooptickets`, save identity `SushiLoopTickets`. The build uses the unchanged Mobile/Vulkan Android configuration, original pinned release signer and nondebuggable release flag. Build metadata/source fingerprints and APK audit are recorded in `release-audit.json`. Runtime artwork import caches were reused; the normal staging, source hashes, signer checks and APK audits were retained.

No Android device was connected (`adb devices` was empty), so this revision has not been installed or GPU-tested on an Android device. Desktop Mobile/Metal capture evidence does not substitute for an Android Vulkan run.
