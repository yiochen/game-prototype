# Inkfin Cuttlefish — creature for issue #70

Live 3D creature, like the Storm Eel: one skinned GLB with named clips, crossfaded at runtime.

**Status:** approved by the user on 2026-11-11 from `design/inkfin-preview/`. In Godot (#70) the same GLB is copied to `godot/assets/expedition/creature/inkfin-cuttlefish.glb` and rendered live by `godot/scripts/expedition/creature_view.gd`. Re-copy it there after any re-export.

## Design

- **Style.** Low-poly, flat-shaded and a real animal, following the approved Storm Eel v2 rules: gold eyes with a dark slit pupil, no lids, no face.
- **Colour.** Deep violet back with lighter zebra bands, pale lavender skirt fins and belly, pink glow spots. It stands out on the turquoise seabed.
- **Direction.** It jets mantle-first, as a fleeing cuttlefish does. The pointed mantle tip leads north; the head and arms trail south, towards the ship. The camera sees the patterned back, the eyes and the arms, and the funnel (where the ink leaves) points back at the ship.
- **Reference.** `concept/issue-70-concept.jpg` is the issue's inspirational mock. No new concept image was generated; the model was built from the brief, as Storm Eel v2 was.

## Files

- `source/build_model.py`: procedural model and rig. Run in Blender on an empty file.
- `source/build_actions.py`: the clip set. Run after the model.
- `source/inkfin-cuttlefish.blend`: editable result.
- `export/inkfin-cuttlefish.glb`: runtime candidate (≈553 KB, 791 vertices, 21 bones, 10 clips).
- `validation/`: Blender angle and pose views, and the model in the HTML preview.

## Rig

**Axes:** X right, +Y north, Z up, 1 unit = 1 cell. The body is about 2.1 × 4.3 cells, swimming 0.8 cells above the seabed. Every bone points +Y with roll 0, so bone axes equal world axes.

| Bones | Job |
|---|---|
| `root` | Ground root; only `escape` moves it. |
| `body` | Whole-animal position and rotation. |
| `mantle`, `mantle_tip` | Scale on `mantle` is the jet pulse and the ink-sac swell; the tip flexes. |
| `head` | Head, eyes and funnel. |
| `arms.L_0–2`, `arms.R_0–2` | Each side's four arms: yaw spreads or closes them, pitch lifts or droops them. |
| `fin.L_0–4`, `fin.R_0–4` | Skirt fins; a phase step along the row makes a travelling wave. |

## Clips

Names match the Storm Eel's, so the runtime drives both the same way. 30 fps.

| Clip | Frames | Loop | Purpose |
|---|---|---|---|
| swim | 60 | ↻ | Jetting ahead of the ship; fins ripple |
| restless | 30 | ↻ | Faster fins, arms flaring |
| hit | 18 | – | Harpoon impact: jolt and arm flare |
| hooked | 20 | ↻ | Straining north in hard jet pulses |
| struggle | 24 | ↻ | Thrashing, arms whipping |
| windup | 30 | – | Ink warning: the mantle swells and trembles, arms pull in, fins tuck |
| attack | 18 | – | Ink burst: the mantle clamps, the animal kicks north, arms flare |
| recover | 27 | – | Back to the swim pose |
| escape | 36 | – | Bursts north off screen (root motion +9 cells) |
| exhausted | 60 | ↻ | Caught: rolled on its side, arms limp |

## Engine-driven effects

- The glow spots (`inkfin_spot` emission) are not baked; the engine drives them, as with the eel.
- The ink itself is drawn by the game, not the model.

## Open items

- Only swim and windup have been inspected frame by frame in Blender; the other clips have been seen only in the preview.
- A dedicated HUD icon and a hit shape.
