# Dense decoration cluster review — issue 33

Both scene pages use reusable native decoration assemblies, with the unchanged original scene concepts still shown below the composed views. The catalog contains 125 published objects; the eight new clusters have their own four-facing, repeated 3×3, shared-scale context and animation pages.

| Theme | 2×4 variations | 3×3 variations |
| --- | --- | --- |
| Restaurant | restaurant-border-garden-a / b | restaurant-corner-garden-a / b |
| Underwater | underwater-reef-garden-a / b | underwater-coral-garden-a / b |

Each cluster has 22–26 independently editable native components, unequal fractional positions, varied heights and overlapping foliage/rock/coral masses. A/B variants change geometry arrangements rather than only color. Each has a 12-frame ambient loop at 12fps and a one-frame static state, captured in N/E/S/W. Capture scale is 4× and runtime atlases use a uniform 2× sample of each complete registered frame. The fixed native component ground offsets are recorded in `catalog_clusters.py`; no individual pose or finished bitmap is fitted.

The entrance is modeled at 4×1 cells, with supports at its outer cells and a clear two-cell center. Roof members and curtains were rebuilt at the wider span. Its pitched roof has a declared 0.12-cell depth overhang; this does not enlarge the ground support. The 12×12 restaurant stages it at(4,11), in front of the walking lane. The 14×12 underwater scene uses reef/coral clusters around its existing connected banks and travel routes.

## Verification

- Native geometry/action audit: 8 clusters plus entrance, 388 actual evaluated facing/frame samples; all pass. Four geometry fingerprints establish distinct A/B arrangements. Actual mesh rays check the entrance opening.
- Native capture/alpha checks: 420 new frames, all complete, no capture-edge clipping. The full 125-object preflight passes 11,872 frames with zero failed/pending IDs. Source audit passes all 125 objects with zero errors; recorded warnings retain visual approval and intentional return-to-rest limitations.
- Browser checks: all eight new object pages, both states/all directions, sampled frames 0/5/11, repeated arrangements, comparison scenes and image decoding pass. Both composed scenes pass 320px,844px landscape and 1440px layouts, playback and single-document-scroll checks. The five existing scene regressions pass.
- Final gate-clearance follow-up: June remains fully visible at 12 desktop route times and four phone times. Corrected full-scene images and `final-gate-report.json` supersede the earlier entrance placement. `before-gate-clearance/occlusion.png` preserves the beam obstruction found during visual review; it is historical failure evidence.
- 164 engine/helper tests and the production build pass. Existing native belt/wall/terrain joins and route timing remain unchanged.

`initial-browser-report.json` covers the object/underwater checks and the earlier restaurant layout. `atlas-alpha-report.json` records every new frame. Native source and geometry reports live under `assets/production/source/evaluations/decoration-clusters/`; complete Blender geometry, materials and baked actions remain in the saved project. Native grounding diagnostics and the earlier validator's static-clip detection mismatch are preserved separately from the final passing report.

Finished scene-asset approval is pending user review. Issue #33 remains open; Godot Android remains the game target.
