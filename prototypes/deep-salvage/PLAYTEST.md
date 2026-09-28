# Prototype verification — 2026-09-27

## Current checks

- `npm test`: 108 repository engine tests passed, including 48 Deep Salvage tests.
- `npm run build`: passed. Vite retains its advisory for the shared Phaser chunk exceeding 500 kB; the prototype's own JavaScript is approximately 62 kB before gzip.
- All 20 browser scenarios passed after the layout and test-fixture corrections described below. Checks use the production build, real mouse/touch gestures and screenshots of the Phaser canvas plus DOM interface.

Phone layouts were checked at 412 × 924, 448 × 1000, 412 × 820 and 360 × 740 CSS pixels; landscape at 924 × 412. The normal play screen does not scroll or clip controls. Lab and forge cells have equal widths, at least 44 CSS pixels at these sizes. Touch input also runs in a mobile context at 3× density. These are browser emulations, not physical-device tests.

## Seven-by-seven engineering surface

The lower panel contains 36 lab cells, six forge cells in the right column, and a full-width bottom row with five fixed stack slots and two paging arrows. There are no panel labels, explanatory text, tile power readouts or forge action button. Charge bars, beam appearance, stack counts and upgraded icons remain visible.

Browser checks cover pagination, persistent empty stack slots, tap-to-place from a later page, horizontal touch dragging without scrolling, cancelled gestures and direct hold-to-forge placement. Mouse and touch drops use the floating preview center, including bottom-row destinations with the finger outside the highlighted cell. Occupied cells reject without consuming a part. Keyboard rotation/removal, branching circuits, battlefield salvage and return to storage remain covered.

The initial layout check exposed an inherited CSS alignment rule narrowing forge cells. The forge now explicitly fills its single grid column. Screenshots were inspected after the fix: `pixel-10-pro.png`, `small-phone.png`, `landscape.png`, `fixed-parts-small-phone.png`, `two-gun-circuit.png` and `forged-piercing-beam.png` under the ignored `artifacts/deep-salvage/` directory.

## Automatic forge

All thirteen recipes run in both ingredient orders in engine tests. Pairwise multiset checks reject duplicate/subset recipes. The larger recipes use upgraded components: Piercing amplifier + Overcharger + Rail lens produces Prism overcharger; Trident + Prism mirror + Fusion core + Heavy laser produces Duplicator.

Tests verify automatic start on the last ingredient, exactly-once payment/output, waiting for cash, pausing timers, queueing behind the current job, arbitrary unrelated ingredients, six-slot capacity, occupied-slot rejection, and moving unused ingredients during a job. Only matched slots lock and clear; leftovers survive. Completion stacks the output and triggers the standard discovery introduction.

Browser checks forge duplicate, mixed, three-part and four-part recipes through actual drag controls, inspect partner highlights in the lab/hold/battlefield, install outputs, and verify enhanced icons and stronger piercing beams. Forge-only fixtures delay enemy spawning so cash assertions and timers are independent of combat rewards and defeat. Combat runs normally in the separate gameplay scenarios. Screenshots include `automatic-forge-working.png`, `recipe-manual.png`, `three-part-forge.png` and `four-part-forge.png`.

## Gameplay retained

Regression coverage includes first discovery and local persistence, repeated salvage, loot expiry/flashing, held-drop protection, pause/manual/background clocks, victory/defeat/restart, all-side component inputs and terminating feedback loops.

Continuous laser, pulse and support tests cover frame-rate-independent damage, armor/piercing/shields, charge thresholds, independent terminals, full/disconnected/paused charge, grid moves versus stacking, healing caps and no resurrection. Browser scenarios exercise pulse, Shield and Medic installation, charging/restoration and manual pause. Damage screenshots show shield rings, hull flashes, recoil and feedback numbers.

All three maps and ten enemy roles remain tested, including sniper range, leech shield drain, mender healing and bomber self-destruction without kill rewards. Route selection changes scenery/encounters, restart preserves the chosen map, and cancelling selection preserves the active dive. The manual contains 20 parts, 13 recipes, 10 enemy descriptions and a route atlas.

Deterministic balance tests confirm the untouched starter loses in wave two. An affordable Overcharger plus salvaged lens clears the 39-enemy city with 54 hull; adding Medic yields 70, or Shield yields 80. Foundry requires further investment: forging a Heavy laser in the first refit is a verified victory using available inventory and earned cash. Killing all scheduled enemies generates ten parts; every player kill awards cash.

The preview URL includes `?ntl-drawer-state=hidden` so Netlify's review drawer does not cover gameplay controls. No production deployment is performed.
