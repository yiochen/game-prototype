# Round11 fixed world feedback strokes

This revision fixes three expressions in the whole-world renderer: the holding
clock ring and hand use `1.4 * _native_screen_pixel_scale`; the preference timer
uses `maxf(1.4 * _native_screen_pixel_scale, pitch * 0.032)`. The existing native
factor already maps source Control pixels into native pixels. Its default1 keeps
the direct/gallery renderer unchanged.

| Source cell | Clock baseline / corrected | Old clock | Timer baseline / corrected | Old timer |
|---|---:|---:|---:|---:|
|128|1.4|0.7|4.096|4.096|
|55|1.4|0.30078125|1.76|1.76|
|32|1.4|0.175|1.4|1.024|

Radius, center, hand length, colors, arc samples, timer progress, source anchors,
world painter order, picking and state are unchanged. The four compositor helper
and shader files are exact sealed round10 bytes. The native project remains the
exact reviewed `source/round-09.blend`; no model, material, camera, phase, frame,
atlas or exported asset pixel is changed. All sealed source/runtime and round09/
round10 files stay read-only.

`round10-to-round11.patch` is the complete three-line incremental change.
`integration.patch` is the original direct renderer to round11 patch. The
coordinator copies only `restaurant_view_native.gd` into the actual game's
`restaurant_view.gd`; no other installed helper needs changing.

`fixed-pixel-audit.json` accounts for every drawing call. Editor markers already
scale fixed pixel sizes. Caption font arguments and paper-style dimensions are
gallery-only/direct. Socket and bubble offsets and symbol radii use pitch, and
arc sample counts/progress thresholds are dimensionless.

`run_probes_round11.py` creates a disposable game resource project. It runs96
actual GL/M4 GPU cases:128/55/32 cells, portrait/landscape, aligned/fractional
cameras, clock plus timer progress0/.001/.1/.25/.5/.75/1. Three paths use the actual
original, sealed round10 and corrected renderer functions; only sprites are
suppressed so strokes can be inspected. Raw transparent readbacks are retained.
Landscape controls use fractional heights to keep exact requested cell sizes;
full-app integer-window checks belong to the coordinator. A full renderer probe
also preserves17,190 picking results, source anchors and gallery pixels.

`inspect_feedback_round11.py` derives measured RGBA/ink-coverage proxies and
inspection sheets. ViewportTexture RGB is premultiplied: display crops composite
it correctly over sand. These labelled display crops are not asset pixels or
substitutes for actual opaque production screenshots. Direct vector AA and
native area reduction differ, so no pixel-identical antialiasing claim is made.
The 56 timer captures at55/128 are nevertheless byte-identical to round10 because
the relative width already governs there.

A supplemental opaque-background bench import was canceled at the coordinator's
request before rendering, to avoid overlapping its actual-game import series.
Its log is retained; only the completed transparent GPU bench is claimed.
No audio changes were made. The known intermittent WAV/playback shutdown warning
and its original-renderer reproduction remain in the immutable earlier receipts.

`assemble_round11.py` preserves all round10 delivery resources, all native raw
frames/atlases/previews and the full09/10 receipts, then adds round11 source and
proof. It does not seal a packet or self-approve. The coordinator adds exact-game
code/test/capture receipts before final sealing and independent judging.
