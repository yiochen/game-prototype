# Catalog delivery contract

Use the actual object contract. Native Blender capture resolution and the published sprite resolution can differ. Keep both explicit; never relabel a 4× render as a 2× render.

- `project` names the editable source. `recipeScript` names executable reproduction code; `recipe` may separately name settings.
- `heroes` and `previews` are maps of named aliases to object-relative path strings. Include every preview alias required by the frozen brief.
- `rawFrames` lists the **published registered frames** that occupy atlas cells, with `clip`, `direction`, zero-based `index`, `path`, dimensions and hash. Each must match its atlas rectangle exactly. Preserve larger original native captures separately as `nativeRawFrames` and explicit packet resources.
- `atlases` lists every original clip/facing with path, dimensions, columns, rows and original rectangle layout. Preserve all frame counts, ordering, cadence and loop flags.
- `nativeRecords` points to camera, assetRecord and rig JSON used by production. Published records must use the catalog's published `sourceScale`, logical frame and logical root. Also retain the untouched original native records, actual `nativeCaptureScale`, native resolution, camera matrices, measured calibration and declared whole-canvas publication sampling. Derive published pixel measurements uniformly from the native ones; do not fit the occupied alpha bounds.
- Keep existing nominal functional height and footprint metadata distinct from measured physical bounds. A model within an authorized envelope does not silently change gameplay metadata.
- Include actual measured root matrices for each native facing/frame in validation or a packet-bound capture manifest. Names such as `static-N` must declare their clip and direction clearly.
- Declare the complete portable reproduction closure in `resources`. Save source, all required native/published captures, playback/assembly evidence, validation and exact replay results. Preserve prior sealed rounds and reviews.

For 2D artwork, apply the same published frame/atlas rules and identify the real source/publisher honestly. Do not invent a Blender project. The coordinator seals the candidate and promotes only independently approved bytes.
