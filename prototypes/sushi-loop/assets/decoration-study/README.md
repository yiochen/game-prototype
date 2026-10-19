# Compact organic decoration review

Issue 33 shape/material study revised from browser feedback: eliminate the continuous blank band in front of low-camera rock bases; break up carved-looking pillars; replace straw-like coral; remove directional capture lighting; keep vertical rise strictly below three tiles.

Five full-footprint families now have offset shoulders, bulges and changing widths along their height. Broad crowns have shallow unevenness. Compact plants sit on bottom, middle and upper ledges. Coral combines squat swollen sponges with thick flared scalloped mouths and asymmetric branching forms. Ordinary-35 maximum vertical rises are approximately 1.03, 1.67, 2.26, 2.81 and 1.90 tiles for low rock, coral reef, kelp, crag and ruin respectively. The 70% camera gives smaller rises. All source models remain within one physical X/Y cell with 92% top-down coverage.

## Direction-free surface shading

The saved scene has zero LIGHT objects and zero world illumination. All 45 materials use emission surfaces, so no directional Blender lighting or cast shadow enters the sprites. Rock colors use world height and absolute normal Z to graduate from dark bases to bright tops; those quantities are invariant under cardinal Z rotations. Small facet color variation is deliberately subtle. Coral and kelp use symmetric camera-facing form tone to reveal their volume, without a world light direction. Future Godot ground-contact shadows stay separate.

## Upper view and square footing

The floor always uses the established 70% square-grid oblique camera. Both object profiles keep 128-pixel X pitch, 192×768 logical frames, root (96,688), 4× source scale and native 768×3072 transparent PNGs.

- `oblique70`: screen Y = 128 (-Y - 0.70 Z).
- `ordinary35`: 35° ordinary orthographic camera for upper geometry, plus an explicit native capture-space footing correction below Z=0.42. Before rendering, capture-only mesh coordinates use `Ycapture = Y * (1 + (1/sin(35°)-1) * max(0,1-max(0,Z)/0.42)^2)`. This gives square projected ground contact at Z=0 and smoothly returns to the ordinary upper view. Source logical geometry and gameplay footprint remain unchanged.

This is a hybrid capture projection, not a pure ordinary camera over the whole model. The recipe applies it before capture, restores source vertices afterward and saves the actual evaluated capture geometry under `capture-geometry/`. No bitmap stretch, fitting, masking or silhouette shift is used. Receipts retain both physical bounds and capture-geometry hashes. All facings reach the front and back tile boundaries; natural silhouette notches remain, but the previous continuous blank strip is removed.

The page compares All 70% with Mixed, selecting the low upper view for assets whose reference S silhouette exceeds two tiles. This rule and projection exception remain experimental for isolated decor. Connected terrain and production architecture retain their existing contract.

`decoration-study.blend` is the isolated editable source authored through Blender MCP. `source/create_and_capture.py` recreates it with `create(NEW_DIR)` and captures its saved library with Blender CLI `--python source/create_and_capture.py -- --capture OUTPUT_DIR`. There are 41 captures: five objects × four facings × two profiles, plus one floor. Project/source/image/capture-geometry hashes are bound by the manifest and receipts.

Run `python source/audit.py PATH_TO_THIS_FOLDER REPORT_JSON` with Pillow. Native checks cover height limits, one-cell physical bounds, coverage, irregular shoulder/crown geometry, three growth bands, calibrated camera axes, actual projected footing limits, rendered front-row alpha, complete frame sizes and alpha margins. Independent native material inspection is saved with the review evidence. Historical original/moderate studies and earlier commits preserve prior art. This is a static experiment awaiting approval; production rollout, animations, runtime collision/shadows and issue 33 closure remain pending.
