# Prototype verification — 2026-09-27

- `npm test`: 78 engine tests passed across the repository, including 18 Deep Salvage tests.
- `npm run build`: passed. Vite reports the shared Phaser chunk above its default 500 kB advisory threshold; the prototype's own JavaScript is approximately 30 kB before gzip.
- `npx playwright test prototypes/deep-salvage/tests/game.spec.js`: 10 browser scenarios passed against the production build.
- Catalog navigation to the new game and canvas boot checked independently, without page errors.

Portrait layouts verified at 412 × 924, 448 × 1000, 412 × 820 and 360 × 740 CSS pixels. Landscape verified at 924 × 412. Grid cells remain at least 44 CSS pixels at these sizes, the board stays above storage, and the normal play screen does not scroll. Mobile touch input was exercised at 3× device scale. These checks emulate Pixel 10 Pro-shaped browser viewports; no physical phone was connected.

Browser coverage includes real taps and drags, an actual enemy drop, direct installation, stacked storage, occupied-cell rejection, pointer cancellation, tap rotation, touch drag completion, keyboard rotation/removal, a complete two-gun build through the controls, first discovery, persisted discovery history, guide/pause clock freezing, flashing/expired loot, defeat/restart, and victory.

Inspected screenshots are written under `artifacts/deep-salvage/`, including `pixel-10-pro.png`, `small-phone.png`, `landscape.png`, `two-gun-circuit.png`, `first-discovery.png`, and `installed-lens.png`. The rendered art is produced by Phaser and the live DOM interface, not a static mockup.

The opening wave leaves room to learn. Deterministic balance checks confirm that the untouched starter machine eventually loses in wave three, while a machine upgraded with another amplifier and a piercing lens can reach the beacon. Tuning remains intentionally centralized in `balance.js`.

Interaction follow-up: drag highlighting and release use the floating preview center rather than the finger. Mouse and touch regressions cover a finger outside the highlighted cell, occupied preview targets, bottom-row placement, returning parts to storage and cancellation. Amplifiers, lenses, splitters and guns accept all four input directions; only reactors and mirrors rotate. Tests cover all input sides, retained straight-through travel, relative splitter branches, combined gun inputs, feedback termination and a horizontal circuit in the browser. The corresponding screenshots are `preview-aligned-bottom-row.png` and `omnidirectional-circuit.png`.
