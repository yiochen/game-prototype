# Doodle art revision for ticket #10

The supplied [component catalog](../../../design/art-directions/doodle.png) is the camera, proportion, material and ink reference. Production artwork is newly generated; the catalog is never cropped into game textures. Exact prompts and original output paths are in [visual-revision.json](visual-revision.json).

## Native sources and registration

Fifteen character clips contain six separately drawn poses each: chef preparing north and south, chef holding north, both customers walking in four directions, waiting seated and eating seated. Original atlases are 1448 × 1086 RGBA. Each visible character is at least 445 native pixels tall. Frames are cropped through AtlasTexture regions; source PNG pixels are unchanged.

[build_metadata.py](build_metadata.py) measures opaque bounds and the center of the shoes. Each frame's measured foot point maps to the **center of its occupied square tile**. A common scale reference within each clip prevents size changes from atlas padding or arm movement. Feet registration, frame counts, distinct pixels and loop wrap are checked by the native art suite. Mipmapped linear sampling keeps the high-resolution originals smooth when reduced to phone size.

The floor uses broad ochre paint and sparse hand-drawn grain. Grid cells remain square without perspective distortion. Props and people show their top and front, with height extending above the ground anchor.

## Connected animated conveyor

A single connected four-cell conveyor was generated as [belt_connected_v3.png](../production/belt_connected_v3.png). It has a broad deck, rounded caps, thick coral rails and visible front supports. The opaque surface period comes from the separately generated deck material.

[Godot's native compositor](../../tools/bake_belt_frames.gd) renders six whole-strip phases at native resolution. Only the deck moves; the structure stays fixed. [belt-bake.json](belt-bake.json) records the source crop, surface polygon and period. Each 2008 × 460 strip is then cut into four **equal 502 × 460 regions** through AtlasTexture. Those cuts reconstruct the same whole image in every frame; modules are never independently cropped or height-scaled. The loop's speed is derived from the configured belt travel time and half-cell slat period.

The room draws the complete structural conveyor pass before any dish. Sushi crossing a join therefore remains above both neighboring deck sprites. People and room objects sort by their ground anchor.

To reproduce the frame bake and metadata, from the Godot directory:

```sh
python3 tools/test_native.py --visible --script tools/bake_belt_frames.gd --output assets/production
python3 assets/provenance/build_metadata.py
python3 tools/audit_art.py
```

The two Python art tools require Pillow; the read-only audit also requires NumPy. They are authoring tools, not Android dependencies. Connected source and material PNGs are excluded from export; the six finished strips are shipped.

[Frame registrations, runtime animation and audit results](../../review/10/animation/) accompany the review. Earlier generation records in this directory document the replaced first attempt; their old production filenames are no longer used.
