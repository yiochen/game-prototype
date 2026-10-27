# Staff & applicants — issue 16 UI review

Interactive HTML/CSS/React prototype, isolated from native Godot gameplay and its saves. Integration is pending user approval of the deployed prototype, as requested by game-ui-prototype.

Open `/prototypes/sushi-loop/design/staff-hiring-preview/`. The review selector provides applicants, Staff, People/Edit, capacity full, insufficient coins, empty offers and Shared components. Reset explicitly resets the mock state. Browsing and closing do not hire. Hire removes only its offer and charges once; Refresh replaces the remaining pool and starts a real five-minute deadline that continues while closed. Prototype data use the isolated `sushi-loop-issue16-ui-review-v1` browser key.

Try hiring, closing to the roster, dragging a new chef upward onto an empty cell beside a belt, and closing the idle picker without Prepare. Horizontal roster gestures browse; upward gestures place. Tap a photo for separate details; Place in restaurant also supplies keyboard-operable placement targets. Escape cancels a drag or closes the popup. Closing applicants/details restores tray mode, horizontal scroll and focus. The scene is a static review arrangement; this prototype does not run the native simulation, camera or progression.

## Hired stamp and new-chef indicators

Hiring commits payment, staff and removal of the offer once, then keeps that paper on screen for a 1.28-second confirmation: expand uniformly to 1.045×, drop the independently illustrated physical stamp, reveal live Hired ink in the existing red frame, hold the mark and fly out. The following offers settle afterward. Closing or reopening during the sequence preserves the paid chef and unread flag. No hire toast is shown. Reduced motion shows the Hired mark with a short fade and omits expansion and the falling prop.

New chefs carry a persisted `isNew` flag. Their inventory photos display a small red dot until the photo has been at least 85% visible for 1.4 uninterrupted seconds with no modal covering the roster and the document visible. Hidden/offscreen/covered photos remain new. Opening details or placing the chef acknowledges them immediately. Staff and People use the same Photo component. Shared components includes the same hire-animation replay and new-dot presentation.

Built-in `image_gen.imagegen` supplied the separate physical prop. See [exact prompt](hiring-stamp-prompt.txt), [cutout refinement prompt](hiring-stamp-cutout-prompt.txt), [full output](raw/hiring-stamp-cutout.png), [selected runtime asset](assets/hiring-stamp.png), [provenance/reference hashes](hiring-stamp-provenance.json), and [deterministic crop script](prepare-hiring-stamp.py). The imprint text and red ink frame remain independent; no Hired label is baked into the prop. The alpha-bound crop is uniformly fitted with its bottom-center rubber contact as the anchor. Earlier full outputs remain unchanged.

Current evidence: `../../review/16/hired-stamp/`.

## Status and application-motion revision

Above-Hire errors are removed. A full roster uses red “Roster full” in the header. An unaffordable disabled Hire shows current / required coins, with the required amount red. The same résumé presentation appears in Shared components.

`application-card-surface.jsx` owns keyed paper presence separately from the continuous drag/spring layer. Initial applications enter with a light stagger; hired or replaced applications remain mounted and inaccessible for their 210ms paper exit. Their replacements enter after 190ms, and surviving applications move from their actual on-screen positions. Reduced motion uses 80ms opacity-only changes. Closing Applicants adds a 170ms panel exit while preserving the input shield, then restores tray focus. Hiring and explicit Refresh use the same animation path. User decision: no timed replacement. Existing offers persist until hired or explicitly refreshed; cooldown expiry only re-enables Refresh and never replaces offers or advances the selected application.

Evidence for the current revision is in `../../review/16/application-motion/`; historical card-fan review remains in `card-fan/`.

## Card-fan revision

The application now shows identity/background, cooking speed, growth per level, maximum level and the explicit Hire cost. Strength, reachable tier and initial level/assignment copy were removed. The old paging row was replaced by a custom horizontal scroll view that extends beyond the maple panel, from game-screen edge to edge. Adjacent cards tilt and peek into view. It follows the pointer continuously, resists at the ends and hands release velocity into an interruptible spring. Arrow keys and wheel also browse. No vertical scroll or visible scrollbar is introduced. Existing paper/portrait artwork is reused without regeneration.

## Composition and assets

See [complete screen brief and asset map](brief.md). Catalog sections 5, 8 and 9 guide the feature, with 3, 13 and 14 for coins, plates and notifications. Current approved wood dock, independently generated photo frames and illustrated chef headshots supply the neighboring family. #15's existing React recipe picker is reused unchanged. No new chef identities or world sprites were generated.

Built-in `image_gen.imagegen` generated the blank résumé paper. [Exact prompt](paper-prompt.txt), [full unchanged output](raw/resume-paper.png), [reference hashes and provenance](provenance.json), [derived paper](assets/resume-paper.png), and [deterministic preparation script](prepare-assets.py) are retained. The source crop is (24,120,1034,1224); nine-slice margins are 170px on all sides, uniformly rendered at 36px. Only quiet middle spans resize. Safe content insets are 20px, with a documented 15px narrow-screen composition. Text, headshots, plate identity, prices and controls remain separate.

Existing world frames are cropped at the production library's first registered idle/running frame without resampling. Portraits, inner/outer photo frames and Assigned stamps remain independent. Buttons, maple surfaces and borders extend the approved HTML wood dock source. Texture repeats instead of stretching the complete frame. See `style.css` for source registration and adaptive layout.

## Verification

- Build passed (existing chunk-size warning).
- 20 feature browser checks passed for this revision; the 9 existing wood dock tests passed in the first review. Includes actual touch swipe, touch pickup, direction ownership, invalid/cancelled drops, atomic hiring, capacity/coin disables, persisted deadline and assignments, modal focus restoration/trap and 44px targets.
- Layout captures: 320×720, 390×844, 844×390, 1440×1000. All application layouts have zero vertical scroll. Short landscape uses a compact two-column card; narrow portrait keeps all stats and Hire fully visible. The custom fan reaches both scene edges, hides scrollbars, exposes tilted neighboring cards, and supports spring interruption, end resistance and reduced motion.
- Repository tests: 200 passed, 2 failed in unchanged `refinement-rollout.test.js` because existing source-evidence files are absent: `belt-straight-n/candidates/round-09/consumer/.godot/.gdignore` and `coin-pop/final/original-catalog-object.json`. No native source or historical evidence was changed to bypass these failures.
- Full-scene state and Shared gallery captures: `../../review/16/hired-stamp/` (earlier review captures remain in their versioned folders). Phone and wider portrait-contained screenshots were visually inspected for paper corners, portrait crop, disabled contrast, plate aspect ratios, clipping and roster labels.

Current draft: https://6adfa8edd2cc138ad8c62b1f--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/staff-hiring-preview/ . All 20 feature browser checks passed against this deployment. Phone, wide and landscape captures verify the screen-width fan, tilted neighbors, no paging controls, no vertical scroll, and complete card content.

Original draft retained for history: https://6adf01af05a8be333e3861c4--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/staff-hiring-preview/ .

The deployed review URL and remote verification results are recorded in `../../review/16/hired-stamp/verification.json`.
