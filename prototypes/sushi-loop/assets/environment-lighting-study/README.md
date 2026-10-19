# Conveyor and crate lighting transfer study

The existing `#character-lighting-study` review page now has a Subject selector
for Noor, a straight conveyor, a wood crate and a connected conveyor corner.
These are isolated native Blender experiments. No production sprites are replaced.

The four treatments use the exact lighting recipe from Noor: production emission,
and Soft / Faceted / Crisp matte Principled surfaces with overhead powers
100 / 140 / 180 W. Each uses the same four 100 W fill lamps, roughness .85,
specular .03, native lower-material ramps and 135% sRGB compositor. The overhead
lamp is centered on Z; the cardinal fills are symmetric under 90° rotations.
There are no extra browser color filters or postprocessed color changes.

Environment captures retain square floor pitch and the selected 70% height
projection, rather than borrowing the character's 35° camera. Geometry, native
UVs, registration and palette are identical across all treatments. Each subject
has four directional stills at four-times logical resolution.

- Straight belt: native `belt-straight-e`, frame 192×352, root (96,248), one cell.
- Wood crate: native `crate-wood`, the same frame/root and one-cell footprint.
- Connected L: `belt-straight-s` into `belt-corner-n-e`, followed by
  `belt-straight-e`, sharing their exact authored ports at deck height .64.
  Frame 384×448, root (192,288), centered within a two-by-two-cell floor.

The South view of the connected L includes the complete 24-frame loop at 12 fps.
All three moving deck materials retain their original UV and procedural phase
graphs, driven together by `phase = -7 × frame / 24`. Frame 24 closes to frame 0
without exporting a duplicate closing image. Playback starts paused, and one
clock synchronizes all four treatment cards and their detail views.

## What the comparison shows

The lights separate the red rail tops from their sides and reveal the crate's
raised frame, braces and bevels. The light-transfer result also exposes a color
limit: the crate's already bright top boards lose channel detail in Faceted and
Crisp. Soft retains more wood color. The exact clipping measurements and their
change from baseline are retained in the independent review; this is a finding
of the experiment, not an approved replacement treatment.

## Editable source and reproduction

`source/environment-lighting.blend` has twelve independent color scenes and two
native classification-mask scenes. Meshes were frozen from the saved production
pose through Blender MCP. The original editable models/actions remain in the
production `.blend`; this study keeps the actual lighting, materials, meshes and
UVs editable for iteration.

From the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background prototypes/sushi-loop/assets/environment-lighting-study/source/environment-lighting.blend \
  --python prototypes/sushi-loop/assets/environment-lighting-study/source/lighting_study.py -- \
  --render prototypes/sushi-loop/assets/environment-lighting-study
```

Optionally split `--variants baseline soft` and `--variants faceted crisp` into
independent workers. Capture records and statuses use different filenames per
worker. All 148 native PNGs (140 color, eight masks) retain byte hashes and camera,
geometry and phase records. Masks distinguish rail/wood top and side normals;
the deck is a separate class. They receive no grade.

See `../../review/33/environment-lighting-study/` for independent native/pixel
checks, color measurements and responsive browser evidence. Issue 33 stays open;
lighting selection and final scene-art approval remain pending.
