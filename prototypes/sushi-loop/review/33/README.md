# Issue 33 native world asset review

## Current native review pass — approval pending

Review route: `/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library`. Each object has its own `#object-<id>` page. The approved concept remains available at `#art-catalog` for comparison.

The current native pass contains **125 objects across 17 families**. The saved version 11 Blender project is a normal editable `.blend` with **4,455 owned objects and 5,776 independent native actions**. It starts on `restaurant-corner-garden-a` / `ambient`, native frame 4, facing south. All 125 entries are published, including the new clusters and widened entrance; capture, source and focused browser checks pass. These are source inventory totals, not a declaration of finished visual approval.

For each object, review its four directions on the square tile grid, repeated placement in a 3×3 arrangement, scale beside interacting objects, and every directional animation. Fixed capture frames and shared tile scale are retained across poses; use the animation pause and frame controls to inspect contact, layering and clearance.

Current native coverage includes:

- Three actual recipe geometries on the chef blackboard and preference bubble: salmon, cucumber and eel. These are separate modeled food assemblies, not recolored recipe labels.
- Three distinct salvage mesh variants.
- Camera-facing reaction bubbles and reward coins, using native counter-rotation pivots to keep their symbols readable in all four world-facing contexts.
- One submarine entry with baseline and upgraded geometry variants, each with six animation clips.
- Eight dense native garden clusters, with 22–26 components per 2 × 4 or 3 × 3 assembly, a 12-frame / 12 fps ambient loop and an explicit one-frame static state.
- A modeled four-tile entrance with a two-tile clear center and the original ground-root convention.
- Animated connected conveyor pieces using **24 frames at 12 fps**. Each slat cycle uses the same phase at connected ports. The separately carried plate is a staged centerline-path preview; its travel clock is independent of the slat material.

Native fish clips are **in-place gesture studies**. Clip names do not demonstrate complete gameplay travel: translation, paths, collision and encounter behavior remain game integration work.

The [production source guide](../../assets/production/source/README.md) describes the reproducible Blender workflow. The [editable native project](../../assets/production/source/blender/sushi-loop-world-library.blend), [native action index](../../assets/production/source/native-records/index.json) and [runtime publication manifest](../../assets/production/library.json) record the source and published captures. Consult the runtime manifest for the actual publication status while the final pass is being promoted.

### Dense gardens and four-tile entrance: current revision

`restaurant-border-garden-a/b` and `underwater-reef-garden-a/b` each occupy 2 × 4 cells. `restaurant-corner-garden-a/b` and `underwater-coral-garden-a/b` each occupy 3 × 3. Their 22–26 native components combine closely packed foliage, stones, coral and restrained accents at fractional positions; A/B variants change the actual arrangement. Staggered ambient motion and a static view remain separately inspectable. Fixed source-mesh ground offsets put the components on their islands without fitting individual frames.

The restaurant composition is now 12 × 12, with four garden assemblies around the room and the four-tile entrance at `(4,11)`. The underwater composition is 14 × 12, with four native reef/coral assemblies along the banks and corners. Existing directed belt joins, matched terrain profiles, seated registrations and staged travel lanes remain the composition's reference points. The modeled entrance preserves its centered ground root and clip IDs, leaves two center tiles clear, and explicitly allows the roof to project 0.12 cell beyond its 4 × 1 ground footprint in depth.

The editable `catalog_clusters.py` recipe is retained with the native source. Source captures remain 4×; runtime sprites uniformly sample the complete authored frame at 2×. All poses and facings keep their declared capture frame. Native geometry validation passed all eight clusters and the entrance over **388 samples**. All 420 new frames are complete, and the focused object/scene checks pass. [Dense-cluster evidence](decoration-clusters/README.md) records final renders, all directions, capture checks and the entrance-clearance correction.

### Connected-module revision

All eight corner conveyors have a curved lower frame and legs placed beneath the curve, replacing the extra square table. Section 03 now shows corner-to-straight belt routes, matching wall and terrain panels, continuous rope posts, tiled floor patches, and dock assemblies. Four reversed corner UV directions were corrected so animated slats keep the same phase across their joins. The normal editable Blender project and reproducible builders include these changes. [Connected-fixture evidence](connected-fixtures/README.md) records all 50 assembled examples, 100 visible-dish samples, phone/landscape checks, and the corrected dish-layering defect.

### Forward-walk revision

The four customer walk and panic cycles now move grounded feet backward relative to the character and recover forward while lifted. This fixes the shared native gait that appeared to moonwalk. Frame order, four-direction facing, 12-frame timing and fixed sprite roots remain unchanged. The native action check covers all 32 customer/facing/walk-panic combinations, including evaluated sole contacts and loop closure; the original failing baseline is retained. [Forward-walk evidence](forward-walk/README.md) includes the 32-case browser pass, all four customers on a translating floor, and a before/after planted-boot comparison.

### Earlier complete scene preview and held-food revision

The full restaurant (`#scene-restaurant`) and underwater (`#scene-underwater`) pages compose the same registered catalog assets at one tile scale. At this earlier checkpoint, the restaurant had 69 placements with a connected conveyor island, chefs, seated diners and a walking aisle. The underwater scene had 77 placements with connected canyon/reef/wreck sections, an exploring submarine, creatures, currents and layered scenery. Playback, scrubbing, fit/detail zoom and optional grid/root overlays remain available alongside per-object links.

The restaurant composition exposed a native held-food attachment defect. The baker now exposes each rig while sampling and retains constant posed attachment transforms. The corrected 12-character library passes 96 native holding cases /1,152 samples; the historical failure is retained. [Full-scene evidence](full-scenes/README.md) records scene layouts, phone/landscape controls and the before-fix source proof. Final asset approval remains pending.

### Historical 117-entry verification record

These results belong to the earlier 117-entry source/capture revision; they are retained as milestones and do not certify the new garden/entrance pass. That version 10 project was approximately 4.4 MB, with 2,078 owned objects and 3,314 independent native actions.

- At that checkpoint, all 117 entries were ready in the runtime manifest, with no queued or partial exports.
- Full native preflight: **11,456 frames checked, 117 objects passed, zero pending or failed captures**. Source audit: **117 passes, zero errors**; 245 warnings retain independent visual-review limits and intentional return-to-rest endpoints. Reports are retained under `assets/production/source/evaluations/`.
- Final browser suite: **14 passed, one expected queued-state skip**, including phone, landscape, document scrolling, touch gestures, Back restoration and playback controls. Targeted QA checked 13 objects / 79 clips, all recipe/ship/salvage variants, and five camera-facing effects / 20 clips. All sampled images decoded. See [native-final/](native-final/README.md).
- **149 engine/helper tests and the production build passed** after the connected-module revision. Native port geometry checks cover 42 modules, four floor patches and four dock assemblies; native shader/UV checks cover all 20 conveyors and 480 baked phase samples.
- Finished scene-asset approval: **Pending user review. Issue #33 remains open until that approval.**

### Current 125-entry verification record

- Native geometry validation: **eight clusters plus the four-tile entrance passed, 388 samples**.
- Version 11 project: **4,455 owned objects / 5,776 actions**, startup `restaurant-corner-garden-a` / `ambient` / frame 4 / south. SHA-256: `732a5a4cc73c908f69ccc832e8dc1e66a63c81307157427d9b73e0efdc2acbcd`.
- Complete captures and runtime publication for the new revision: **Complete — all 125 entries are ready; 420 new frames passed capture/alpha checks.**
- Final 125-entry structural/source preflight and browser QA: **Passed — 11,872 frames / 125 objects, zero errors; eight new object pages and both responsive scenes checked; all five scene regressions pass.**
- Finished scene-asset approval: **Pending user review. Issue #33 remains open until that approval.**

## Historical concept review

The following records describe earlier checkpoints. Their counts, publication status and animation timing are historical; the current native pass above supersedes them.

Route: `/prototypes/sushi-loop/?ntl-drawer-state=hidden#art-catalog`.

This is the first concept-approval page, not the completed issue #33 production library. The user selected the wireframe site as the review destination. Final actual sprite/animation and tiled-composition acceptance remains pending; no issue has been closed.

- Repository engine tests: 129 passed.
- Production Vite build passed.
- Existing Sushi Loop browser suite: all 35 prior tests passed, including all 58 routes at 320×740, 390×844, 844×390 and 1440×1000.
- New catalog tests passed at 320×740, 844×390 and 1440×1000: fit/zoom containment, all 17 families, dish/chef coverage, previous/next bounds, reset and view-switch scroll reset.
- Existing feedback tests and new catalog branch-specific persistence/handoff test passed. No external feedback was posted.
- Actual phone-size sheet, chef and dish views are captured alongside this document. Imagegen concept details remain labeled as concepts throughout.
- Independent code review identified missing multi-panel mappings and retained scroll positions; both were fixed and covered by browser checks.

## Historical production batch 1

Ten actual Blender exports are published under `#object-library`: cream floor, wood/blue stools, crate, barrel, three recipes, straight east belt and north-to-east turn. Each has four native directional captures, nine-copy repetition and a shared-scale comparison. Belts have12unique frames at12fps, exact pause/scrub, touching seams and a separately conveyed plate. The native editable `.blend` and Python modeling/rig/camera source are versioned in `assets/production/source/blender/`. Final asset approval remains pending;107objects remain queued.

Validation:141engine/registrationtests,productionbuild,fiveactual-spritebrowserchecks,previous37wireframechecks,tenstructuralassetpasseswithzerofailures. The structural audit does not certify visualquality orfullcoverage. Actualconnected-Landphonecapturesareincluded.
