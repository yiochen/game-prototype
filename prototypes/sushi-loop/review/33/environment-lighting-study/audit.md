# Independent environment-lighting study audit

This verifies an isolated review experiment, not an approved replacement for production lighting. The three Noor lighting presets are transferred without tuning their powers: Soft 100 W, Faceted 140 W, Crisp 180 W; every candidate has the same four 100 W fills. The crate's broad upper surfaces show why an unchanged lighting preset can have a different palette tradeoff on another object.

Saved study: `assets/environment-lighting-study/source/environment-lighting.blend`, SHA-256 `2131844e91b581812ca007dca1846ecf6208c4f5f8cb9f93de2b7749c27e756b`. Current reproduction recipe: `3ef3c62f29d12280e5930edfaf873c886a8a64d30f6230501f1968dd9eef73a2`. Its final change reads the same 100 W fill value from the preset settings; the saved lamps and all pixels are unchanged. The authoritative production library remains SHA-256 `c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`.

## Saved-source verification

`native-audit.json` passes all 12 color scenes and both classification scenes:

- The single conveyor has eight meshes; the crate has 14; the connected three-module L has 24. Geometry, topology, UV loops, root transforms and cameras are identical across the four treatments of each subject. Copies match the saved native production objects within `6 × 10⁻⁸` cell vertex precision and `3 × 10⁻⁸` UV precision. Conveyor UVs match exactly.
- All upstream lower-shading, color and deck-phase graphs match production. Candidate Principled materials connect directly to the existing base-color × world-height-ramp output, bypassing the old view-normal term. Roughness is `.85`, specular is `.03`, metallic and emission strength are zero. Baselines retain their original emission output.
- Each actual candidate lamp set contains a disk key at `(0, 0, 4.5)`, size 3.5, and four equal disk fills at cardinal positions of radius 3, height 1.8, size 4. The actual lamp positions, orientations, powers, shapes and colors form the same set after 90°, 180° and 270° world-yaw rotations. World strength is zero. This proves symmetry for the four game facings; different geometry seen from different facings need not have equal average RGB.
- Environment projection is unchanged: one world cell is 128 logical pixels in each ground axis, and one cell of height rises 89.6 pixels. Ground roots and complete authored canvases are preserved. The compositor's actual three clamped multiply-add channels retain the 1.35 sRGB grade, their Render Layers source belongs to the correct scene, and alpha bypasses RGB grading.
- Copied shader animation is cleared deliberately, while the original `Deck travel phase` Value node and procedural graph remain. The study driver sets all deck trees to `−7f/24` for frames 0–23, with closure at `−7`. The connected L has three synchronized trees. Both adjoining incoming/outgoing ports coincide exactly at deck height `.64` cells.
- Mask polygon indices match their geometry-derived definitions: red is selected upward normals (`Z ≥ .65`), blue selected side normals (`Z ≤ .35`), green the belt deck, black excluded surfaces. Mask compositing is disabled. Selection is based on rail geometry or all crate wood, not candidate image colors.

## Pixel and animation verification

`pixel-audit.json` passes 148 records: 140 color captures and eight masks. Every image hash, complete canvas, camera record, phase and expected phase-material count matches its receipt. Each connected-L treatment has **24 unique visible RGBA frames at 12 fps**, after clearing invisible RGB before hashing. All 96 animated frames match the alpha of their same-phase baseline byte-for-byte; all 36 candidate facing stills match baseline alpha byte-for-byte. The saved study and production hashes were rechecked after capture.

The eight single-object baselines also closely reproduce the preserved production PNGs: mean absolute opaque RGB difference is 0.0091–0.0121 byte for the belt and 0.0121–0.0143 byte for the crate, with maximum interior differences of two and three bytes respectively. Edge alpha differs on 2,718–4,807 pixels by at most 12 bytes. These small differences are consistent with the 64-versus-32-sample change; this comparison does not establish that sampling is their sole cause. The independent source audit verifies the actual geometry, UVs, shader graphs and projection rather than inferring them from pixel similarity.

Measurements use common opaque pixels (`alpha ≥ 250`) inside the native classification masks, eroded by two source pixels. Luminance is linear Rec.709 after decoding the PNG's sRGB values. Channel clipping means a byte value of at least 254. The reported ranges cover N/E/S/W; mask normal classes compare actual top/side surfaces, so object color and height variation also contribute to their ratio.

| Subject | Current top/side luminance | Soft | Faceted | Crisp |
| --- | ---: | ---: | ---: | ---: |
| Conveyor red rails | 1.092–1.101 | 1.340–1.350 | 1.387–1.405 | 1.434–1.461 |
| Crate wood | 2.412–2.523 | 3.890–4.042 | 4.395–4.562 | 4.542–4.703 |

| Crate upward wood region | Red clipped | Green clipped |
| --- | ---: | ---: |
| Current production | 47.85–51.24% | 0% |
| Soft | 56.86–59.88% | 0% |
| Faceted | 85.72–90.32% | 46.59–49.89% |
| Crisp | 88.95–93.39% | 48.06–51.46% |

This is broad wood-top clipping, rather than a few small highlights. None of those wood-top samples clips all three channels; blue still varies. The rail tops already have 100% red-channel clipping in the baseline and in all candidates, with zero green/blue clipping in those class interiors. Rail side and crate side class interiors have no clipped channels in these captures.

Soft is the least disruptive transferred preset for crate color because it introduces no green clipping; stronger presets expose a clear brightness/color tradeoff. The rail and wood measurements support reviewing each material class before applying a single preset to the whole catalog. No preset is approved by this audit, and production materials, frames and decisions remain unchanged.

## Reproduction

Run from the repository root. The audit loads and evaluates saved files in a separate Blender CLI process and never writes either `.blend` file:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background prototypes/sushi-loop/assets/environment-lighting-study/source/environment-lighting.blend \
  --python prototypes/sushi-loop/review/33/environment-lighting-study/audit_saved_study.py -- \
  --study prototypes/sushi-loop/assets/environment-lighting-study \
  --production prototypes/sushi-loop/assets/production \
  --output prototypes/sushi-loop/review/33/environment-lighting-study/native-audit.json

/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  prototypes/sushi-loop/review/33/environment-lighting-study/audit_pixels.py \
  --study prototypes/sushi-loop/assets/environment-lighting-study \
  --output prototypes/sushi-loop/review/33/environment-lighting-study/pixel-audit.json
```

`--production-raw /private/tmp/sushi33-art-rollout-v12/export/raw-frames` optionally adds a comparison with the preserved production raw captures. The study uses 64 EEVEE samples and those production captures use 32, so that comparison is numerical evidence rather than a claim of byte identity.
