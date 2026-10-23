ROCK-SHELF-MIDDLE ROUND-01 — NATIVE EDITOR HANDOFF, AWAITING ORIGINAL JUDGE
The fixed original/target/style/native source were independently inspected before the frozen criteria; see initial-observations.json. Brief and root native contract hashes are acknowledged in frozen-brief-acknowledgement.json.

EDITABLE SOURCE
round-01.blend is a private self-contained scene containing only this low shelf, root, registered camera, five symmetric broad area lights, native material graphs and the build recipe text. No external images/libraries, animation, armature, shape keys, ground receiver or image repairs. Core is a closed manifold mesh with two exact six-vertex end caps, exact six-point rings in the .06world endpoint bands, sculpted crown grooves, shoulder/body relief and three embedded flattened stones. The max native height is below .45. Original six-point port section and finite ground y±.45 are preserved.

REPRODUCE IN A NEW COPY, preserving sealed bytes here:
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b -P source/build-round-01.py -- capture
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b source/round-01.blend -P source/validate-native.py
PYTHONDONTWRITEBYTECODE=1 /Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 source/publish-and-preview.py
node source/capture-consumer.cjs
PYTHONDONTWRITEBYTECODE=1 /Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 source/measure-seams.py
Paths above are relative to the object experiment; scripts resolve their own paths. This reconstructs art from native geometry, not the target image. No per-view parameters or fitting. Native runtime binaries are externally pinned; the used grade/consumer/minimal bundled Playwright modules are frozen here.

CAPTURE / PUBLISH
EEVEE32, actual registered55.0079798014degree orthographic square-grid camera, pixelAspect1.22065556, logical192x352/root96,248/cell128; native4x768x1408/root384,992. Persistent native filter_size.5, whole-frame BOX to published2x384x704/root192,496. All four exact original-layout atlases are 1x1/static1frame/fps12/nonloop. Native3middle roots(-1,0,0),(0,0,0),(1,0,0) rotate together under the same camera/rig; joined viewport logical448x608/root224,376.

EVIDENCE
native-validation.json records actual topology, bounds, cap faces, static checks, camera/root, graph/resource identities and lights. endpoint-evidence.json records actual ordered endpoint corner normals/albedo and ray-sampled neighboring bands. True boundary YZ/albedo match exactly; stored custom normal differences2.05e-6. Band ray sampling has numerical residuals up to3.41e-5normal and1.55e-6albedo.
publication-proof.json verifies every whole RGBA BOX result against its original-layout atlas pixels. Actual unchanged spriteFrame/groundRoot/orderPlacements/worldRasterPlan/paintWorldRaster render all4 on light/gray/dark at logical128cell/phone32cell. Only unused React hooks are stubbed. Native nearest is set AFTER resize; final wholecanvas uses ordinary CSS filtering. All4 phase0/.25/.5/.75 screenshots include both logical and phone sizes.
seam-measurements.json reports zero assembled alpha undercoverage on native-opaque pixels, globally and within the actual projected cutface masks, in all4. Finite native area lighting and centered independent captures retain broad RGB residuals (local max up to20), so no fullimage RGB identity is claimed. Measurements are technical evidence, not visual approval.

Declared review previews are listed in delivery/delivery.json. Every exact candidate render/declared preview requires original judge coverage under frozen REVIEW-COVERAGE. No self-approval, production promotion or family approval is inferred. Follow-on shelf resources remain subject to their own review after canonical approval.
