# Boulderhead Parrotfish (issue #76)

Live 3D creature, like the Storm Eel and Inkfin Cuttlefish: one skinned GLB with named clips.

**Status:** in the game (#76). The rig and clips were approved by the user on 2026-11-13 from `design/boulderhead-preview/` (the "Parrotfish clip" control plays each one). After a re-export, copy `export/boulderhead-parrotfish.glb` to `godot/assets/expedition/creature/`.

Teal checkered parrotfish, boulder forehead, cream beak. Low-poly, flat-shaded, flat colours, in the Storm Eel and Inkfin Cuttlefish style.

- **Size:** 2.8 × 4.9 cells (X × Y), 288 / 327 vertices / faces.
- **Axes:** X right, +Y north (travel direction), Z up, 1 unit = 1 cell.

## Files

- `source/build_model.py`: the model and rig (uses `../creature-kit/kit.py`).
- `source/build_actions.py`: the clip set.
- `source/export.py`: runs both, saves the `.blend` and exports the GLB: `blender -b --factory-startup --python export.py` from `source/`.
- `source/boulderhead-parrotfish.blend`, `export/boulderhead-parrotfish.glb`: the result.
- `validation/poses.png`: clip frames from Blender (exhausted, hit, hooked, struggle, swim). `game-view.png`, `three-quarter.png`: the unrigged concept.
- `concept/issue-76-concept.jpg`: the issue's inspirational mock.

## Rig

Every bone points +Y with roll 0, so bone axes equal world axes.

| Bones | Job |
|---|---|
| `root` | Ground root (no clip moves it; the game carries the escape). |
| `body` | Whole-animal position and rotation. |
| `spine_0` | The trunk; head and tail chain hang off it. |
| `head` | Head, boulder, beak and eyes; counter-yaws so the head stays steady. |
| `spine_1`, `spine_2`, `tail` | The rear chain: yaw with a phase step bends the body in a wave that grows towards the tail fin. |
| `pec.L`, `pec.R` | Pectoral fins: roll flaps them (parrotfish row with them), yaw folds them back. |

Body vertices blend between the two spine joints around their Y; the tail fin follows `tail`, each pectoral its bone.

## Clips

30 fps. The ram lunge and the turn along its line stay in code.

| Clip | Frames | Loop | Purpose |
|---|---|---|---|
| swim | 60 | ↻ | Lazy tail beat, fins rowing |
| restless | 30 | ↻ | Faster beat and rowing |
| hit | 18 | – | Harpoon impact: jolt, fins flare |
| hooked | 20 | ↻ | Straining north: hard tail strokes, fins pulled back |
| struggle | 24 | ↻ | Thrashing and rolling (low resistance) |
| escape | 36 | – | Full-power strokes, fins tucked |
| exhausted | 60 | ↻ | Caught: rolled on its side, curled |
