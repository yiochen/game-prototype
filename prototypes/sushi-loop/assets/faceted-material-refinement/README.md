# Selected Faceted lighting: wood and conveyor material refinement

**Approved historical study — 2026-10-19.** The user approved the tuned crate
wood and muted-clay rails and authorized regeneration of the whole native
library. The [approved production rollout](../../review/33/faceted-rollout/README.md)
records the completed capture and validation. This folder retains the original
before/after comparison images.

The user selected Faceted lighting on 2026-10-19. This follow-up keeps that exact
lighting and compares original materials with a quieter, matte finish. The
previous four-preset study is retained unchanged in `../environment-lighting-study/`.
The user subsequently approved the tuned materials. This isolated study remains
separate from the complete production recapture linked above.

## Material changes

- Crate: all three active wood colors use 42% of their previous **linear** base
  color, preserving their hue relationships and the native lower-height ramp.
  The active Principled shaders use roughness 1, specular IOR level 0, metallic 0
  and emission strength 0. The lower albedo prevents the pale top boards washing
  out under the chosen light; roughness alone cannot correct diffuse brightness.
- Conveyor: the red rails change from sRGB `#E3493F` to muted clay `#966B60`.
  The actual connected shader receives the converted linear RGB values, with
  roughness 1 and specular IOR level 0. The charcoal deck, procedural movement,
  legs and their wood colors remain unchanged. Straight and curved modules share
  the same new finish.

Both treatments retain the centered 140 W overhead area key, disk size 3.5, and
four equal 100 W cardinal area fills, disk size 4. Geometry, UVs, facets, lower
material ramps, the native 135% sRGB grade and alpha bypass remain unchanged.
Environment captures keep square floor pitch and the selected 70% height camera.

## Native source and captures

`source/faceted-materials.blend` contains eight isolated scenes: before/after
for the straight conveyor, crate and connected L, plus the two native surface
classification masks. Authoring and material edits were performed through Blender
MCP. The editable models, lamps, materials, camera and compositor are saved.
The original production project and prior experiments remain unchanged.

The 35 original Faceted PNGs and eight masks are copied byte-for-byte from the
previous study. There are 35 new tuned captures: four directional stills for each
subject plus the remaining 23 connected-conveyor animation frames. Every PNG is
four-times logical resolution. The connected L retains the complete 24-frame
loop at 12 fps; all three deck materials share phase `−7 × frame / 24`.

Reproduce the tuned captures from the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background prototypes/sushi-loop/assets/faceted-material-refinement/source/faceted-materials.blend \
  --python prototypes/sushi-loop/assets/faceted-material-refinement/source/material_refinement.py -- \
  --render prototypes/sushi-loop/assets/faceted-material-refinement
```

For independent workers, add `--subjects crate-wood belt-straight` or
`--subjects belt-connected`; their receipts and statuses use distinct filenames.
The recorded source/recipe hashes and per-capture phase/camera/geometry hashes
support verification. See `../../review/33/faceted-material-refinement/` for
independent source, pixel, clipping, animation and responsive browser evidence.

The live review page shows the selected Faceted materials beside their revised
materials with four facings, enlarged surface views and synchronized belt playback.
It does not use a browser filter. Lighting and the tuned materials are approved;
the current production catalog uses the full-library rollout linked above.
