# Concept decoration review evidence

Asset paths and commands below refer to the [native asset folder](../../../assets/concept-decoration/README.md); this folder holds review screenshots and validation evidence.

The previous exploratory arrangements did not follow the concept art closely enough. This isolated native set uses twelve identifiable decoration families from the approved underwater and restaurant images. Every piece has an explicit reference crop, a fixed modeling recipe and a short shape/material brief. No random sampling or randomly assembled garden generator is used.

Underwater: broad cobalt crags, a low cobalt shoulder, fanned thick hollow pink/violet coral, bent branching kelp, a broken pale column with lime growth, and a moss-covered stone face. Restaurant: a grey-violet slate bank, dense angular shrubbery, a full wooden planter, offset framed crates, a cone/striped-curb corner, and a golden lantern/timber/shrub grouping. Each family is a reusable one-cell composition; grouping does not imply that collision, support and visible art bounds are the same.

| Piece | Scene | Max projected silhouette | Top-down union | By-height profile |
| --- | --- | --- | --- | --- |
| Cobalt crag bank | underwater | 2.59 | 95% | 35° upper / square foot |
| Low cobalt shoulder | underwater | 1.58 | 95% | 70% oblique |
| Fanned pink and violet coral | underwater | 1.83 | 94% | 70% oblique |
| Branching kelp fan | underwater | 2.38 | 94% | 35° upper / square foot |
| Broken pale column | underwater | 2.13 | 99% | 35° upper / square foot |
| Mossy stone face | underwater | 2.37 | 90% | 35° upper / square foot |
| Slate rock bank | restaurant | 2.38 | 95% | 35° upper / square foot |
| Dense angular shrub | restaurant | 1.80 | 91% | 70% oblique |
| Honey-wood planter | restaurant | 1.94 | 100% | 70% oblique |
| Stacked honey-wood crates | restaurant | 1.78 | 76% | 70% oblique |
| Construction corner | restaurant | 1.33 | 83% | 70% oblique |
| Golden lantern and shrub | restaurant | 2.43 | 86% | 35° upper / square foot |

## The four rules

1. **Projection follows height.** The shared ground always uses the 70% square-grid oblique profile. By-height mode picks 35° upper geometry with square footing if the largest 70% complete silhouette across four facings exceeds two tiles; otherwise the object uses 70%. Every family retains both sets of native captures. Unlike the earlier study's S-only reference rule, this threshold uses the largest facing. Camera exceptions remain for review, not a change to connected production architecture.
2. **Maximum three projected tiles.** The audit measures the entire projected silhouette from actual evaluated capture vertices, including footprint depth and the near-ground projection correction, across every facing and both profiles. It also checks rendered alpha height. Every source shape fits below three tiles; this is stricter than only limiting vertical rise.
3. **Full cell width/depth and substantial mass.** All assemblies stay within one native X/Y cell, with at least 0.98 cell extent along each ground axis and 76–100% top-down mesh-union coverage. Natural contour notches and ground gaps remain visible. This is a plan-area metric over the whole assembly, not measured ground contact or collision. Floors are independently reusable beneath the objects. Rocks have broad main masses and offset shoulders; plants occupy their own cell, rather than always garnishing a tall rock. Compact rubble supports replace the earlier flat colored plant plates.
4. **Dark lower surfaces without a world light direction.** The isolated scene has zero lights and zero world illumination. All material surfaces are emission. World Z drives darker bases and brighter tops; camera-relative symmetric form tone helps expose facets without introducing world light azimuth. Golden lantern surfaces remain bright. Ground-contact shadows remain a separate future runtime layer.

## Native capture and source

`concept-decoration.blend` is the isolated editable source created through Blender MCP; the user's active project is not overwritten. `source/create_and_capture.py` contains explicit mesh placements, native materials and fixed capture controls. Create with `create(NEW_EMPTY_DIR)` through Blender MCP. Capture the saved library with Blender CLI `--background NEW_DIR/concept-decoration.blend --python source/create_and_capture.py -- --capture NEW_DIR`.

There are 98 unchanged full-frame native PNGs: twelve pieces × four facings × two profiles, plus two floors. They share a 128px logical tile pitch, 192×768 logical frame, root (96,688) and 4× source scale (768×3072 pixels). Blender render dithering is disabled and lossless PNG compression set to 100 to avoid noise and unnecessarily large transparent frames. No bitmap squeeze, alpha fitting, individual recentering or silhouette mask is used.

For the 70% profile, screen Y = 128 (-Y - 0.70 Z). For the ordinary-35 upper profile, screen Y = 128 (-Ycapture sin35 - Z cos35), where below Z=0.42 the native capture-space Y coordinate transitions to a square footing: `Ycapture = Y * (1 + (1/sin35-1) * max(0,1-max(0,Z)/0.42)^2)`. The actual transformed capture geometry is exported and source vertices restored. This is a hybrid upper-view/footing projection, not pure ordinary orthographic over the entire shape.

Native project, recipe, logical geometry, images and actual capture geometry are SHA256-bound by manifests/receipts. `concept-references.json` records unchanged image hashes and crop rectangles (x1,y1,x2,y2). The UI shows those original crops via SVG viewBoxes, never as reconstructed concept art.

## Review and verification

`#decoration-study` switches between two scene sets and shows the preserved original concept, a deliberate seven-column perimeter, mixed or repeated 3×3 patches, and every object's four facings beside its exact concept crop. Global projection, grid and layer controls preserve one document scroll on phone and landscape. Existing full-scene pages and production catalog assets remain available.

Run `python source/audit.py THIS_DIR` with Pillow to regenerate `measurements.json`. It checks all hashes, crop bounds, physical bounds and mass, calibrated axes, true projected and rendered height, frame/alpha margins and square-footing depth preservation. Run `inspect(THIS_DIR)` from `source/inspect_materials.py` inside Blender to verify the isolated scene's actual materials and lighting.

This is a static native shape/material review. No ImageGen surface reskin, animation or production-library rollout is represented as completed by this study. Final polish and plant motion follow shape approval; any animations must preserve the established six-frame minimum and 12 fps. Issue 33 remains open until the user approves the scene assets.

## Validation evidence

164 engine tests, production build and three browser tests pass. Each responsive test covers both scenes at 390×844, 844×390 or 1440×1200, original references, six cards × four facings, profile switching, floor invariance, layers/grid, repetition, image dimensions, no horizontal overflow and a single vertical scroller. Native audit covers all 98 captures. Independent material inspection is bound to the exact project/recipe hashes.

Earlier native iterations are retained selectively under `iterations/` to show the straight-kelp/narrow-rock/flat-footing issues; they are not served as current assets. The final set uses broader rock masses, bent/forked kelp and low rubble under coral/kelp.
