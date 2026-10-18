# Issue 33 native asset source and capture workflow

The approved concept has become an editable native Blender library covering **117 catalog entries across 17 families**. The [project](blender/sushi-loop-world-library.blend) contains the actual meshes, materials, character/creature rigs, independent action cohorts and cosmetic assemblies. It opens as a normal Blender project. The initial camera view shows Rosa’s corrected walk facing east; enable another asset collection in the Outliner to inspect it.

**Finished scene-art approval is pending. Issue #33 remains open.** This delivery is labeled a native Blender review pass. It does not claim a completed imagegen surface-refinement pass. Captures are published in complete batches; [the runtime manifest](../library.json) is the authority for each page's published status, while [the native index](native-records/index.json) inventories editable model/action evidence. A model in that index does not, by itself, establish complete or approved sprite coverage.

## What is retained

| Location | Role |
| --- | --- |
| [blender/sushi-loop-world-library.blend](blender/sushi-loop-world-library.blend) | Current normal editable project, isolated from the unrelated scene originally open on the user's computer. |
| `blender/*.py` | Native modeling, composition, rig, action, capture and publication recipes. Models were authored through Blender MCP; background workers capture the saved native actions. |
| [native-records/](native-records/README.md) | Per-entry `asset.json`, `camera.json` and `rig.json`, including model bounds, roots, clips, action owners, timing, controls and source hashes. |
| `records/<id>/` | Metadata used for the published sprite captures. This may advance separately from the native model index. |
| `registered/<id>/<clip>-<direction>/` | Whole-frame packing guides and hashes of unchanged source captures. |
| `validation/` | Representative unchanged native captures retained in Git. |
| [../sprites/](../sprites/) | Runtime atlases uniformly sampled from complete authored frames at 2× logical resolution. |
| `blender/revisions/`, `blender/history/`, `records-history/`, `registered-history/` | Earlier source/capture attempts retained when a publication changes. Consult the recorded hashes rather than assuming an old revision is current. |

Original 4× PNGs and redundant intermediate sheets are kept locally with their registered capture folders and omitted from Git to avoid duplicating render intermediates. The native index reports whether a historical source hash was located; an unavailable historical source version must remain explicitly marked unavailable, not replaced by another version or treated as a passing result.

## Registration and timing

One logical cell is 128 pixels. Blender axes are `x = X`, `depth = -Y`, `height = Z`. Environment capture uses the square top/front oblique projection: 45° orthographic with √2 vertical projection stretch before rendering. The actual camera matrices and calibration vectors are recorded. At 4× capture, one environment unit spans 512 source pixels along X, depth and height. Finished PNGs are never stretched to create this projection.

People, rounded dishes and creatures use the declared ordinary orthographic art camera, normally at 35° elevation. The submarine uses a recorded 65° overhead exception. These assets share the same logical cell pitch and projected ground root; their physical floor depth is foreshortened. Seat, palm, deck and equipment attachments remain separate from sprite bounds. Do not apply a seated support elevation twice.

Every animated clip runs at **12 fps**. Most native states use 12 samples; the twenty directed conveyor modules use **24 unique frames over two seconds**, with fixed rails and moving deck material. This avoids the reversed-motion aliasing of seven slat periods sampled in twelve frames. The separate plate is a staged review animation along the deck centerline, including the native quarter-circle turns. Its travel clock is independent of the moving slat material and resets at the start cap; it is not a gameplay transport simulation. Duplicate closing keys belong to native interpolation only and are excluded from runtime sprite frames. Static states remain explicitly static.

The submarine stays one catalog entry: baseline and upgraded geometry each expose the same six states, for twelve clips in total. Their ground root, footprint and camera frame remain fixed. Recipe, salvage and equipment variants belong to their parent entries rather than adding new catalog objects. Inspect the current per-entry variant/clip records for exact coverage.

Reaction bubbles and reward coins use a native visual pivot that counter-rotates the world ground root around Z. These effects face the fixed art camera in all four world-facing contexts; the source retains the actual driver. Physical characters, furniture, food, belts and terrain keep separate directional views.

Each object has one complete authored capture frame for every pose and facing. Larger action bounds use a declared larger frame, never per-pose fitting. Current clearance contracts include eel 448×512/root (224,352), boost trail 448×544/root (224,352), and reef fragments 320×448/root (160,320). Camera records remain the authoritative values for any later revision.

Corner supports now use the same height and materials as the straight conveyor, with a quarter-annular lower frame and four legs fully beneath the curved deck. Reversed corners use incoming-to-outgoing UVs and the same negative slat phase as the straight modules, preserving phase at their joins. The native `catalog_corner_supports.py` and `catalog_belt_flow.py` helpers retain these changes for later iteration.

Section 03 includes authored connections for all 42 modules with native ports, tiled patches for the four floor styles, and the four dock assembly views. Belts meet directed straight neighbors; wall, terrain and rope pieces meet neighbors with matching native edge profiles. Overlays expose port alignment. Use `publish_captures.py --repo <repo> --interactions-only` to rebuild these fixtures from the retained native records without repacking sprites.

Customer walk and panic cycles use a backward-moving grounded stance and a forward lifted recovery relative to local front `-Y`. The sprites remain in place at their authored ground root. A forward-moving game character travels **0.56 world cells per gait cycle** to keep its support foot planted: walk uses one gait cycle in its 12-frame loop (0.56 cells/second), while panic uses two (1.12 cells/second). The native gait audit checks evaluated foot bones, deformed sole contact, toe direction and cycle closure in all four facings; it also retains the failing moonwalk baseline.

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
  --ids chef-lena --clips hold --directions S --frames 5 \
  --worker lena-proof --mcp-idle-confirmed \
  --output "$ART_WORK/raw-proof"
```

`--frames` is zero-based, so this selects native timeline frame 6. Omit `--clips`, `--directions` and `--frames` to capture every authored state in N/E/S/W. Workers load the saved native actions through `native_actions.apply_clip`; they do not rerig, infer a camera from alpha, or transform the rendered bitmap. They use the same EEVEE lighting, color settings and 4× camera calibration as the MCP capture runtime. Whole asset IDs are exclusively reserved, and completed files are reused only when their receipts match the native project, metadata, helper version, dimensions and PNG checksum. Partition whole IDs between concurrent workers.

For a mesh or rig change, edit the native model through Blender MCP and retain the changed modeling source. Rebuild that entry with `production_library.build`, bake its independent clips with `native_actions.bake_asset`, and save the isolated production library. `finalize_project.py` converts that isolated library into a normal main project in a separate background process, using a new output filename. Freeze worker inputs before replacing the canonical project. Never run a live-session `save_as_mainfile` over the user's unrelated Blender project.

A clip can involve several native action owners: an armature, plate root, knife visibility, shape-key geometry or material node tree. Use the complete action cohort from its `rig.json`, not only the armature action. Belt shader records identify the exact owning material because embedded node trees can share the same display name.

## Publish and review

Publication requires a complete state/facing set. The one-frame diagnostic above is intentionally insufficient. Once complete captures and their matching source metadata are staged, use `publish_captures.py --repo <repo> --native <iteration-export> --ids <stable-id>`. `--raw-root <folder>` selects a separate completed capture batch, such as the 24-frame belt batch, without overwriting earlier raw attempts. The publisher retains previous packs and sources, checks exact frame counts, and uniformly samples full authored frames. Use a Python environment with Pillow and the registered-sheet helpers from the installed character/tile skills.

Review `/prototypes/sushi-loop/#object-library`; each stable `#object-<id>` page contains four facings, a repeated/joined 3×3 grid, related-object scale fixtures and all published directional states. Pause, scrub and overlays expose registration and timing. The concept sheet remains at `#art-catalog`. Comments are review feedback, not final approval or game saves.

Structural audits, native-versus-capture parity and browser checks support review, but do not establish natural deformation, convincing joins, correct layering or final art approval. The user must approve the actual finished scene assets before #33 can close. The review site introduces no restaurant/expedition simulation; Godot Android remains the game implementation target.
