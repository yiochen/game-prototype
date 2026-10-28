# Native implementation complete · Android 0.10.0 / 71

The approved Shop is implemented in Godot. [Download the signed APK on Google Drive](https://drive.google.com/file/d/1wmOCgF7hhkr_k0y2jnIPOr-YAGym4yow/view?usp=drivesdk). Its checksum and size were verified after upload. Native implementation evidence and test limitations are in [review/18/native](../../review/18/native/README.md). The prototype revisions below are retained as design history.

# Revision 5 · slower purchase flight

Purchase travel now takes **1.1 seconds**, increased from 0.68 seconds, so its path into the bag is easier to follow. The arc and bag arrival pulse remain the same. Transactions still commit immediately, and the bag can close Shop during travel. Reduced motion still skips the flight. Duration is adjustable in `balance.js` under `timing.purchaseFlightMs`. Current verification: `../../review/18/slower-flight/`.

# Revision 4 · tap the bag to return

The floating shopping bag is now the **Back to inventory** button. Tap/click it or use Enter to close Shop and restore the same Edit inventory tray, category, horizontal scroll and opener focus. It stays usable during a purchase animation; paid items remain in inventory. The shared X and system Back still work. Current evidence and verification: `../../review/18/bag-return/`.

# Shop · issue 18 UI review · revision 3

The current Shop uses the game's **maple wood popup shell** and the recipe picker's **beige rounded catalog**. It reuses `.wr-panel` and `.wr-catalog` directly from `wireframe/recipe-maple.css`: exact grain, rim, depth, beige color and inset shadow. The list has rounded clipping on all four corners and scrolls independently below the fixed title/coin header. The bag floats in the maple footer; independent item flights can pass over the catalog edge. The earlier generated paper is retained as history and is no longer rendered.

Edit-only tray entry, hidden/restored inventory, the shared close X, purchase persistence, bag flights, reduced motion and accessible Back/focus behavior remain as described below. No new raster assets or native gameplay changes were needed. Current evidence is in `../../review/18/maple-popup/`; the full composition amendment is in [brief.md](brief.md). Native integration awaits approval of this deployed revision.

# Shop · issue 18 UI review · revision 2

This revision follows the user's Edit-only shopping feedback. Native Godot integration and ticket completion still await approval of the deployed UI under the requested game-ui-prototype workflow.

Open `/prototypes/sushi-loop/design/shop-preview/`. The default view is the restaurant in Edit. **Shop opens only from the inventory tray.** The left HUD Shop shortcut is removed, and Live has no Shop entry. Opening Shop hides the entire inventory tray while retaining its DOM, tab and horizontal scroll. Closing restores that exact tray and opener focus.

The upper-right control is the **same cream round X** shared with the existing chef and applicant popups (`wireframe/shared-close.jsx` and `.css`). It replaces the earlier curled corner. The paper is a full leaf with its original four rounded corners. Escape and browser Back close the Shop too.

A floating shopping bag sits at the lower right. Each successful purchase pays once, updates saved inventory/stock immediately, then flies a separate copy of that row's item artwork into the bag. The bag gives a small arrival pulse. There is no visible or announced purchase-status text. The catalog scroll viewport ends above the bag so prices remain unobstructed. Concurrent flights, closing mid-flight and tab/focus loss cannot undo or duplicate purchases. Reduced motion skips travel and fades the bag briefly.

Buy a stool, belt tile or decoration, close Shop, then drag the good upward from Layout onto empty floor. Tap an inventory item and then an empty cell for keyboard placement. Tap a placed item and Return to store it. Sideways gestures browse the tray; upward gestures place. Invalid/cancelled drops retain the item.

The external review selector provides Shop, insufficient coins, sold-out goods, the restaurant, Live without Shop and Shared components. Shared uses the exact same `PaperShop`, `ShopRow`, close button, bag and flight components. All controls retain 44px minimum targets. Shop keeps Edit paused; only the separate Live restaurant runs the small review sale/charge clock.

The isolated browser key is `sushi-loop-issue18-shop-review-v2`; Reset affects only this prototype. Prices/timing are review fixtures in `balance.js`; rules are in `model.js`. This is not the native restaurant simulation or its Android saves. Live purchases are also rejected by the model boundary. Stock rotation and floor-style unlocks remain later slices.

## Composition, assets and history

[The revised full-screen brief](brief.md) records the new composition and state inventory. Catalog sections **5, 8, 10–11, 15**, supported by 3 and 14, retain the same material direction. The original ImageGen paper, maple grain, font, goods and registered scene sprites are reused unchanged. The bag extends the existing monochrome SVG vocabulary; no new raster artwork was needed.

The first draft's [ImageGen original](raw/shop-paper.png), [exact prompt](paper-prompt.txt), reference hashes and [nine-slice calibration](generation.json) remain intact. The runtime crop `(20,24,1085,1352)` has 170px source corners uniformly rendered at 26px, with 18px symmetric content insets. Only plain spans and center resize. Item thumbnails remain separate from names, quantities and prices. `world-registration.json` records retained production roots and 128-unit square cells.

First-draft evidence remains in `../../review/18/prototype/`. Current revision evidence is in `../../review/18/edit-only-bag/`, including normal, flying/arrived purchases, disabled, sold-out, Shared pressed, selected placement, Live without Shop and Edit tray entry, across 320×720, 390×844, 844×390 and 1440×1000.

## Verification

- Vite build and five review-model tests passed.
- Fifteen feature browser checks passed on built output, including Edit-only entry, hidden/restored dock, unobstructed bag bounds, independent flights, interrupted purchases, reduced motion, persistence, touch placement, focus/Back and four viewport sizes.
- All 36 neighboring chef-development/applicant checks passed after extracting their existing close control into a shared component.
- Historical baseline: the original repository suite had 200 passes and two missing-evidence failures in unchanged `refinement-rollout.test.js` (`belt-straight-n/.../consumer/.godot/.gdignore` and `coin-pop/final/original-catalog-object.json`).

Repeat with `node --test prototypes/sushi-loop/tests/shop-preview.test.js`, `shop-preview.spec.js`, and `capture.mjs`. Current draft URL and remote verification are recorded in `../../review/18/edit-only-bag/verification.json`.

Current verified draft: https://6ae163a8f7324f48c83535fb--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/shop-preview/

Revision 3 verified draft: https://6ae164cdef87b86c35eaa95f--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/shop-preview/

Revision 4 verified draft: https://6ae16d1cdf4a7b47c0823d05--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/shop-preview/

Revision 5 verified draft: https://6ae16dc4693b906640736dcd--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/shop-preview/
