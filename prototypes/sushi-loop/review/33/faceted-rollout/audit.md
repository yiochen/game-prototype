# Independent Faceted rollout verification

The user approved Faceted lighting, the matte crate wood and muted clay conveyor
rails, and requested the production sprite recapture and issue #33 completion.
This independent audit reads saved Blender files and captures. It does not use
or save the live Blender session, modify source projects, fit sprites, or grade
images after capture.

## Frozen baseline

The prior production source is SHA256
`c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`.
`audit-native-baseline.json` freezes 104 native entries, 525 materials, 1,834
independent action curves and 2,256 representative evaluated pose/facing states.
It includes mesh topology and positions, shape-key coordinates, UVs, polygon
material indices, parent relationships, armature bones, spatial metadata and
registered camera calibration. Thirteen flat artwork/effect entries have
independent original atlas hashes in `audit-flat-baseline.json`.

The pre-rollout runtime check passes all 117 entries, 11,082 frame/facing
contexts and 967 distinct atlas files (`audit-atlases-before.json`).

## Prior floor-calibration attempt

`audit-native-prior-floor-fix.json` verifies the first saved Faceted project,
SHA256 `56f4efdb746285a45d19c9bf0a10b14272c54f2d04bd3e6ba4843cad83709f45`.
It passes all geometry/action/material checks, including the selected light rig.
A visual pilot subsequently exposed overly bright floor colors. The final
project therefore adds a 0.42 linear-albedo multiplier only to `floor-*` and
`dock-floor`. This preserves hue relationships, tile borders and original
procedural color sources under the actual lighting. The first attempt and its
passing structural audit are historical evidence, not the final capture source.

## Final native source

`audit-native-faceted.json` passes against SHA256
`b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6`.
All 104 entries preserve their original mesh topology/positions, UV coordinates,
polygon material assignments, shape-key coordinates, object parents, armature
bones and 1,834 action curves. All 2,256 sampled native poses/facings, registered
roots, fixed canvases, projection profiles, sockets, ports and spatial metadata
match the frozen baseline.

Actual active connections and values verify:

- Five enabled white area disks: 140 W overhead at `(0, 0, 4.5)`, size 3.5;
  four equal 100 W fills at cardinal radius 3, Z 1.8, size 4. All aim at
  `(0, 0, 0.8)`. Other retained legacy lamps have zero energy; world strength is 0.
- Matte Principled surfaces use roughness 0.85, specular IOR level 0.03,
  metallic 0 and emission strength 0. The original lower-height graph feeds
  Base Color directly; the obsolete camera-normal tone is disconnected.
- The crate's original wood base colors are multiplied by 0.42 in linear RGB;
  all conveyor rails use sRGB `#966B60`. These materials use roughness 1 and
  specular 0. No other object palette changes are permitted except the floor
  calibration described above.
- Floor and dock-floor constant/procedural colors retain their original source
  and apply only the 0.42 linear albedo calibration. They acquire no artificial
  height ramp. Held ImageGen sushi preserves its exact active unlit/transparent
  material graph, texture and alpha routing.
- All 20 conveyors retain the exact registered material action owners. Actual
  deck phases match `-7 × frame / 24` through the 24 exported samples and the
  unexported closing boundary.
- Every color scene retains the actual native 135% sRGB multiply/add channel
  math with clamping. Its Render Layers node targets the correct scene and
  alpha bypasses RGB grading.

Reproduce the final native check with a separate background Blender process:

```sh
blender -b prototypes/sushi-loop/assets/production/source/blender/sushi-loop-world-library.blend \
  --python prototypes/sushi-loop/review/33/faceted-rollout/audit_native.py -- \
  --records prototypes/sushi-loop/assets/production/source/native-records \
  --reference prototypes/sushi-loop/review/33/faceted-rollout/audit-native-baseline.json \
  --floor-calibration 0.42 \
  --output prototypes/sushi-loop/review/33/faceted-rollout/audit-native-faceted.json
```

## Capture and publication verification

All checks pass. [The combined report](audit-summary.json) records every final
atlas SHA256 as well as the source identity and independent result totals.

- `audit-pixels-native.json`: all **104 native entries / 9,390 native frames**
  have complete, correctly sized captures and matching PNG receipts. Every
  animated clip/facing has at least six distinct visible frames; every conveyor
  has 24 distinct frames. No object is clipped by its fixed capture canvas.
- `audit-receipts.json`: every frame identifies the frozen project, its actual
  capture/runtime/style/action/footing helper hashes and the corresponding
  asset/rig metadata. The complete batch uses Blender 5.2.2 LTS, 32 EEVEE
  samples, 4× authored capture size and 12 fps. There are no extra PNGs.
- **9,385 frames retain byte-identical alpha.** The remaining five translucent
  light-shaft frames differ at only 2–7 source pixels each, by at most 5/255
  alpha, with identical bounds. `audit-alpha-exceptions.json` lists them.
  `audit-transparency.json` verifies the original transparent node colors and
  Mix Shader factors, including all twelve ImageGen held-food graphs.
- `audit-selected-reference.json`: all four crate and straight-belt facings
  match the approved matte-wood/clay-rail study within **0.462/255 mean opaque
  RGB difference**. The study uses 64 samples; production uses 32. Top-region
  luminance differs by at most 0.04% for crate wood and 0.42% for rails. Neither
  measured top region clips an RGB channel.
- `audit-published-atlases.json`: all **117 runtime entries / 11,082 frame-facing
  contexts / 967 atlas files** pass. All **9,390 native runtime cells are
  byte-identical** to a LANCZOS resize of the complete corresponding 4× native
  capture into its declared 2× frame size. This verifies full-frame sampling;
  no per-pose fitting, cropping or silhouette-based scaling is introduced.
- All **13 flat artwork/effect entries remain byte-identical** to their frozen
  original atlas hashes. Shared directional references deliberately reuse the
  same 2D artwork.
- The largest texture dimension is **7,360 px**, within the 8,192 px cap. Eight
  dock-cover clip/facing groups use five columns: **7,360 × 4,224** atlases with
  unchanged **1,472 × 1,408** frame cells. Only cell placement changes; frame
  pixels, registered roots, timing and sample scale remain fixed.

Reproduce the full runtime check with the Pillow/NumPy Python environment:

```sh
python prototypes/sushi-loop/review/33/faceted-rollout/audit_pixels.py \
  --published \
  --atlas-raw /path/to/complete-faceted-export/raw-frames \
  --flat-reference prototypes/sushi-loop/review/33/faceted-rollout/audit-flat-baseline.json \
  --output prototypes/sushi-loop/review/33/faceted-rollout/audit-published-atlases.json
```

These checks establish source and capture fidelity, sprite animation coverage,
registration and texture packing. Actual Godot imports, browser playback and
Android-device performance are separate checks. This audit does not claim an
Android APK or a completed game runtime.
