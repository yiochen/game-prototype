# Issue #23 · native Godot evidence

Approved HTML compositions (2026-11-04/05):
- `design/storm-eel-preview/`: the Storm Eel v2 model and clips.
- `design/harpoon-preview/`: the harpoon, button, slow motion and callouts.

Draft review link: `https://storm-eel-harpoon-23--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/harpoon-preview/`.

User decisions:
- The Harpoon button sits centred between the steering arrows, not in the lower right.
- A hit pins the harpoon to the struck body part.
- The rope draws over the world: obstacles never hide or cut it.
- A strike plays in slow motion, with a focus circle closing on the impact.
- "Hooked!" and "It got away" are plain outlined text without a backing.
- No lightning: eel discharges belong to #25.

## What is implemented

**Arena.** Route version 3 inserts an open-water arena (44 rows, seven open columns) before the finish. Saves from #22 keep route version 2 and never meet an encounter. A few rows into the arena, the Storm Eel arrives from the north and swims 5.6 rows ahead of the ship, weaving sideways. The shooting window opens with no countdown, and resistance stays full.

**Hit area.** A fixed ellipse in the rules (`hit_half_columns`, `hit_half_rows`), whatever the animation does.

**Harpoon.** `expedition_fire` launches one harpoon straight up from the ship's nose on a fresh press. Holding, repeated presses and key repeat never fire again. A miss reels back, and the button's ring fills amber until the 1.6 s reload ends (green ring = ready). No ammunition is spent. Steering touches (playfield halves) and the button's touch are independent.

**Restless and escape.** The eel turns restless for the last 4 s of the 16 s window, keeping its movement and hit area. Expiry without a hook lets it escape ("It got away · No recipe this time"); the route then finishes normally with no recipe.

**Hook.** A hit records one hook (`along`/`across` on the body) and holds the run still: ship, creature and timers stop advancing travel, the arrows dim and the button disappears. This is the saveable handoff for #24's pursuit. It awards nothing and never turns into a catch or escape by itself; Pause → Return early leaves.

**Save and pause.** Save/restore and Pause preserve the window, a shot in flight, the reload and the hook. Reopening resumes behind Paused, as before.

**Presentation.**
- The eel is the approved GLB, rendered live (`creature_view.gd`): ordinary orthographic camera at 35°, seven columns, flat Lambert light, 135% contrast.
- Its glow is driven per clip; soft shadow blobs follow its spine.
- Slow motion is presentation time only: the rules just receive smaller elapsed steps.

Balance lives in `godot/content/expedition.json` → `encounter`.

## Screenshots

`phone/` (390 × 844) and `wide/` (1100 × 820, portrait-contained) from `tests/capture_expedition_encounter.gd`, on Metal (Forward Mobile):

| File | State |
|---|---|
| 01 | Window open: eel ahead, resistance pill, Harpoon ready (green ring) |
| 02 | Shot in flight with its rope; the ring reloading |
| 03 | The miss reeling back |
| 04 | Strike slow motion: the focus circle closing on the impact |
| 05 | Hooked: the harpoon pinned, flash ring, "Hooked!" callout |
| 06 | Holding the hook: taut rope, arrows dimmed, no button |
| 07 | Paused over the hook |
| 08 | Restless before the window closes |
| 09 | Escaped: "It got away" |

## Checks

- `tests/expedition_encounter_tests.gd`: 46 rule checks through the command/time/save boundary.
- `tests/expedition_features_tests.gd` is updated for the arena edge.
- `tests/capture_expedition_encounter.gd` asserts the button, reload, slow motion, hook, dimmed arrows, restless and escape while capturing.

## Handling follow-up (2026-11-05)

User feedback: the hull ran out before the eel. Changes:
- **Round collision.** A `ship_radius` circle against a `rock_radius` circle per rock cell; corners and glancing passes no longer dent the hull. It stays inside the box chunk validation flies, so validated routes stay passable.
- **Solid rock.** A hit knocks the ship to the nearest clear water (sideways or back, never ahead). The hull is dented once per hit protection; later touches only push the ship out.
- **Hit animation.** A wobble, a red tint, sparks, yellow hull chips and bubbles, with the knock-back sliding out.
- **Banking.** The ship banks into turns.
- **Cheats flag.** One `cheats` flag (`--cheats`, or `tools/build_android.py --cheats`) shows DEBUG · Shield and DEBUG · To Eel.

`handling/` (390 × 844, with `--cheats`) is from `tests/capture_expedition_handling.gd`: 01–02 banking right and left, 03–04 a rock hit, 05 the Shield cheat, 06 the To Eel cheat.
