# Prototype verification — 2026-09-27

## Current checks

- `npm test`: 112 repository engine tests passed, including 52 Deep Salvage tests.
- `npm run build`: passed. Vite retains its advisory for the shared Phaser chunk exceeding 500 kB; the prototype's own JavaScript is approximately 62 kB before gzip.
- All 21 browser scenarios passed after the layout and test-fixture corrections described below. Checks use the production build, real mouse/touch gestures and screenshots of the Phaser canvas plus DOM interface.

Phone layouts were checked at 412 × 924, 448 × 1000, 412 × 820 and 360 × 740 CSS pixels; landscape at 924 × 412. The normal play screen does not scroll or clip controls. Lab and forge cells have equal widths, at least 44 CSS pixels at these sizes. Touch input also runs in a mobile context at 3× density. These are browser emulations, not physical-device tests.

## Seven-by-seven engineering surface

The lower panel contains 30 lab cells (6 × 5), five forge cells in the right column, and fourteen storage cells across the bottom two rows (7 × 2). There are no panel labels, explanatory text, tile power readouts, forge action button or pagination controls. Charge bars, beam appearance, stack counts and upgraded icons remain visible.

Storage capacity is enforced by the engine, rather than hiding overflow. Tests cover fourteen occupied stacks, adding duplicate parts, rejecting new types without consuming their source, reusing an emptied slot without shifting its neighbors, and keeping a forged output in the forge if storage cannot accept it. The output remains draggable to the lab and can be recovered after making room.

Browser checks cover all slots being visible, horizontal touch dragging without scrolling, cancelled gestures, tap-to-place, direct hold-to-forge placement, full-storage feedback and installing a completed output from a full forge. Mouse and touch drops still use the floating preview center. Keyboard rotation/removal, branching circuits, battlefield salvage and return to storage remain covered.

Screenshots are saved under the ignored `artifacts/deep-salvage/` directory, including `pixel-10-pro.png`, `small-phone.png`, `landscape.png`, `fixed-parts-small-phone.png`, `full-hold-forge-output.png` and `forged-piercing-beam.png`.

## Automatic forge

All thirteen recipes run in both ingredient orders in engine tests. Pairwise multiset checks reject duplicate/subset recipes. The larger recipes use upgraded components: Piercing amplifier + Overcharger + Rail lens produces Prism overcharger; Trident + Prism mirror + Fusion core + Heavy laser produces Duplicator.

Tests verify automatic start on the last ingredient, exactly-once payment/output, waiting for cash, pausing timers, queueing behind the current job, arbitrary unrelated ingredients, five-slot capacity, occupied-slot rejection, and moving unused ingredients during a job. Only matched slots lock and clear; leftovers survive. Completion stores the output when it fits, otherwise retains it in a consumed forge slot, and triggers the standard discovery introduction.

Browser checks forge duplicate, mixed, three-part and four-part recipes through actual drag controls, inspect partner highlights in the lab/hold/battlefield, install outputs, and verify enhanced icons and stronger piercing beams. Forge-only fixtures delay enemy spawning so cash assertions and timers are independent of combat rewards and defeat. Combat runs normally in the separate gameplay scenarios. Screenshots include `automatic-forge-working.png`, `recipe-manual.png`, `three-part-forge.png` and `four-part-forge.png`.

## Gameplay retained

Regression coverage includes first discovery and local persistence, repeated salvage, loot expiry/flashing, held-drop protection, pause/manual/background clocks, victory/defeat/restart, all-side component inputs and terminating feedback loops.

Continuous laser, pulse and support tests cover frame-rate-independent damage, armor/piercing/shields, charge thresholds, independent terminals, full/disconnected/paused charge, grid moves versus stacking, healing caps and no resurrection. Browser scenarios exercise pulse, Shield and Medic installation, charging/restoration and manual pause. Damage screenshots show shield rings, hull flashes, recoil and feedback numbers.

All three maps and ten enemy roles remain tested, including sniper range, leech shield drain, mender healing and bomber self-destruction without kill rewards. Route selection changes scenery/encounters, restart preserves the chosen map, and cancelling selection preserves the active dive. The manual contains 20 parts, 13 recipes, 10 enemy descriptions and a route atlas.

Deterministic balance tests confirm the untouched starter loses in wave two. An affordable Overcharger plus salvaged lens clears the 39-enemy city with 54 hull; adding Medic yields 70, or Shield yields 80. Foundry requires further investment: forging a Heavy laser in the first refit is a verified victory using available inventory and earned cash. Killing all scheduled enemies generates ten parts; every player kill awards cash.

The preview URL includes `?ntl-drawer-state=hidden` so Netlify's review drawer does not cover gameplay controls. No production deployment is performed.

## Illustrated level picker

The welcome screen now uses “Levels” and three distinct generated environment images. Story copy, gameplay/support instructions, the slogan and level descriptions are removed from this screen. Names, difficulty/wave metadata, selected border/checkmark and start/back controls remain. The three optimized WebP backgrounds total 184,194 bytes; prompts and generation method are saved in `assets/levels/PROMPTS.md`.

The engine suite still passes all 112 tests and the production build passes. Three focused browser scenarios pass: the illustrated picker across 412 × 924, 360 × 740, 797 × 1232 and 924 × 412; level selection/restart/cancellation and scenery; and discovery/manual persistence. Checks verify all three unique images load, no explanatory paragraphs remain, keyboard level selection works, and the start button fits without modal scrolling. Portrait stacks cards vertically; short landscape lays them out side by side. Screenshots `levels-360x740.png`, `levels-797x1232.png` and `levels-924x412.png` were inspected.
