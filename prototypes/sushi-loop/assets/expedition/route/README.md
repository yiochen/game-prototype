# Expedition routes · issue #21

Runs are assembled from **chunks**: short hand-made maps joined at random under a seed. A chunk is a map-designer document. There is no build step: the game, the review page and the designer analyse chunks when they load them.

## Chunk files

`godot/content/expedition/chunks/<id>.json`, one file per chunk, in the designer's `sushi-loop-underwater-map` version 1 format. The file name is the chunk id. Chunks are **11 columns** wide (the world); the screen shows 7 and follows the ship sideways.

| Layer | Meaning |
|---|---|
| `obstacles` | Rock (collidable) |
| `decor` on rock | Growth mark: `decor-kelp`, `decor-foreground-coral`, `decor-midground-coral` |
| `decor` on water | Seabed dressing (starfish / sunken boat silhouettes) |
| `pickups` | `salvage-gold`, open water only |

```json
"chunk": { "kind": "fork", "difficulty": null, "source": "authored (wide)" }
```

`kind` is `launch`, `start`, `normal`, `rest`, `fork` or `finish`. `difficulty` is `null` (computed) or a 1–5 override.

`launch` chunks are the open-water lead-in the preparation screen cruises through before the player presses: keep a straight clear lane down the middle (the ship holds the start column) and no gold. Only another launch chunk or the start chunk may follow one.

## Editing without rebuilding

1. Open the map designer, **Import** a chunk file (or **New map → Route chunk · 11 × 16**).
2. Paint obstacles, decor and gold. The **Route chunk** panel validates live with the same rules the game uses and shows the computed difficulty.
3. **Test in route preview** opens the expedition review with this chunk forced into a seeded run.
4. **Export JSON** and save it into the chunk folder. Reload the review page or restart the Godot game; no other step.

An invalid chunk is reported (browser console, Godot warning) and left out of runs; it never breaks the game. `node …/validate-chunks.mjs` prints the library and fails on invalid chunks.

## Rules (route.js / route.gd)

- **Seams:** chunks join only where the exit row of one and the entry row of the next share an open run at least 2 cells wide, and the joined pair is proven passable.
- **No dead ends:** every cell reachable from the entry must be able to rise to the exit. A reachability check that respects steering speed (2 cells sideways per row) must reach the exit, and every gold piece must be reachable.
- **The real hull flies it:** steering is a joystick with a finite sideways speed, so validation also flies the ship's collider (0.64 × 0.88 cells) through the chunk at quarter-column, sixth-of-a-row resolution, sliding at most 1.5 columns per row (full stick). The exit must be reachable, every gold must be collectable without getting stuck, and no lane may be enterable but not leavable (**trap lane**). One-cell lanes that step diagonally every row fail this: give a lane two rows at a column before it shifts, or make it two cells wide.
- **Seams fly too:** a chunk may follow another only if their shared open run is at least two cells wide and the hull flies the four rows either side of the seam without new problems.
- **Difficulty:** 1–5 from narrowness, required swerving and rock density inside the passage.
- **Runs:** `launch, launch, start, 1.5, 2, rest, 2.5, fork, 3, 3.5, rest, fork, 4, finish` (balance: `godot/content/expedition.json`). Each slot picks a compatible chunk weighted toward the target difficulty and away from repeats. Same seed → same route.
- **Scene:** rock cells become one standalone production or same-recipe piece over the ground layer; growth marks become coral/kelp about 40% of the time; landmarks (ruined arches, bridges) span 1–3 cell passages with legs on the bordering rock.

`route.js` is the reference shared by the review and designer. `godot/scripts/expedition/route.gd` is a line-for-line port; `godot/tests/expedition_route_tests.gd` checks it against `parity-fixture.mjs` output for fixed seeds (hash, RNG, library analysis, sequences, grids and every placed piece). Regenerate the fixture after changing either side:

```sh
node prototypes/sushi-loop/assets/expedition/route/parity-fixture.mjs
```

## Tests

```sh
node --test prototypes/sushi-loop/tests/expedition-chunks.test.js
node prototypes/sushi-loop/assets/expedition/route/validate-chunks.mjs
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/expedition_route_tests.gd
```
