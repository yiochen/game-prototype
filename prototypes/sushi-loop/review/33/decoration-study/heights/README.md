# Decoration height comparison

User requested a taller patch after reviewing the original, then explicitly asked for bold 3–4 projected-tile-height decorations. The page defaults to Bold, with Moderate and Original comparison settings. These are experiments awaiting visual approval, not new locked height bands or a production rollout.

| Object | Original projected height | Moderate | Bold |
| --- | ---: | ---: | ---: |
| Rock shelf | 0.25 | 1.0 | 1.0 |
| Coral | 0.59 | 1.2 | 1.8 |
| Broken column | 0.67 | 1.4 | 2.5 |
| Kelp | 0.87 | 1.6 | 3.0 |
| Cobalt peaks | 0.91 | 1.6 | 4.0 |

Heights measure the vertical component above ground after the 70% projection, excluding visible ground depth. The model heights are those values divided by 0.7. Native upper meshes are extended around their attachment heights; ground stones stay shallow, and all X/Y vertices remain unchanged. The pronounced narrow spires are intentionally exposed for review rather than widened outside the one-cell footprint. Bold assets have extra transparent headroom, without changing pixel pitch or fitting silhouettes. Both new native projects are saved in the repository. Original project provenance is commit 0edc5ae.

42 new native captures pass hashes, measured target heights, unchanged 1×1 footprints (88–95% geometry coverage), 70% axis calibration and alpha-margin checks. Original images remain unchanged. MCP top/right/three-quarter views were inspected for moderate coral/rock and bold peaks. Final phone patch and shoreline screenshots were inspected: taller banks enclose the passage more strongly, while dense 3×3 placements deliberately expose foreground occlusion and repeated shapes. These static native controls retain angular modeling; final surface treatment and animation are outside this height experiment.

164 engine tests, production build, and three responsive browser tests pass. Browser checks cover bold/moderate/original switching, correct height labels and PNG dimensions, viewport headroom, layer toggles, mixed/repeated placement, facing controls, image decoding and single-page scrolling at 390×844, 844×390 and 1440×1200. Issue 33 remains open pending asset approval.
