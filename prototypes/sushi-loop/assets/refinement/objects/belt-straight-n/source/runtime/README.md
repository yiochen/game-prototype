# Native world composition, round09

The native belt geometry, camera, material pixels, source2 frame registration,
24-frame/12fps clip, original four-facing atlases and loop remain exactly round08.
This revision corrects the real game's independent texture-filtering seam.

## Integration

Copy `native_pixel_compositor.gd`, `native_world_layer.gd`,
`native_reduce2.gdshader`, and `native_present.gdshader` into `godot/scripts/`,
and apply `integration.patch` to `restaurant_view.gd`.
`restaurant_view_native.gd` is the exact resulting renderer.
`restaurant_view_baseline.gd` freezes the previous renderer for repeatable probes.
No ArtBook, Session, gameplay, UI/controller, render_plan, object_at, owner records,
registration, ports, sprite atlas pixels or clock function is changed.

The main Control keeps the original screen-space room-item pass for picking.
A noninteractive render-only instance uses the same ArtBook/visible atlas cache
and the same complete world pass, including floors, furniture, guests, dishes,
attachments, editor selection/ghosts, feedback and sale pops in their old order.
Gallery stays on its original direct path; native targets stop updating there.
Only belt source atlases override filtering to nearest in the native pass.
Other source textures keep their existing filter policy at that native scale.

## Coordinate and alpha contract

One native cell is256 pixels. The authoritative current portrait/floor layout is
uniformly mapped into a viewport; the clone's pitch is exactly256, avoiding a
second floating aspect-ratio calculation. Only the visible portrait is allocated,
so landscape letterboxes and offscreen world columns add no render-target area.
All original screen-space roots/hit coordinates stay authoritative.

The common fractional camera/floor grid origin is removed from the native canvas
and restored in the presenter's draw offset. The two translations sum to zero.
This avoids half-texel nearest ties between atlas regions and full textures while
keeping smooth subpixel world motion. Individual objects are never snapped.
A16-native-pixel guard is allocation/filter padding, not geometry overhang or
extra asset artwork. Presentation is clipped to the original portrait rectangle.

ViewportTexture RGB is already premultiplied. The four2x reduction passes and
presentation use `blend_premul_alpha`; none multiplies alpha into RGB a second
time. Each reduction's bilinear centre is the exact2x2 area mean. Presentation
chooses the appropriate reduction from actual screen derivatives and weights
texel intersections in the remaining footprint. An epsilon stabilizes exact2x,
4x and8x boundaries; there is no floating-ceil3-tap equal-average case.

## Cost and evidence

The current seven-column room uses about31.4MB of explicitly allocated RGBA8
color buffers including all four reductions, guards and padding. This estimate
excludes existing atlas textures and driver overhead. There is one visible-world
buffer chain, no per-phase/world-map images, no runtime GPU readbacks, and no
runtime image copies. `ArtBook` and belt wrappers release unused visible atlases.

`bench_round09.gd` is a validation-only actual Godot4.7.2 GL Compatibility/M4
fixture. It consumes the unchanged imported mipmapped atlases, renders all four
facings at all24 times plus closure at128/55/32 cells, and compares the implemented
consumer with actual connected native Blender references. Additional fractional
camera origins are tested at frame0/12/23/closure. Light/gray/dark/transparent
outputs and12fps playback pixels come from Godot. The reference PNG loading and
readbacks exist only in the benchmark, never in the production helpers.

`integration_probe_round09.gd` runs the frozen baseline and candidate full room
renderer with actual Session/ArtBook data. It checks painter sequence, ownership
records,17,190 pick probes, all object anchor transforms, world-overlay state,
portrait, panned landscape, phone32 editor, parent translation/scale and the
unchanged gallery. Final production app/UI tests and captures are coordinated
separately; dedicated consumer fixtures use refined belt pixels, while the full
game fixtures retain the current production catalog until the authorized rollout.

## Shutdown receipts

The exact seven-screen `capture_starter.gd` flow was repeated with private save
identities and fresh imported project copies. An intermittent two-object exit
warning occurred in1/3 native landscape runs and1/3 original-renderer landscape
runs. The coordinator's verbose actual-game capture names
`AudioStreamPlaybackWAV` and `AudioStreamWAV`, each at reference count1.
No compositor object is named. The warning and full logs remain in
`candidates/round-09/teardown/receipts.json`; it has not been suppressed.

Two ownership probes each destroy four normal apps and four freshly initialized
gallery apps. All tracked compositor nodes, fonts, materials, viewport textures
and belt wrappers free; orphan-node counts stay zero. Four script resources
retain the same IDs across every cycle, with no accumulation. These checks found
no demonstrated helper ownership defect. Helper, integration and audio bytes
remain unchanged. `teardown_round09.py` reproduces the captures/probe in temporary
projects; `frozen-pre-teardown/` preserves the exact integrated helper revision.

## Fixed editor-marker pixel dimensions

The subsequent unsealed round09 marker revision passes the native/source factor
into the render clone. Only the fixed2px bracket inset/minimum stroke and1.5px
inset/3px ghost stroke use that factor. Cell-relative lengths stay cell-relative;
the direct renderer/gallery keeps factor1. The viewport core, shaders, native
asset pixels, game state and picking are unchanged.

`marker_probe_round09.py` runs24 actual GPU comparisons against the original
renderer: ground brackets and valid/invalid ghost borders, cell32/55 plus
portrait/landscape layouts, with aligned and fractional camera origins.
`marker_metrics_round09.py` records alpha cross-sections and inspection sheets.
All24 half-coverage core stroke widths equal the original; max inferred centroid
difference is0.382px. Nominal fixed-pixel dimensions agree within1.4e-7px. Direct
vector antialiasing and native area reduction have different edge coverage; no
pixel-identical claim is made. The full coordinate/picking probe was rerun with
zero failures. See `candidates/round-09/markers/revision.json` for exact sources.
The shutdown receipts retain their explicit earlier audited revision and identify
this later marker change; no audio change was made.
