# Issue 33 native asset source and capture workflow

The active catalog has **117 objects: 104 native Blender objects and 13 flat 2D artwork/effect objects**. The [editable project](blender/sushi-loop-world-library.blend) starts on the revised C125 green-hatted chef Noor in the selected Faceted lighting. It retains 1,992 owned model objects and 1,834 independent native actions. The eight obsolete garden bundles and former 3D dish/bubble/eel-effect entries are absent from this active native project.

**The user approved the Faceted lighting, matte wood and muted-clay conveyor materials and authorized the complete native recapture on 2026-10-19.** Issue #33 can close when the new publication and validation finish. This is native Blender art, with actual ImageGen artwork for sushi and bubbles. It does not claim ImageGen surface refinement of every native mesh. The [runtime manifest](../library.json) records each published sprite batch; the [native index](native-records/index.json) records editable model/action evidence.

## Faceted finish rollout

The selected source finish uses matte Principled surfaces, a centered 140 W
overhead area light (disk size 3.5), and four equal 100 W cardinal fills (disk
size 4). A native material-height ramp keeps lower surfaces dark. The shared
135% sRGB compositor preserves alpha and receives no additional browser grade.
Crate wood uses 42% of its former linear base color, roughness 1, specular IOR level 0,
metallic 0 and emission 0. Conveyor rails use muted clay sRGB `#966B60`, roughness
1 and specular IOR level 0; moving deck UVs and animation timing stay fixed.
Other wood colors, including conveyor legs, retain their original albedo.
Floor materials receive a separate 42% linear albedo calibration to preserve
their palette and visible tile borders under the new diffuse illumination.

All **9,390 native pose/facing frames across 104 objects** have been regenerated
and published from the frozen editable project, SHA-256
`b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6`.
Physical geometry, roots, camera calibration, lower shading,
held-food artwork and action cohorts are retained. The 13 flat ImageGen and
procedural effect entries remain 2D. [Faceted rollout evidence](../../../review/33/faceted-rollout/README.md)
records the source identities, complete capture publication and validation.

Runtime atlases retain 2× complete authored frames. The publisher chooses columns
near six while keeping each dimension at or below 8192 pixels; dock-cover clips
use five columns rather than shrinking their frames. This is a sprite-resource
publication for the review site. Godot resource-import verification is separate
from the later Godot Android game implementation.

## Historical native pass: version 12 — emission finish

The following version-12 hashes and audits describe the earlier emission finish;
the Faceted rollout evidence supersedes them for the current selected lighting.

Frozen editable project SHA-256: `c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`.
All native objects use the approved 135% sRGB compositor and direction-free lower material shading. Environment captures use 70% vertical projection with square ground pitch. C125 characters retain ordinary35, tiny feet, rounded heads and fuller identity-specific hair. Tall concept decorations use the documented upper35/square-footing transition and a three-tile complete-silhouette cap. Floors have explicit cell borders. Blackboard/sign are blank, single-facing front-edge overlays.

Native capture is 4× logical resolution, uniformly sampled to 2× runtime atlases; every animated state retains at least six distinct frames at 12 fps, with 24-frame conveyor travel. No alpha fitting or per-pose resizing is used. Expanded car/tarp frames prevent animation clipping. [Revision review and feedback coverage](../../../review/33/full-art-rollout/README.md) includes the independent geometry/material audit and capture/browser evidence. Source recipes remain in `blender/`; original 2D images, exact prompts and Godot drawing source are in [2d/](2d/README.md).

All **9,390 version-12 native frames across 104 objects** pass the [historical independent pixel audit](../../../review/33/full-art-rollout/independent-pixel-audit.json): fixed dimensions, complete frames, no visible alpha touching object capture edges, and at least six distinct visible frames per animated clip/facing. The 13 flat artwork/effect entries have their separate [2D source and atlas audit](2d/audit.json). New Faceted captures have their own rollout evidence.

## Re-render selected objects after an edit

The project contains actual meshes/rigs/actions and packed held-food textures.
Object/action names are the stable bindings in `native-records/`; keep those names
when adjusting meshes or materials. To render the saved actions without rebuilding
models or touching the project file:

```sh
python prototypes/sushi-loop/assets/production/source/blender/recapture_library.py \
  --ids chef-lena --out /tmp/sushi-art-recapture
```

Add `--clips hold --directions S --frames 0` for one diagnostic frame, or
`--dry-run` to inspect the plan. Original four-times-resolution PNG frames and
receipts are written under the selected output directory; complete two-times
runtime atlases are committed in `../sprites/`. Ground pitch, capture canvas and
root are taken from the native record, never from a fitted silhouette.

## Historical version 11 (superseded)

The following sections retain earlier modeling/capture history. Their old counts, camera, source hashes and garden bundles do not describe the active version 12 project.

### Version 11 inventory

The isolated normal project contains **4,455 owned objects and 5,776 independent native actions**. Its frozen project SHA-256 is `732a5a4cc73c908f69ccc832e8dc1e66a63c81307157427d9b73e0efdc2acbcd`. This source revision adds eight dense, reusable scenery assemblies; it does not add eight new gameplay systems.

| Native cluster pair | Footprint per assembly | Components per assembly |
| --- | --- | --- |
| `restaurant-border-garden-a/b` | 2 × 4 cells | 22 |
| `restaurant-corner-garden-a/b` | 3 × 3 cells | 24 |
| `underwater-reef-garden-a/b` | 2 × 4 cells | 24 |
| `underwater-coral-garden-a/b` | 3 × 3 cells | 26 |

Each assembly has independently editable native components at irregular fractional positions, with varied native scales and orientations. Foliage, coral and lantern motion use staggered phases in a **12-frame, 12 fps ambient loop**, plus an explicit **one-frame static** state. The source helper `blender/catalog_clusters.py` retains the layouts, component roles, meshes and composition recipes. Per-component grounding uses one fixed offset measured from the evaluated source mesh base, placing it on the 0.035-high island. No animation frame or facing is fitted to its silhouette.

The same helper rebuilds `entry-finished` as a **four-tile-wide modeled entrance** with a **two-tile clear center**, wider native columns/lintel, additional roof bars and four side curtain panels. Its logical ground footprint is 4 × 1, the ground root stays centered, and the original clip IDs remain. The modeled roof retains an explicit **0.12-cell depth-overhang allowance** beyond the ground footprint; this does not enlarge the ground support mask or stretch the sprite. Declared height is 2.30 to cover the native roof ridge.

Native geometry checks passed for all eight clusters and the wider entrance over **388 facing/frame samples**. All nine new capture sets are complete and published. The full **125-entry preflight passes 11,872 frames**, with no failed or pending IDs; source audit passes all 125 objects with zero errors. Focused browser review covers all eight new object pages, both scenes and the corrected entrance clearance; the five scene regressions pass. [Dense-cluster evidence](../../../review/33/decoration-clusters/README.md) retains the final results and the earlier grounding/occlusion findings. Captures retain **4× source resolution**, with whole authored frames uniformly sampled to **2× runtime atlases**.

## What is retained

| Location | Role |
| --- | --- |
| [blender/sushi-loop-world-library.blend](blender/sushi-loop-world-library.blend) | Current normal editable project, isolated from the unrelated scene originally open on the user's computer. |
| `blender/*.py` | Native modeling, composition, rig, action, capture and publication recipes. Models were authored through Blender MCP; background workers capture the saved native actions. |
| [native-records/](native-records/README.md) | Per-entry `asset.json`, `camera.json` and `rig.json`, including model bounds, roots, clips, action owners, timing, controls and source hashes. |
| `records/<id>/` | Metadata used for the published sprite captures. This may advance separately from the native model index. |
| `registered/<id>/<clip>-<direction>/` | Whole-frame packing guides and capture hashes in Git; full 4× source PNGs and intermediate sheets are locally retained and ignored. |
| `validation/` | Historical representative native captures retained in Git; not the complete current 4× batch. |
| [../sprites/](../sprites/) | Runtime atlases uniformly sampled from complete authored frames at 2× logical resolution. |
| `blender/revisions/`, `blender/history/`, `records-history/`, `registered-history/` | Earlier source/capture attempts retained when a publication changes. Consult the recorded hashes rather than assuming an old revision is current. |

Original 4× PNGs and redundant intermediate sheets are kept locally with their registered capture folders and omitted from Git to avoid duplicating render intermediates. The new complete raw batch is also local at `/private/tmp/sushi33-faceted-rollout-v2/export/raw-frames`. Git retains every complete 2× runtime atlas, editable Blender projects, current recipes/records, per-frame hashes, packing guides and audits; it does not contain all 9,390 individual 4× PNGs. The current native index hashes the active model/camera/rig records. Per-rig `sourceFiles` also retain hashes sampled during intermediate baking; they do not assert that every intermediate script version was retained. The final frozen project and capture recipes are retained and verified. Nine earlier script versions referenced by intermediate bake records have not been located; see the [independent provenance review](../../../review/33/full-art-rollout/feedback-coverage.md). Keep those original hashes rather than substituting a later version.

## Registration and timing

One logical cell is 128 pixels. Blender axes are `x = X`, `depth = -Y`, `height = Z`. Environment capture uses the approved 70% vertical coefficient: `screenY = rootY + 128*(-Y - 0.70*Z)`. Its native orthographic camera elevation is `atan(1/0.70)`, approximately 55.008°, with pixel aspect X `sqrt(1 + 0.70²)` and Y 1. Actual matrices and calibration vectors are recorded. At 4× capture, one environment unit spans 512 source pixels along X/depth and 358.4 pixels vertically. Finished PNGs are never squeezed to create this projection.

People and creatures use the declared ordinary orthographic art camera, normally at 35° elevation. The submarine uses a recorded 65° overhead exception. Tall concept decorations use the documented 35° upper view with square footing below Z=.42; this hybrid is explicitly distinct from a pure ordinary camera. These assets share the same logical cell pitch and projected ground root. Sushi is ImageGen 2D artwork; held dishes use the same image on a camera-facing plane attached to evaluated palms. Seat, palm, deck and equipment attachments remain separate from sprite bounds. Do not apply a seated support elevation twice.

Every animated clip runs at **12 fps**. Most native states use 12 samples; the twenty directed conveyor modules use **24 unique frames over two seconds**, with fixed rails and moving deck material. This avoids the reversed-motion aliasing of seven slat periods sampled in twelve frames. The separate plate is a staged review animation along the deck centerline, including the native quarter-circle turns. Its travel clock is independent of the moving slat material and resets at the start cap; it is not a gameplay transport simulation. Duplicate closing keys belong to native interpolation only and are excluded from runtime sprite frames. Static states remain explicitly static.

The submarine stays one catalog entry: baseline and upgraded geometry each expose the same six states, for twelve clips in total. Their ground root, footprint and camera frame remain fixed. Recipe, salvage and equipment variants belong to their parent entries rather than adding new catalog objects. Inspect the current per-entry variant/clip records for exact coverage.

Reaction/ambient bubbles and all sushi dishes use ImageGen 2D artwork, shared across four world-facing review contexts. Reward coins retain their native visual pivot that counter-rotates the world ground root around Z. Physical characters, furniture, belts and terrain keep their declared directional views; the blank sign and chef blackboard expose only their player-facing surface.

Each object has one complete authored capture frame for every pose and facing. Larger action bounds use a declared larger frame, never per-pose fitting. Current clearance contracts include eel 448×512/root (224,352), boost trail 448×544/root (224,352), and reef fragments 320×448/root (160,320). Camera records remain the authoritative values for any later revision.

Corner supports now use the same height and materials as the straight conveyor, with a quarter-annular lower frame and four legs fully beneath the curved deck. Reversed corners use incoming-to-outgoing UVs and the same negative slat phase as the straight modules, preserving phase at their joins. The native `catalog_corner_supports.py` and `catalog_belt_flow.py` helpers retain these changes for later iteration.

Section 03 includes authored connections for all 42 modules with native ports, tiled patches for the four floor styles, and the four dock assembly views. Belts meet directed straight neighbors; wall, terrain and rope pieces meet neighbors with matching native edge profiles. Overlays expose port alignment. Use `publish_captures.py --repo <repo> --interactions-only` to rebuild these fixtures from the retained native records without repacking sprites.

Customer walk and panic cycles use a backward-moving grounded stance and a forward lifted recovery relative to local front `-Y`. The sprites remain in place at their authored ground root. Revised C125 short legs travel **0.225 world cells per gait cycle**: walk uses one gait cycle in its 12-frame loop (0.225 cells/second), while panic uses two (0.45 cells/second). The earlier 0.56-cell long-leg gait remains historical only. The native character audit checks evaluated foot bones, contact and anatomy across all clips/facings.

The native baker temporarily exposes only the target collection and armature while sampling, restoring their presentation state afterward. This keeps evaluated hand attachments current even when other catalog objects are hidden. Constant posed object transforms are keyed when they differ from the saved baseline; the world ground root keeps its external facing control. Native held-food checks compare the actual evaluated palm meshes with the food-root position across all 12 characters and four directions.

## Reproduce a native capture

Use a separate working folder so an iteration cannot overwrite the checked-in source project. From the repository root:

```sh
ART_SOURCE="$PWD/prototypes/sushi-loop/assets/production/source"
ART_WORK=/private/tmp/sushi33-art-review
mkdir -p "$ART_WORK/export/source"
cp "$ART_SOURCE/blender/"*.py "$ART_WORK/"
cp "$ART_SOURCE/blender/sushi-loop-world-library.blend" "$ART_WORK/export/source/"
cp -R "$ART_SOURCE/native-records/." "$ART_WORK/export/source/"
```

Stop any MCP capture targeting the same output folder before starting background workers. This diagnostic renders one native frame without rebuilding the model:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background "$ART_WORK/export/source/sushi-loop-world-library.blend" \
  --python "$ART_WORK/capture_worker.py" -- \
  --export-root "$ART_WORK/export" \
  --ids chef-lena --clips hold --directions S --frames 3 \
  --worker chef-proof --mcp-idle-confirmed \
  --output "$ART_WORK/raw-proof"
```

`--frames` is zero-based, so this selects native timeline frame 4. Omit `--clips`, `--directions` and `--frames` to capture every authored state in N/E/S/W. Workers load the saved native actions through `native_actions.apply_clip`; they do not rerig, infer a camera from alpha, or transform the rendered bitmap. They use the same EEVEE lighting, color settings and 4× camera calibration as the MCP capture runtime. Whole asset IDs are exclusively reserved, and completed files are reused only when their receipts match the native project, metadata, helper version, dimensions and PNG checksum. Partition whole IDs between concurrent workers.

For a mesh or rig change, edit the native model through Blender MCP and retain the changed modeling source. Rebuild that entry with `production_library.build`, bake its independent clips with `native_actions.bake_asset`, and save the isolated production library. `finalize_project.py` converts that isolated library into a normal main project in a separate background process, using a new output filename. Freeze worker inputs before replacing the canonical project. Never run a live-session `save_as_mainfile` over the user's unrelated Blender project.

A clip can involve several native action owners: an armature, plate root, knife visibility, shape-key geometry or material node tree. Use the complete action cohort from its `rig.json`, not only the armature action. Belt shader records identify the exact owning material because embedded node trees can share the same display name.

## Publish and review

Publication requires a complete state/facing set. The one-frame diagnostic above is intentionally insufficient. Once complete captures and their matching source metadata are staged, use `publish_captures.py --repo <repo> --native <iteration-export> --ids <stable-id>`. `--raw-root <folder>` selects a separate completed capture batch, such as the 24-frame belt batch, without overwriting earlier raw attempts. The publisher retains previous packs and sources, checks exact frame counts, and uniformly samples full authored frames. Use a Python environment with Pillow and the registered-sheet helpers from the installed character/tile skills.

Review `/prototypes/sushi-loop/#object-library`; each stable `#object-<id>` page contains its declared facings, a repeated/joined 3×3 grid, related-object scale fixtures and all published states. Blank signs and chef blackboards expose one player-facing surface; flat artwork retains its authored world-facing contexts. Pause, scrub and overlays expose registration and timing. The concept sheet remains at `#art-catalog`. Comments are review feedback, not final approval or game saves.

The complete composition pages are `#scene-restaurant` and `#scene-underwater`. The restaurant uses a seven-column portrait layout with a tall, connected conveyor and the four-tile entrance at the back. The underwater page uses a seven-column channel with continuous cliff banks. Individual full-cell plants, rocks, coral, kelp and props layer over independent bordered ground tiles; eight obsolete large garden bundles are absent from the active library. These placements retain the registered belt/terrain joins, seated supports and staged travel lanes. Playback, scrubbing and fit/detail zoom inspect the same catalog sprites; no separate flattened background or per-object bitmap transform is introduced.

Structural audits, native-versus-capture parity and browser checks support art review; they do not independently establish visual approval. The user approved the chosen finish and authorized the complete native recapture and issue closure once publication and validation finish. The review site introduces no restaurant/expedition simulation; Godot Android remains the game implementation target.
