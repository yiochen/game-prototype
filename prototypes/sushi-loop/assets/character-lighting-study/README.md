# Noor: top-versus-side lighting study

**Historical study — 2026-10-19.** The user chose Faceted lighting and approved
the later crate/rail materials. The [approved full production rollout](../../review/33/faceted-rollout/README.md)
supersedes this experiment; its original comparison images remain unchanged.

An isolated experiment requested after the full-catalog review. It left the
production library unchanged at the time. Open `#character-lighting-study` on the wireframe site to
compare one fixed Noor idle pose in all four directions, with enlarged hat views.

The former emission treatment ignores lamps. Its subtle camera-facing form term
can even make a top plane slightly darker than a front plane. This study replaces
the active surface with matte Principled BSDF, retaining the original palette and
world-height lower ramp while letting actual Blender lights describe the facets.
The original emission version is retained as the baseline.

| Candidate | Overhead disk | Four equal fill disks | Top/side luminance ratio, four facings |
| --- | --- | --- | --- |
| Before Faceted rollout | None | None | 1.065–1.116 |
| Soft overhead | 100 W | 100 W each | 1.706–1.903 |
| Faceted overhead | 140 W | 100 W each | 2.135–2.405 |
| Crisp overhead | 180 W | 100 W each | 2.562–2.911 |

All key disks have diameter 3.5 at (0,0,4.5). The equal 4-unit fill disks sit at
(3,0,1.8), (0,3,1.8), (-3,0,1.8) and (0,-3,1.8), aimed toward (0,0,.8).
The rig is invariant under cardinal yaw rotations: no fixed brighter world-left
or world-right side is baked into the four facings. World strength remains zero.
Principled roughness is .85, specular IOR level .03, metallic and emission zero.

The original native 135% sRGB grade and alpha bypass remain enabled. No PNG or
browser contrast adjustment is added. Higher key strengths were rejected because
the grade clipped the green channel, which lost upper-facet variation. Their
sources and evidence are retained in the review attempts folder.

The final three candidates have zero clipped green pixels in the measured hat-top
regions. Ratios use linear Rec.709 luminance, with actual normal-classification
masks and eroded edges. They quantify the experiment, not artistic approval.

## Saved project and reproduction

`source/noor-lighting.blend` contains four independent lighting scenes and one
hat-mask validation scene. Each has the same 58 frozen evaluated meshes from
Noor's production `idle` frame 4: original geometry, C125 proportions, 35° camera,
192×320 logical frame, root (96,248) and four-times source resolution. This is a
still-pose lighting project; the production model retains the editable rig/actions.

Authored through Blender MCP. To iterate, open the saved project, choose a study
scene and adjust its overhead area light or equal fill lights. Recapture from the
repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background prototypes/sushi-loop/assets/character-lighting-study/source/noor-lighting.blend \
  --python prototypes/sushi-loop/assets/character-lighting-study/source/lighting_study.py -- \
  --render prototypes/sushi-loop/assets/character-lighting-study
```

The renderer writes native transparent PNGs directly. `manifest.json` and
`captures.json` retain camera, geometry, project, recipe and image records.
The independent audits and responsive review evidence are in
`../../review/33/character-lighting-study/`.

Faceted was subsequently approved for the complete native production library;
this folder retains the earlier comparison and its measured results.
