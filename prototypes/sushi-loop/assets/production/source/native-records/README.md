# Native model and action index

[index.json](index.json) is a generated provenance snapshot for the 117 stable issue #33 entries. Its model/action inventory is separate from the published preview status in [the runtime manifest](../../library.json). A native record can exist before its full sprite set is published or approved.

Each `<id>/` folder contains:

- `asset.json`: native frame, anchor, source scale, logical footprint, projection, attachment sockets, clips and declared variants.
- `camera.json`: actual matrices, pixel aspect and calibration. Read any recorded camera exception rather than assuming every object uses the environment projection.
- `rig.json`: native action cohorts, owner identifiers, twelve-fps frame ranges, closing-key convention, bones/controls where applicable, sampled sockets/feet and source hashes.

For recipe, salvage and submarine variants, all assemblies remain children of the same catalog ground root. Use each variant's explicit clip list. The submarine has baseline and upgraded geometry with six states each; the twenty conveyors use 24 samples per running loop at 12 fps. Static assets do not acquire invented motion.

The current normal editable project is [../blender/sushi-loop-world-library.blend](../blender/sushi-loop-world-library.blend). The top-level `project` reference and its recorded hash identify the staged project. Per-record paths are resolved from the index folder; source references under `blender/` in historical availability entries are relative to the parent `source/` directory. Do not interpret an older export snapshot's hash as a newer finalized project's identity.

`bakedSourceHashAvailability` distinguishes retained source versions from hashes whose original source file has not been located. Preserve that distinction. Current authoring scripts and later working fixes do not retroactively prove the availability or quality of every historical version. Earlier attempts and grades remain evidence, even when a later capture replaces them on the live page.

For a native clip, assign every action owner in its cohort. These can include mesh visibility, held dishes/utensils, shape keys and shader material nodes in addition to an armature. Shader owners must use the recorded exact material identity; the common embedded node-tree name alone is ambiguous.

Do not edit this index or the generated per-entry records to mark artwork approved. Regenerate them from the corresponding native project and capture pipeline. [The source workflow](../README.md) describes reproducible capture and publication. Final scene-art approval remains with the user, and issue #33 stays open.
