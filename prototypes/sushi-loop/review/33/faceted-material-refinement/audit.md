# Faceted material refinement verification

The user selected **Faceted** lighting. These checks verify the new material
comparison; they do not approve the wood/clay palette or close issue 33.

## Native source

`audit-native.json` passes against the saved eight-scene Blender project:

- Source SHA256: `e5dd006c8bb16a2bf4b12e1a3a94418a2993cfce1d53e94d37174cf30954f6fa`.
- Recipe SHA256: `60e7686e90645aafde18e0d0dbcdff5a0894898b3847beb4e7ab1dea4036e111`.
- All three subjects retain exactly the historical Faceted mesh positions,
  polygons, face assignments, UV coordinates, registered roots and cameras.
  The straight belt has eight meshes, crate fourteen, and connected L twenty-four.
- The selected rig remains one 140 W overhead area disk (size 3.5), with four
  equal cardinal 100 W area disks (size 4). Light transforms, white color,
  zero ambient-world strength and cardinal symmetry are unchanged.
- The only material changes are the crate's three wood colors multiplied by
  **0.42 in linear RGB**, and the four copied rail materials set to sRGB
  `#966B60`. These seven materials use roughness 1 and specular 0. Their actual
  active Principled shader is connected to the original world-height ramp.
- All other active material graphs and values are identical, including belt
  legs, wooden supports, moving charcoal deck and native deck-phase graph.
  The lower ramp is unchanged and the obsolete view-normal multiplier stays
  bypassed. Metallic and emission remain zero.
- Each color scene's Render Layers node owns that scene. Actual channel math
  is the native 135% sRGB grade, with Render Layers alpha bypassing the grade.
- All 25 sampled phase values (frames 0–24) equal `-7 × frame / 24` on every
  applicable deck material. The three connected decks remain synchronized;
  frame 24 is the loop boundary, not an exported duplicate closing image.
- Classification-mask geometry, material indices, ungraded export and camera
  remain identical to the historical masks.

The historical environment study project/manifest and production Blender source
match the recorded hashes. Git also shows no changes under the production
assets, historical environment assets or Noor lighting-source folders.

## Capture and pixel evidence

`audit-pixels.json` passes for **78 PNGs**: 35 historical Faceted color captures,
eight historical masks and 35 newly rendered tuned captures. Historical copies
are byte-identical to the original files and their original receipts. Every new
image matches its final-source capture receipt, camera, geometry hash, canvas
and recorded phase. There are no missing or extra PNGs.

All four facings retain byte-identical alpha. Each connected variant contains
**24 distinct visible frames at 12 fps**, and all tuned frames retain their
same-phase historical alpha. Unchanged straight-belt deck interiors are
byte-identical RGB in all four facings; only the intended rails change there.

Measurements use native geometry-derived, unlit masks, common opaque interiors
and two-pixel erosion. A channel value of at least 254/255 counts as clipped.
Ranges below cover all four facings:

| Measured region | Original Faceted | Tuned Faceted |
| --- | --- | --- |
| Crate top red-channel clipping | 85.72–90.32% | 0% |
| Crate top green-channel clipping | 46.59–49.89% | 0% |
| Belt rail top red-channel clipping | 100% | 0% |
| Crate top/side linear luminance ratio | 4.40–4.56 | 6.41–6.72 |
| Belt rail top/side linear luminance ratio | 1.39–1.40 | 2.65–2.69 |

No RGB channel clips in the measured tuned top regions. The stronger ratios
show recovered surface separation after removing clipped warm highlights;
they are evidence about this comparison, not a target for every material.

## Reproduce

From the repository root, run:

```sh
blender -b prototypes/sushi-loop/assets/faceted-material-refinement/source/faceted-materials.blend \
  --python prototypes/sushi-loop/review/33/faceted-material-refinement/audit_native.py \
  -- --study prototypes/sushi-loop/assets/faceted-material-refinement

python3 prototypes/sushi-loop/review/33/faceted-material-refinement/audit_pixels.py \
  --study prototypes/sushi-loop/assets/faceted-material-refinement
```

The pixel audit requires Pillow and NumPy. Both scripts read native sources and
captures and write only their review JSON reports; neither uses the live Blender
session or rewrites any `.blend` file or sprite.
