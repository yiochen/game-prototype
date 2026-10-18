# Issue 33 native world asset review

## Current native review pass — approval pending

Review route: `/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library`. Each object has its own `#object-<id>` page. The approved concept remains available at `#art-catalog` for comparison.

The current native pass contains **117 objects across 17 families**. All **117 entries are published and ready for review**. Structural/source checks cover the full inventory; browser checks exercise the shared layouts and representative objects below. The saved version 8 Blender project is a normal editable `.blend` of approximately **4.4 MB**, with **2,078 owned objects and 3,186 independent native actions**. These are source inventory totals, not a declaration of finished visual approval.

For each object, review its four directions on the square tile grid, repeated placement in a 3×3 arrangement, scale beside interacting objects, and every directional animation. Fixed capture frames and shared tile scale are retained across poses; use the animation pause and frame controls to inspect contact, layering and clearance.

Current native coverage includes:

- Three actual recipe geometries on the chef blackboard and preference bubble: salmon, cucumber and eel. These are separate modeled food assemblies, not recolored recipe labels.
- Three distinct salvage mesh variants.
- Camera-facing reaction bubbles and reward coins, using native counter-rotation pivots to keep their symbols readable in all four world-facing contexts.
- One submarine entry with baseline and upgraded geometry variants, each with six animation clips.
- Animated connected conveyor pieces using **24 frames at 12 fps**. Each slat cycle uses the same phase at connected ports. The separately carried plate is a staged centerline-path preview; its travel clock is independent of the slat material.

Native fish clips are **in-place gesture studies**. Clip names do not demonstrate complete gameplay travel: translation, paths, collision and encounter behavior remain game integration work.

The [production source guide](../../assets/production/source/README.md) describes the reproducible Blender workflow. The [editable native project](../../assets/production/source/blender/sushi-loop-world-library.blend), [native action index](../../assets/production/source/native-records/index.json) and [runtime publication manifest](../../assets/production/library.json) record the source and published captures. Consult the runtime manifest for the actual publication status while the final pass is being promoted.

### Connected-module revision

All eight corner conveyors have a curved lower frame and legs placed beneath the curve, replacing the extra square table. Section 03 now shows corner-to-straight belt routes, matching wall and terrain panels, continuous rope posts, tiled floor patches, and dock assemblies. Four reversed corner UV directions were corrected so animated slats keep the same phase across their joins. The normal editable Blender project and reproducible builders include these changes. [Connected-fixture evidence](connected-fixtures/README.md) records all 50 assembled examples, 100 visible-dish samples, phone/landscape checks, and the corrected dish-layering defect.

### Final verification record

- All 117 entries are ready in the runtime manifest, with no queued or partial exports.
- Full native preflight: **11,456 frames checked, 117 objects passed, zero pending or failed captures**. Source audit: **117 passes, zero errors**; 245 warnings retain independent visual-review limits and intentional return-to-rest endpoints. Reports are retained under `assets/production/source/evaluations/`.
- Final browser suite: **14 passed, one expected queued-state skip**, including phone, landscape, document scrolling, touch gestures, Back restoration and playback controls. Targeted QA checked 13 objects / 79 clips, all recipe/ship/salvage variants, and five camera-facing effects / 20 clips. All sampled images decoded. See [native-final/](native-final/README.md).
- **149 engine/helper tests and the production build passed** after the connected-module revision. Native port geometry checks cover 42 modules, four floor patches and four dock assemblies; native shader/UV checks cover all 20 conveyors and 480 baked phase samples.
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
