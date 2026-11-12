# Inkfin Cuttlefish ink blackout · issue #70 review

Interactive HTML prototype for discussing #70's mechanics before any art or Godot work. It builds on the approved #24 chase and #25 creature-chunk pattern (`../eel-strike-preview/`). Open it through the Vite site at `/prototypes/sushi-loop/design/inkfin-preview/`.

**Approved** (user, 2026-11-11) and implemented in Godot: rules in `expedition_book.gd`, the sight check in `sight.gd`, the ink layer in `ink.gdshader`. This page stays as the reference.

## Direction under review (user, 2026-11-11)

- The ink covers the **whole screen**. The submarine's **light** cuts through it, so the player sees only the water just ahead.
- For comparison, the earlier idea is still available: a clear band at the bottom with the ink covering the top of the screen (**Light → Band**).

## Flow

1. **Chase.** The cuttlefish is already hooked. Ordinary chunks alternate with ink chunks, as in #25: normal → ink → normal → ink → normal.
2. **Warning.** When the ship enters an ink chunk, the cuttlefish's spots pulse and the screen edges pulse purple three times over 1 s. The whole sea is still visible, giving one last look ahead.
3. **Ink.** The ink seeps out from the cuttlefish gradually, over 1.6 s (user, 2026-11-11: 0.5 s was too sudden). It stays for the rest of the chunk and 15 rows into the next one, to make it harder (user, 2026-11-11), then lifts over 1 s. It only lingers into a chunk that passes the sight check too. There is one burst per chunk.
4. **Light.** The forward cone has a curved front, an arc round the ship like a torch beam (user, 2026-11-11). It is 3 rows deep and 5 columns wide at its far end, with a soft glow round the hull. Steering tilts the cone up to 18°, so the player can look the way they are turning. The light doesn't clear the water: everything it shows is monochrome purple, like grayscale tinted purple (user, 2026-11-11; a slider blends it back towards full colour).
5. **What shows above the ink.** The cuttlefish **hides inside the ink**, so only the cable stays visible, pointing the way it went (user, 2026-11-11; switchable for comparison). Pickups glow lime through it, following the dive's "good" signal (optional). Under the ink, the cuttlefish swims towards safe water near the ship, so following it is a hint (optional).
6. **Rules that don't change.** Ink does no damage and never changes collision; rock hits work as in #24. A catch or an escape clears the ink at once.

## Sight check (`sight.js`)

The question: can the player avoid a crash they had no chance to see?

At chase handling (1.4× forward, 3.3 columns/s sideways), the ship can move at most 1 column sideways per row it rises. The check works on a grid of cells:

- **Safe cell:** the top of the chunk can still be reached from it.
- **Doomed cell:** reachable from the entry, but not safe.
- **Fork:** a safe cell with a doomed next step. The player must see the end of the doomed branch before committing to it. That needs branch depth + 1.5 rows + a 0.3 s reaction (about 0.9 rows).
- **Cone width:** in cone mode, the end of the dead branch must also lie inside the beam, allowing for steering tilt.
- **Baseline:** any rock needs at least 1.5 rows plus the reaction distance (2.4 rows) to dodge.

A chunk can be an ink chunk only when its worst fork fits the current settings.

**Finding.** Run `node check.mjs` with the default 3 clear rows. Every ordinary chunk and all but one fork chunk pass, each needing 2.4 rows. The exception is **Ruin Split**, which needs 3.4 rows: its forks lead into dead branches that are only visible too late. The ink therefore needs **no new terrain to be fair**; new ruin chunks would be for theme only. A 2-row light would rule out every chunk.

## Review controls

| Control | What it does |
|---|---|
| **Light** | Switches between the cone and the earlier band idea. |
| **Clear rows**, **cone width**, **tilt**, **spread time**, **linger**, **darkness**, **purple tint** | Tune the light and the ink. Clear rows and cone width re-run the sight check and restart the chase. |
| **First ink chunk** | Forces a chunk. An unfair one is allowed here so you can feel why it is rejected (try Ruin Split). |
| **Show ink chunks and sight check** | Shows the clear-sight line and each ink chunk's forks: green if the dead end is seen in time, red if not. |
| **Ink chunks & sight check** tab | Every candidate chunk, with its dead ends and its verdict. |

## Creature and placeholders

- The cuttlefish is its own low-poly model, `assets/creature-inkfin-cuttlefish/` (awaiting approval).

- The HUD icon is a code-drawn SVG in the eel icon's style (`cuttle-icon.svg`, the game's `inkfin-icon.svg`).
- The award here still shows "Placeholder recipe"; the game awards Ika nigiri (`dish/`).

Terrain, submarine, cable, HUD, award and results are the approved #21–#25 art, unchanged.

## Checks

- `node check.mjs`: lists the verdict for each chunk at the current `balance.json`.
- Headless captures at 390×844 (2×), with no console errors, are in `review/70/prototype/`:
  - `1-warning.png`
  - `2-cone.png`
  - `3-cone-steer-left.png`
  - `4-band.png`
  - `5-ruin-fork-unfair-overlay.png`
  - `6-chunks-tab.png`
