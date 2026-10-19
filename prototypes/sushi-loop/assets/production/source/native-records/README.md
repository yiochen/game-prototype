# Current native records — version 12

`index.json` lists the 104 active native objects in the saved project. The 13 flat artwork/effect objects use `../2d/`; eight obsolete garden bundles are removed. Superseded 3D records are in `../native-records-history/retired-v11/`. Registered capture publication is separate from editable model presence and user approval.

## Native model and action index

[index.json](index.json) is the generated provenance snapshot for 104 native issue #33 entries. Its model/action inventory is separate from the published preview status in [the runtime manifest](../../library.json). The other 13 active entries are flat artwork/effects. A native record can exist before its full sprite set is published or approved.

Each `<id>/` folder contains:

- `asset.json`: native frame, anchor, source scale, logical footprint, projection, attachment sockets, clips and declared variants.
- `camera.json`: actual matrices, pixel aspect and calibration. Read any recorded camera exception rather than assuming every object uses the environment projection.
- `rig.json`: native action cohorts, owner identifiers, twelve-fps frame ranges, closing-key convention, bones/controls where applicable, sampled sockets/feet and source hashes.

For recipe, salvage and submarine variants, all assemblies remain children of the same catalog ground root. Use each variant's explicit clip list. The submarine has baseline and upgraded geometry with six states each; the twenty conveyors use 24 samples per running loop at 12 fps. Static assets do not acquire invented motion.

The current normal editable project is [../blender/sushi-loop-world-library.blend](../blender/sushi-loop-world-library.blend). The top-level `editableProject` reference and `sourceBlendSHA256` identify the staged project. All index paths are relative to the parent `source/` directory, including `native-records/<id>/` record paths. Do not interpret an older export snapshot's hash as a newer finalized project's identity.

Version 12 hashes each active `asset.json`, `camera.json` and `rig.json`; it does not contain the old `bakedSourceHashAvailability` field. Per-rig `sourceFiles` preserve hashes from intermediate baking. Some earlier versions are unavailable, while the final frozen project and capture recipes remain retained; see the [independent provenance review](../../../../review/33/full-art-rollout/feedback-coverage.md). Do not replace an unavailable historical hash with a later source version or treat the later file as proof of the earlier file's contents.

For a native clip, assign every action owner in its cohort. These can include mesh visibility, held dishes/utensils, shape keys and shader material nodes in addition to an armature. Shader owners must use the recorded exact material identity; the common embedded node-tree name alone is ambiguous.

Do not edit this index or the generated per-entry records to mark artwork approved. Regenerate them from the corresponding native project and capture pipeline. [The source workflow](../README.md) describes reproducible capture and publication. Final scene-art approval remains with the user, and issue #33 stays open.
