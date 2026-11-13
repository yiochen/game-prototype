# Boulderhead Parrotfish broken path · issue #76 review

Interactive HTML prototype for discussing #76's mechanics before any art or Godot work. It builds on the approved #24 chase and #25 creature-chunk pattern, like `../inkfin-preview/`. Open it through the Vite site at `/prototypes/sushi-loop/design/boulderhead-preview/`.

**Approved** (user, 2026-11-13) and implemented in Godot: see the #76 entry in `../../AGENTS.md`. The reef sounds now live in `godot/assets/audio/generate_audio.py`.

## Direction under review (user, 2026-11-12)

- **Crash through.** Brittle reef shatters when the submarine hits it, at a hull cost and a short slowdown. The ship is never trapped, but the broken path is the cheap way through. Bedrock stays solid.
- **Winding channel.** The parrotfish carves one continuous breach through solid reef, weaving round bedrock (as in the concept), not one gate per barrier.
- **Random fair line.** Each reef chunk stores several lines that pass the fairness check; a dive picks one per chunk, so the route can't be memorised.

## Flow

1. **Chase.** The parrotfish is already hooked. Route version 7 plan: ordinary → reef, three times, then ordinary. Speed, resistance (220), rock hits and the catch are as in #24.
2. **Reef chunks.** Dense pale **brittle reef** round a few **bedrock** outcrops, with open water at the entry and exit. In reef chunks, bedrock uses only the dark approved rocks, so pale always means breakable. The first one shows "Reef ahead! · Follow the broken path".
3. **Smash.** The fish swims 5.6 rows ahead and follows its line. White cracks spread over the next breach cells for 0.6 s. Then its nose reaches them and they shatter, losing collision on the same frame, with a lunge, fragments and a dust puff. Fragments are cosmetic. Broken reef stays open, with rubble on the seabed.
4. **Off the path.** The hull shatters any brittle reef it touches: 15 hull (once per hit protection) and a 0.7 s slowdown to 55%, with no knock-back. Bedrock and ordinary rock work as in #24 (25 hull, knock-back).
5. **Hit feedback** (user, 2026-11-13: players couldn't tell they had hit anything; approved the same day, and it must apply to **every** dive hit, on all maps and with all creatures, not only reef). Every hull loss, from reef or rock: a red glow along all four screen edges, a 70 ms hit-stop, a shake, sparks and fragments at the contact, the red hull tint and wobble, a red "−15"/"−25" rising off the ship, and the hull bar shaking with a red glow. A crash during hit protection costs nothing, so it gets a jolt, fragments and a quieter crunch, but no red.
6. **Rounded breach** (user, 2026-11-13: the path looked too narrow to pass). Each reef block is drawn on its collision shape: open faces inset, faces against rock flat, exposed corners rounded (`rock_corner_radius`). When a neighbour breaks, the corners it exposes round off at once, so the breach looks as wide as it flies. **The production 3D reef pieces must do the same**: blocks next to broken cells need rounded exposed corners, not square ones.
7. **Sound.** Synthesized like the game's cues (`audio/generate_reef_audio.py`; on approval they move to `godot/assets/audio/generate_audio.py`):
   - `reef_breach`: the fish's first ram into each reef wall. A double boom, a rumble and falling rubble.
   - `reef_smash`: each row it breaks after that. A short thump and crunch with pebbles, pitch varied ±12%, at most one every 90 ms.
   - `reef_crash`: the submarine ramming reef. A metal clank over the crunch; quieter when hit protection absorbs it.

   The Sound box turns them off. The browser plays sound only after the first key or touch.

## Fair lines (`reef.js`)

The question: can the player always follow the breach at chase handling?

- **Line.** One column centre per reef row. It is carved bottom to top towards random waypoints, turning at most `max_shift_columns` per row (0.8; the ship manages about 1.1). Its `breach_columns`-wide strip (2) must never overlap bedrock.
- **Bot.** A steering bot with the ship's real lateral speed and acceleration, a 0.3 s reaction and 1.2 rows of look-ahead (well inside the fish's lead) flies each line. It starts from the left, centre and right of the water before the reef. A line is fair only if the bot never touches reef from any of the three starts.
- **Table.** Each chunk keeps up to 6 fair lines from 40 candidates. In Godot this becomes a table written into the chunk document by a tool, as with the eel's discharge table.

**Finding.** `node check.mjs`: all four reef chunks give 6 fair lines at the defaults, and each passes route validation. Steeper turns start to fail: at 1.2 columns per row, 13 of 19 candidates in Bedrock Slalom are rejected; at 2.2, all are.

## Review controls

| Control | What it does |
|---|---|
| **Parrotfish lead**, **Crack warning** | How far ahead the breach appears, and how long the cracks show before each smash. |
| **Breach width**, **Sharpest turn** | Re-carve and re-check every line, then restart. |
| **Crash-through damage**, **slowdown** | The cost of leaving the path. |
| **First reef chunk** | Forces a chunk into the first reef slot. |
| **Show the parrotfish's line** | Draws each reef chunk's chosen line and its name. |
| **Reef chunks & fair lines** tab | Every reef chunk with its fair (gold) and rejected (red) lines. |

## Placeholders

- The parrotfish is the static concept GLB (`assets/creature-boulderhead-parrotfish/`, no rig). Swimming, the ram lunge and the hook point are faked with transforms.
- **Reef model** (2026-11-13, awaiting approval): `assets/expedition/v2/reef.py` builds the reef in Blender with the boulder-underwater round-04 recipe's camera, square footing, lights and material, like the v2 rocks. It gives 16 neighbour masks (bits as the seabed beds: N=1, E=2, S=4, W=8) × 3 slab patterns, plus 2 rubble scatters. Each cell's ground footprint is the collision shape: exposed corners rounded at `rock_corner_radius`, open faces inset, cell edges against reef flush. Sprites: `assets/expedition/v2/sprites/reef-*` (not yet in `library.json`). Shape and height approved by the user (2026-11-13). The limestone surface (warm peach tops, banded tan fronts, branched hairline cracks, chipped groove-side corners, no cast shadows) was rebuilt natively against an imagegen style target and approved by an independent judge in round 03. Experiment, target, reviews and final hashes: `assets/production/source/blender/refinement/breakable-reef/`. Non-exposed corners are now near-square (0.015).
  - **Less tidy shape** (user, 2026-11-13, awaiting approval): slab tops slant their own way (up to 0.34 height per cell, low edge kept above the groove core), slab heights spread wider, and open and groove sides lean inward towards the top (flush seams stay vertical, so cells still join). The collision footprint is unchanged. This changes the judge-approved round-03 render, whose exact bytes stay in the experiment's `final/`.
  - **Crack and break spritesheets** (user, 2026-11-13: replace the code-drawn hairlines): `assets/expedition/v2/reef_break.py` renders, per piece, crack-1..3 (fractures run from the impact point on the south edge across every slab, longer and wider each stage, shown over the crack warning) and break-1..6 at 12 fps (the slabs split along those fractures, the chunks burst up and away, biased north, then land as low fragments). break-6 is the rubble the cell keeps. `publish-reef.mjs` puts each piece's nine frames side by side in `sprites/reef-break/<id>.png`. A breaking cell uses the piece it was drawn as when it broke. Code shards are cut to a quarter (the sheet draws the chunks); the dust puff and bubbles stay.

  **Reef art** switches back to the code placeholder, which keeps the code-drawn cracks. Nothing grows on top of the reef (#21 direction), so the placeholder's coral is gone from the model.
- The sounds are synthesized placeholders.
- The HUD icon is a code-drawn SVG (`parrot-icon.svg`). The award shows a placeholder recipe.

## Checks

- `node check.mjs`: fair lines and route validation per reef chunk.
- Headless captures at 390×844 (2×), with no console errors, are in `review/76/prototype/`. A simple autopilot that follows the line flew them.
