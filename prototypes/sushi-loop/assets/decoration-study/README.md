# Raised rock-base decoration study

Focused issue 33 geometry experiment. The extra height comes from the supporting rock bases. Coral, kelp, and ruin pieces retain their original mesh dimensions and move upward rigidly. Rocks have broad level crowns with chipped rims and large irregular side facets, replacing the pointed summits and stretched foliage from the earlier height experiment.

| Composition | Total projected height | Rock base projected height |
| --- | ---: | ---: |
| Rock shelf | 1.00 | 1.00 |
| Coral on ledge | 1.80 | 1.30 |
| Broken column on ledge | 2.50 | 1.92 |
| Kelp on ledge | 3.00 | 2.22 |
| Cobalt plateau | 4.00 | 4.00 |

Values measure vertical rise above ground after the 70% projection, excluding the visible depth of top surfaces. Exact base heights are in `study.json`. All compositions retain a 1×1 footprint and the separate ocean-bed tile. Each level crown covers over 80% of a cell. These are static native shape/material controls, not final surface-refined art or production replacements.

Fixed capture: screen X = 128 X; screen Y = 128 (-Y - 0.70 Z). Logical frame 192×768, root (96,688), source scale 4, PNGs 768×3072. Four native root rotations use the same camera, world scale, and lighting. There are 21 captures: five objects × four directions plus one floor. No bitmap stretch, fitting, rotation or clipping.

`decoration-study.blend` is the isolated editable project authored through Blender MCP. `source/create_and_capture.py` recreates the scene through `create(NEW_DIR)`; render its saved library with Blender CLI `--python source/create_and_capture.py -- --capture OUTPUT_DIR`. Source/project hashes, native geometry and per-capture camera receipts are retained.

`original/` preserves the original low captures. Its source project is retained at commit `0edc5ae`; historical geometry for coral, kelp and column is included for independent shape comparison. `moderate/` is the superseded stretched experiment, retained as historical evidence and excluded from the current page. The previous bold stretching experiment is preserved at commit `1d35584`.

Run `python source/audit.py PATH_TO_THIS_FOLDER REPORT_JSON` with Pillow. The audit checks hashes, native 1×1 bounds, top-down mesh coverage, total target heights, calibrated projection, full-frame PNG size and alpha margins. It also verifies broad planar crowns and proves all 22 decorative parts match the historical meshes up to one translation, with unchanged vertices, faces and dimensions.

The live review route `#decoration-study` compares raised rock bases with the original low patch, two seven-column shorelines, mixed/repeated 3×3 patches and four facings. Numeric height choices remain experimental. Final approval, full production rollout, animation, collision and Godot runtime shading remain separate work.
