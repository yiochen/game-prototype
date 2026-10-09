# V2 painted production sprites

These raster assets were generated with the built-in image generation tool, following the accepted doodle study at `prototypes/sushi-loop/design/art-directions/01-doodle.png`. They supersede the corresponding early SVG prototypes when selected by the runtime. No game title or interface wording is painted into them.

## Sources and refinements

- `characters-atlas.png`: original six-character generation, 1536 × 1024 RGBA. Chef, alternate chef, three seated guests without chairs, and one standing green-cap guest.
- `customer-poses-atlas.png`: 1536 × 1024 RGBA, three standing/walking guests above the same three sitting upright with dangling lower legs. Replaces the initial floor-sitting customer poses while preserving those old images in `characters-atlas.png`. Chair and floor are omitted. Exact edit prompt: `customer-poses-prompt.json`.
- `props-atlas.png`: nine props, 1254 × 1254 RGBA. The original generation was refined using the accepted doodle image as a direct visual style reference: squat rounded submarine, stronger ink contours, broad gouache colors and quieter grain. The earlier render remains `props-atlas-initial.png` for provenance.
- `creatures-atlas.png`: three creatures, kelp, coral and portal, 1536 × 1024 RGBA. Also refined against the actual accepted image to replace dense etched detail with broad handpainted shapes. The earlier render remains `creatures-atlas-initial.png`.
- `ui-props-atlas.png`: root-generated rubble, blackboard and blank cream/coral panels, 1254 × 1254 RGBA. Its source image is `/Users/yiouchen/.codex/generated_images/01a11f39-1cbb-7003-9093-5574705cc8bd/exec-8b520d64-df21-41f5-b7d9-f4d7efeb2b2e.png`.

The exact initial prompts are in `sprite-prompts.json`; exact edit prompts and their target/reference roles are in `sprite-refinement-prompts.json`. Environment and title images in this directory were generated separately by the other implementation agents.

## Extraction and verification

`slice_atlases.py` performs only mechanical crops and transparent canvas padding. It neither repaints images nor changes source color or alpha values. The atlases have genuine alpha transparency, verified by their RGBA bands and zero-alpha pixels. A few generated subjects crossed the requested nominal grid boundaries, so extraction uses measured clear gutters instead of clipping their hats, tails or propellers. `atlas-metadata.json` records exact source rectangles, crop bounds, original canvas sizes and final dimensions.

Each standalone sprite has a 16-pixel transparent outer margin and preserves its native aspect ratio. Use aspect-preserving fitting when rendering; creature PNGs are naturally wider than character PNGs. Alpha is retained through every crop. No checkerboard or solid background was removed with image processing.

Production exports: `chef`, `chef_2`, `customer_1`–`customer_4`, `customer_walk_1`–`customer_walk_3`, `submarine`, `gear`, `rock`, `seat`, `plant`, `salmon`, `cucumber`, `shrimp`, `eel`, `creature_salmon`, `creature_shrimp`, `creature_eel`, `kelp`, `coral`, `portal`, `rubble_cluster`, `blackboard`, `paper_panel`, `coral_panel` (all `.png`).

Re-run extraction with a Python environment that provides Pillow. On this workspace the bundled runtime is `/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.

## Launcher icon

`icon.png` is a separate opaque square icon painting generated from the finished submarine and accepted style reference. A targeted composition edit increased the cream-paper inset so the subject and small teal/coral accents fit safely inside a circular Android mask. Exact prompts, source paths and reference roles are recorded in `icon-prompt.json`. Its identical copy at `../icon.png` is the existing Android launcher export input; Godot scales the full-size source. The former SVG-derived PNG is preserved as `../icon-prototype.png`. No game name or text is baked into the icon.
