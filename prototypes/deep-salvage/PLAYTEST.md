# Prototype verification — 2026-09-27

- `npm test`: 87 engine tests passed across the repository, including 27 Deep Salvage tests.
- `npm run build`: passed. Vite reports the shared Phaser chunk above its default 500 kB advisory threshold; the prototype's own JavaScript is approximately 42 kB before gzip.
- `npx playwright test prototypes/deep-salvage/tests/game.spec.js`: 14 browser scenarios passed against the production build.
- Catalog navigation to the new game and canvas boot checked independently, without page errors.

Portrait layouts verified at 412 × 924, 448 × 1000, 412 × 820 and 360 × 740 CSS pixels. Landscape verified at 924 × 412. Grid cells remain at least 44 CSS pixels at these sizes, the board stays above storage, and the normal play screen does not scroll. Mobile touch input was exercised at 3× device scale. These checks emulate Pixel 10 Pro-shaped browser viewports; no physical phone was connected.

Browser coverage includes real taps and drags, an actual enemy drop, direct installation, stacked storage, occupied-cell rejection, pointer cancellation, tap rotation, touch drag completion, keyboard rotation/removal, a complete two-gun build through the controls, first discovery, persisted discovery history, guide/pause clock freezing, flashing/expired loot, defeat/restart, and victory.

Inspected screenshots are written under `artifacts/deep-salvage/`, including `pixel-10-pro.png`, `small-phone.png`, `landscape.png`, `two-gun-circuit.png`, `first-discovery.png`, and `installed-lens.png`. The rendered art is produced by Phaser and the live DOM interface, not a static mockup.

The opening wave leaves room to learn. Deterministic balance checks confirm that the untouched starter machine loses in wave two. A simulated player using only the starting cash and inventory to forge an Overcharger, then installing the first salvaged lens, completes 39 enemies with approximately 28 hull remaining. The full run generates 10 part drops; every kill awards cash. Tuning remains intentionally centralized in `balance.js`.

Interaction follow-up: drag highlighting and release use the floating preview center rather than the finger. Mouse and touch regressions cover a finger outside the highlighted cell, occupied preview targets, bottom-row placement, returning parts to storage and cancellation. Amplifiers, lenses, splitters and guns accept all four input directions; only reactors and mirrors rotate. Tests cover all input sides, retained straight-through travel, relative splitter branches, combined gun inputs, feedback termination and a horizontal circuit in the browser. The corresponding screenshots are `preview-aligned-bottom-row.png` and `omnidirectional-circuit.png`.

Forge and combat follow-up: all eight recipes are exercised in both ingredient orders, including payment, affordability, locked jobs, paused timers, exactly-once output, first discovery and cancellation before payment. Browser tests cover match glows in the lab, hold and battlefield, invalid ingredients, duplicate/mixed recipes, cash gating, output installation, and proportional/piercing beam appearance. Shield tests verify absorption, hull spillover, delayed regeneration and three-target piercing; Phaser screenshots show blue shield ripples, hit tints, recoil and damage numbers. Forge controls fit the shorter phone and landscape layouts. Screenshots include `forge-working.png`, `forge-matching-parts.png`, `forge-360x740.png`, `forged-piercing-beam.png` and `combat-shield-impact.png`.
