# Storm Eel discharge in creature chunks · issue #25 review

Interactive HTML prototype for approval before Godot work, per the game-ui-prototype workflow. It builds on the approved #24 chase (`../pursuit-preview/`). Open `index.html` through the Vite site (`/prototypes/sushi-loop/design/eel-strike-preview/`).

**Approved** (user, 2026-11-05) and implemented in Godot: the four eel chunks now live in `godot/content/expedition/chunks/` with their fair-strike tables, the rules in `expedition_book.gd` and `discharge.gd`, and the drawing in `discharge_art.gd`. This page stays as the reference and keeps the rejected Reef Squeeze example.

## Decisions it reflects (user, 2026-11-05)

- **Creature chunks.** Each creature gets dedicated map chunks. The Storm Eel's are wide open water, and the eel discharges **only** inside them, never in ordinary chunks.
- **Chase plan.** Ordinary and eel chunks alternate: normal → eel → normal → eel → normal (`pursuit_plan` in `balance.json`).
- **Library.** Four eel chunks: Open Basin, Pillar Basin, Opening Funnel and Island Lanes.

## Flow

1. **Chase.** The eel is hooked, and the chase runs at 1.4× as in #24.
2. **Windup.** Once the ship is inside an eel chunk, the eel chooses one fixed strip, 2 or 3 columns wide, that leans towards the ship but does not track it. It glides over the strip and charges for 1.4 s. The strip shows:
   - amber fill;
   - scrolling diagonal hatching;
   - dashed amber edges with an ink outline;
   - two lightning badges, one under the HUD and one below the ship.

   There is no countdown. The strip holds steady, then flashes brightly 3 times in the last 0.6 s before it goes live (user, 2026-11-05). Reduced motion holds it bright instead of flashing. The water outside the strip stays untouched, so the safe lane reads clearly.
3. **Strike.** For 0.5 s, jagged bolts run from the eel down the strip, which turns white-hot, with a soft screen flash. A ship inside the strip loses 25 hull: hit protection applies, it shows the red hull tint and electric sparks, and there is no knock-back. A brief afterglow follows, then a 1.6–2.4 s cooldown.
4. **Catch or escape.** When the chase ends, any warning, live strike or afterglow is removed at once (user, 2026-11-05).
5. **Fairness.** It is checked when the chunks load, so the eel never searches terrain during play. See below.

## Fairness rules (`fairness.js`)

A creature chunk is a map-designer document with `chunk.kind: "creature"`, `creature: "storm-eel"` and `attack_rows`: the chunk rows (counted from the top) where a strike may be live.

For every strike row in that window, sampled every 0.5 rows, and every cell-aligned strip:

- **Meaningful:** the strip lies over at least 1.5 columns of open water.
- **Fair:** every position the ship could hold when the windup starts, and that would get through the terrain alone, can still get through the strike. The ship must stay 0.25 columns clear of the strip and never touch rock. The check assumes a 0.3 s reaction and 70% of the ship's real sideways speed. It uses the same rounded-square rock collision as the game.
- **Accepted:** a chunk is accepted when every strike row offers at least 2 fair strips. A rejected chunk never joins the library.

At run time, a windup starts only when the coming strike row matches the table. The eel picks only from that row's fair strips that are on screen.

`node check.mjs` runs the same checks in Node and also verifies the seams against the ordinary chunks. `eel-reef-squeeze` is a deliberate bad example and is expected to be rejected.

## Review controls

| Control | What it does |
|---|---|
| **Jump to the next eel chunk** | Moves the ship to the next eel chunk. |
| **Hold resistance** | Keeps the eel from being caught, so you can explore every chunk. |
| **Route seed** and **First eel chunk** | Vary the route and force which eel chunk appears first. |
| **Slow motion ¼×** | Plays everything at a quarter of normal speed. |
| **Show eel zones and fair strips** | Overlays chunk names, attack-row brackets and the fair choices during a windup. |
| **Eel chunks & fairness** tab | Shows each chunk beside its fairness tables, plus the rejected example. |

## Asset map

| Surface | Source |
|---|---|
| Terrain, seabed, gold, submarine, Storm Eel GLB, cable, HUD | Approved #21–#24 assets, unchanged; the award backdrop comes from `../pursuit-preview/award-art/` |
| Eel chunks | `chunks/*.json`: map-designer documents using existing rock, coral, kelp and gold pieces |
| Warning strip: fill, hatching, dashed edges | Code-drawn on the world canvas, under the eel |
| Lightning badge | Code-drawn (amber disc, ink rim, white bolt); a candidate for an ImageGen badge in the native pass |
| Bolts and strike glow | Code-drawn, regenerated every 60 ms (200 ms with reduced motion) |
| Eel clips | `windup` while charging and `attack` while striking, with brighter spot glow |

Balance is in `balance.json`. On approval, `discharge` and `pursuit_plan` join the Storm Eel's encounter definition in `godot/content/expedition.json`, and the eel chunks move to `godot/content/expedition/chunks/` as a new chunk kind.

## Checks

- `node check.mjs` passes: all four chunks are accepted, the reef example is rejected, and every chunk joins 13 ordinary chunks at both seams.
- Captured headlessly at 390×844, 320×720, 405×720 and the wider window, with no console errors. Captures are in `review/25/prototype/`.
