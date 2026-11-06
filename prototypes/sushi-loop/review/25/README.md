# Issue #25 · Storm Eel discharge

## Approved prototype

`design/eel-strike-preview/` was approved by the user on 2026-11-05, with two revisions:

- no countdown ring: the strip flashes a few times, then strikes;
- a catch clears any strip or lightning at once.

Its captures are in `prototype/`.

## Native evidence

Captures are in `native/phone/`, made with `tests/capture_expedition_discharge.gd` on the real game (Metal, 390×844, plus 405×720 and 600×820).

| Capture | Shows |
|---|---|
| `01-eel-chunk` | Hooked, entering an eel chunk (DEBUG · Eel zone skip). |
| `02-windup-steady` | One fixed strip: amber fill, diagonal hatching, dashed edges, lightning badges. The eel plays `windup`. |
| `03-windup-flash-on`, `04-windup-flash-off` | The last 0.6 s flashes 3 times (no countdown). |
| `05-strike-dodged` | The live strike with bolts and the `attack` clip; the ship is clear and takes no damage. |
| `06-strike-hit` | A ship in the strip loses hull: red flash and electric sparks, no knock-back. |
| `07-caught-mid-strike` | Catching the eel during a strike removes the strip and lightning at once. |
| `08-windup-405x720`, `08-windup-600x820` | The warning on a 16:9 phone and a wider window. The top badge sits below the HUD row. |

## Rules evidence

`tests/expedition_discharge_tests.gd` covers:

- **Library.** Four accepted eel chunks, each with a current table. A stored table matches a fresh fairness search. A reef edit is rejected, and a stale table leaves its chunk out.
- **Route.** Version 5 alternates ordinary and eel chunks after the arena; version 4 keeps its all-ordinary pursuit.
- **Where it attacks.** Aiming and ordinary chunks are attack-free.
- **The strike.** The strip comes from the table and does not track the ship. The timing is 1.4 s windup, then 0.5 s live, then a cooldown. A hit costs hull only: once, with no knock-back and no change to resistance.
- **Pause and save.** Pause and save/reopen keep the warning, and a restored strike cannot hit twice.
- **Endings.** A catch mid-strike completes the run. Zero hull from lightning lets the eel escape.
- **Bad saves.** Corrupt discharge saves are rejected, and pre-#25 hooks restore without a discharge.
- **Fair routes.** At each windup in both eel chunks of three routes, a ship starting from any open position across the chunk gets through the real rules without a hit, using one of a few simple steering patterns after the reaction delay. Positions where none of those patterns gets past the rocks even without a strike are skipped.

## Tables

`godot/tools/discharge_tables.gd` writes each creature chunk's table into its document. Run it again after editing a creature chunk or the discharge or handling balance.
