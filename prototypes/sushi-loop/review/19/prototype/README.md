# Issue 19 · UI approval evidence

[Open the verified clearance prototype](https://6ae2be3caffabf91f69d4fdf--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/expansion-preview/?state=clear).

Draft deploy `6ae2be3caffabf91f69d4fdf` belongs to `game-prototypes-yiochen` (`a05448cf-3d0c-4100-9b1a-6d8a0d28c886`). Production was not published. `deployment.json` records HTTP 200, asset/page errors, successful clearing, reopening the save and opening the newly enabled Workshop target. `deployed-phone.png` captures the exact hosted feature.

## Reference comparison

Catalog sections **1–2 and 15** govern the square floor, registered roots, distinct complete broken objects and perimeter. Sections **3–5 and 8** support the existing shared HUD/action/popup finish. Starting wireframe and current native/HTML references were read together with accepted B, the Restaurant UI & item catalog and restaurant world concept. See `../../../design/expansion-preview/brief.md` for the complete composition, surface/state inventory, source and anchor decisions. Starting references and exploratory captures are retained separately by name.

Final `*-320x720`, `*-390x844`, `*-844x390` and `*-1440x1000` captures show actual rendered scenes. `clearance-selected`, `clearance-pressed`, `clearance-disabled`, `edit-sofa-confirm`, `edit-cleared-placement`, `cleared-dock`, and `gallery-{sofa,car,shelves}-{normal,pressed,disabled,selected}` cover affected behavior and shared presentation. `starter-left-wall` shows the finished left wall and actual perimeter after panning. The wider scene stays portrait-contained, and short landscape retains every modal control.

Visual inspection checked matching world/preview silhouettes, exact square cells, fixed registered scale, continuous back/left wall, absence of panel-divider walls, no HUD backing, maple material continuity, symmetric shell/well insets, undistorted corners and icons, readable disabled cost, four visible inventory goods, accurate stock after placement, focus return and unclipped actions. An initial missing-thumbnail mapping and incorrect wall facing were corrected. Complete source frames retain alpha padding in the world; measured visible bounds are used only for uniformly scaled popup previews.

## Validation and limits

- Six clearance model tests pass: choice of neighboring patches, atomic/repeated debit, save/restore in Live and Edit, area-based capacity independent of occupancy/perimeter, shared dock reservation, starter affordability and fixed camera.
- Nine clearance browser tests pass locally against the built output, including actual touch drag/tap, outside-tap shielding, Cancel/Escape/browser Back, focus trapping, disabled cost, persisted clearing, Edit pause and newly cleared placement, gallery states and four viewport/asset checks. Remote results are recorded in `hosted-browser-tests.log`.
- All 24 existing editor-dock and Shop checks passed against the built output. The first combined built run caught a test that checked newly inserted thumbnails before download completed; asset assertions now wait for completion and still reject missing/broken images.
- Vite build passes. Its existing large-chunk warning remains.
- Full repository engine run: **211 passed, 2 failed**, including the six new model checks. Both failures are in unchanged historical refinement evidence: missing `belt-straight-n/.../consumer/.godot/.gdignore` and `coin-pop/final/original-catalog-object.json`. See `engine-tests.log`.
- The broader legacy wireframe run reached **51 passed, 11 failed, 1 interrupted, 2 not run** before it was stopped after repeated unrelated recipe/roster timeouts. The unchanged tests still expect earlier recipe, résumé, paging and return structures. Its four deep-link sweeps also failed to settle on intermediate examples; direct checks of the current floor plan, expansion, portrait and expanded examples loaded without page errors. See `broader-browser-tests.log`. This is not a claim that the full repository browser suite is green.

`capture-results.json` records settled scene/card/action measurements and zero capture request/page errors. Test touch bounds use complete border boxes; `clientWidth/clientHeight` in the capture record exclude borders. Controls are at least 44px; final clearance actions are 48px.

Costs, patch masks, 640 review coins, service timing and area/capacity progression are isolated provisional review fixtures. The native starter's 120 coins can reach the provisional 180 access price with five 14-coin sales, without another gate. This validates the prototype's transition, not native economy integration. Workshop/Submarine destinations are presentation previews. Godot engine, native saves, native balance and unrelated gameplay remain unchanged.

The game-ui-prototype skill requires approval of the deployed prototype before game implementation. Issue 19 remains open and native integration is pending that approval.
