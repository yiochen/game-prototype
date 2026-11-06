# Storm Eel — boss creature for issue #23

Live 3D creature (not pre-rendered sprites): one skinned GLB with named clips, crossfaded at runtime.
Status: **v2 model + animations approved by the user on 2026-11-04** from `design/storm-eel-preview/`. In Godot (#23) the same GLB is copied to `godot/assets/expedition/creature/storm-eel.glb` and rendered live by `godot/scripts/expedition/creature_view.gd`. Re-copy it there after any re-export.

**v2 direction (user, 2026-11-04):**
- A real fish, not humanised: fish eyes with no lids or whites, and no teeth.
- Low-poly geometry with flat lighting.
- Dark navy skin so it stands out on the turquoise seabed.
- Both the eel and the submarine swim forward (north). The eel turns its head round only occasionally, to strike with lightning.

The v1 concepts in `concept/` (C1 ugly-cute ogre) are rejected history. v2 was modelled directly from the brief, with no new concept image.

- `source/build_model.py`: procedural low-poly model and rig (run in Blender on an empty file).
  - Octagonal flat-shaded body; separate lower jaw.
  - Moray dorsal and anal fins merging into a pointed tail; small pectoral fins.
  - Lateral glow organs.
- `source/build_actions.py`: the clip set. Body poses are per-joint yaw curvatures. A solver keeps one joint fixed so the front can curl back on itself.
- `source/storm-eel.blend`: editable result.
- `export/storm-eel.glb`: runtime candidate (≈417 KB, 17 bones, 1 skin, 10 clips).
- `validation/storm-eel-encounter-preview.mp4`: capture of the three HTML preview flows.

**Axes:** X right, +Y north (the swim direction, away from the ship), Z up, 1 unit = 1 cell. Body ≈ 0.7 × 7 cells, swimming 0.78 cells above the seabed. The world scrolls under the eel, so clips carry no forward root motion, except `escape`.

| Clip | Frames @30 | Loop | Purpose |
|---|---|---|---|
| swim | 60 | ↻ | swimming ahead of the ship |
| restless | 30 | ↻ | warning before the window expires; keeps the silhouette |
| hit | 18 | – | harpoon impact (the preview adds a white flash) |
| hooked | 20 | ↻ | straining forward against the line |
| struggle | 24 | ↻ | side-to-side thrash |
| windup | 30 | – | curls its front round to face the ship (east side); organs charge |
| attack | 18 | – | discharge: jaw gapes and the body locks (0.1–0.42 s) |
| recover | 27 | – | uncurls back into the forward swim |
| escape | 36 | – | bursts north off screen (root motion +9 cells) |
| exhausted | 60 | ↻ | caught: rolled on its side, jaw slack |

**Engine-driven effects:**
- The organ glow (`eel_spot` emission per clip) is not baked; the engine drives it.
- Discharge effects are deferred to #25: a warned vertical strip (amber fill, diagonal hatching, lightning symbol) that does not track the ship and starts only after hooking. #23 keeps aiming attack-free and adds no lightning.
- The preview renders the materials as flat-shaded Lambert with mostly ambient light.

**Open items:**
- Look-match in Godot: done for #23 (flat Lambert, ambient 0.82 plus key 0.5, 135% contrast), compared against the HTML preview.
- A fixed gameplay hit shape.
- A mirrored (west-side) strike, if wanted.
