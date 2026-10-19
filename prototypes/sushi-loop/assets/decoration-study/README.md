# Living ledges: shape, color and camera study

Focused issue 33 experiment following feedback on the rock-base study. Five decorated rock families use a high back crag, a middle ledge and a low front shelf. Compact kelp/coral appear at all three elevations. Color combinations include blue/purple, pink/amber, and green vegetation with coral accents. Crowns have shallow irregular planes rather than perfectly level tops or pointed summits. Each assembly retains a 1×1 physical footprint with 92% top-down geometry coverage over a separate ocean-bed tile. Plants are authored at compact dimensions, without stretching them to match rock height.

Rock materials multiply their base colors by a height gradient: dark navy at the base, bright blue above. This is stylized object-surface shading, distinct from future Godot ground-contact shadows. The saved native graph uses actual world Z, a height range shared by the assembly, a color ramp and connected base-color multiplication. Independent MCP inspection verifies all 15 rock materials; see the material audit under the review evidence.

## Two native camera profiles

Both profiles use 128-pixel world X pitch, logical frame 192×768, root (96,688), 4× source scale, and complete 768×3072 transparent PNGs.

- `oblique70`: screen X = 128 X; screen Y = 128 (-Y - 0.70 Z). Square ground depth. Native elevation atan(1/0.70), pixel aspect sqrt(1+0.70²).
- `ordinary35`: ordinary orthographic elevation 35°, square pixels. Screen Y = 128 (-Y sin(35°) - Z cos(35°)). Object top depth foreshortens; physical footprint and world geometry remain unchanged.

The floor always uses oblique70. The page defaults to an experimental Mixed rule: an object's complete S-facing silhouette in the reference oblique70 projection exceeds 2 tiles → use ordinary35 for all its facings. Shorter objects keep oblique70. The rule is stable per asset; it does not change with facing or screen size. `All objects · 70% oblique` provides a same-geometry control. This is a camera hypothesis for isolated decoration, not a locked production contract or evidence of an exact angle used by the concept artist. Connected terrain and architecture still require their established square-grid contract.

The mixed camera naturally changes visible object depth, so adjacent isolated bases can expose more of the common floor. Ground placements and roots remain fixed; PNG silhouettes are never fitted to cells. The original low patch is retained as another comparison with its historical frame and source project at commit 0edc5ae.

`decoration-study.blend` is the isolated editable library created through Blender MCP. `source/create_and_capture.py` reproduces it through `create(NEW_DIR)`; render its saved library with Blender CLI `--python source/create_and_capture.py -- --capture OUTPUT_DIR`. There are 41 captures: 5 objects × 4 facings × 2 camera profiles, plus one floor. `study.json`, `geometry/` and `cameras/` bind source/project/image hashes and actual native camera/root matrices. Historical flat-base and stretched studies remain in git history; `moderate/` is retained historical evidence.

Run `python source/audit.py PATH_TO_THIS_FOLDER REPORT_JSON` with Pillow. Checks cover complete captures and alpha margins, hashes, 1×1 world bounds, footprint coverage, uneven crown profiles, three decoration bands, calibrated camera axes, and identical world bounds/root transforms between camera profiles. The review route is #decoration-study. This is a static geometry/material study awaiting visual approval; issue 33 stays open and production rollout remains pending.
