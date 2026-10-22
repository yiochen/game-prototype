Corner N→E native round01 reproduction

No target bitmap is used in any native material. The editable source is round-01.blend.
resources/original-library.blend is the untouched original source (SHA b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6).
resources/approved-family.blend is the exact approved family native source. All procedural materials, actions and native geometry are in the source.

From any copied object directory, with Blender5.2.2 and Python3+Pillow+NumPy:
  blender -b -t 4 --python source/build-round01.py
  blender -b -t 4 --python source/capture-round01.py
  python3 source/package-round01.py
  python3 source/replay-source.py /path/to/blender

The fresh source-only replay receives only build/capture scripts and resources, no candidate .blend or PNGs. All400 decoded RGBA images reproduce exactly. Blender embeds File/Date/timing provenance text, so file byte hashes differ between directories/runs; exact expected/replay pixel hashes and metadata differences are retained in portable-replay.json. Published PNGs/atlases remain the exact reviewed bytes, never stripped or repaired.

The native capture scale and published scale are both2. Frames are384x704, logical192x352, logical root96,248,128logical px/cell. Nominal functional height.695 remains separate from measured bounds. No per-view fitting/recoloring or end overhang/caps are used. Original deck vertices/angularUV/native phase action are preserved exactly. Native rail sections use the approved family cross-section shader in a native attribute basis.

capture-round01.py includes independently native-rendered connected and welded unbroken assemblies, both ports, all4facings×25 samples. Assembly-source.blend is the canonical reference scene, retained beside validation. It is not the asset source. All24 unique frame order/cadence/loop flags remain original. Frame25closure is separate evidence only.

Repository browser verification uses the actual current SpriteScene imported by consumer-bench.jsx, current worldRasterPlan/paintWorldRaster and source layout functions. Run consumer-check.mjs from repository root with Vite4178. Interception substitutes candidate atlas bytes at the exact production image requests while catalog mutations remain in memory. No production file is changed. Native/independent/connected consumer captures, playback/pause/scrub receipts and repeated/staged-plate desktop960/phone320 screenshots are retained. One initial screenshot transient is retained under consumer/transient-capture with isolated stable retry screenshots and native canvas readbacks in retry.json.

The representative Godot GPU harness uses exact current production compositor/reducer/presenter bytes in source/godot-probe/runtime (hash receipts included), no gameplay implementation. From its directory run Godot --editor --headless --import, then Godot --windowed --audio-driver Dummy --resolution64x64 --script res://bench.gd. It resolves native inputs/output relative to the copied object. The harness uses native atlas regions at nearest sampling, shared fractional origins, native reduction and area presentation at128/55/32cells on transparent/light/dark backgrounds. consumer-metrics.py computes fullRGB+alpha and localized join residuals for both actual consumers.

previews/motion-inspection.html is a standalone convenience view of native frames, not a replacement for actual SpriteScene/Godot evidence.
