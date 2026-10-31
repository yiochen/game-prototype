# Issue 19 · Clearance composition

Review milestone: an interactive HTML prototype; approval precedes Godot integration. This does not mark issue 19 complete.

## References and complete composition

Read `../../AGENTS.md`, ART-10, the accepted B composition, Restaurant UI & item catalog, restaurant world concept, current native #18 inventory capture, current #18 HTML dock/Shop, and current floor-plan/expansion/expansion-unaffordable/garbage-cluster/expanded wireframe source. Starting captures are in `../../review/19/prototype/`. Catalog sections **1–2** govern square cells and bottom-centered registered roots; **15** governs outer-edge ornament. Sections **3–5 and 8** support the already approved HUD, action states and popup family.

The full screen retains the existing cream coin/Editing pills, Edit/Live control, 21-column continuous floor, three-row back wall and finished left wall. The camera pans freely at a fixed pitch (seven cells across the portrait window); panel seams have no walls or ornament. Whole-object sofa/car/shelving clusters sit on predefined regions. Tapping a neighboring patch centers it above the bottom clearance card, adds the shared pale selection fill, and shields the room behind a light scrim. The shared maple shell contains one title, a cream preview well and two actions. No X, body copy, dimensions, extra price line or expansion numbering. The same whole-object preview is shown in Shared components. Existing current Edit dock stays visible behind the modal and resumes after dismissal.

## Surface and state inventory / asset map

| Piece | Source and independent content | Geometry, clipping and states |
| --- | --- | --- |
| Coin, Editing, Edit/Live | Existing #18 CSS HUD; SVG glyphs and live HTML count | Existing capsule highlights and shadows, 44px targets; no shared HUD backing |
| Clearance shell | Existing shared `recipe-maple.css` `.wr-panel`, approved wood grain | Responsive CSS geometry, fixed 25px corners, symmetric 14px interior insets; grain tiles at the shared scale |
| Preview well | Existing shared `.wr-catalog` cream material | 18px corners, symmetric 14px padding, independent uniformly scaled object; no bitmap panel stretch |
| Cancel / Clear | Existing cream capsule and `.wr-prepare` vermilion family | Normal, pointer-down pressed, disabled; readable coin and cost remain HTML; 48px minimum height |
| Whole broken objects | Unchanged approved production first frames | Full registered frame in world; independent preview uses measured alpha bounds as SVG viewBox, keeping aspect ratio; no per-cell stamp or stretched furniture |
| Selection / clear reveal | CSS fill and short opacity/lift on object | Selection below artwork; commit/debit/save precedes 260ms removal; reduced motion omits travel |
| Floor, back wall, left wall | Production floor frame, current `RestaurantBackdrop`, registered wall sprites | Undistorted square cells; fixed projection and roots; continuous room, no decorative seams |
| Dock / Workshop | Production dock-floor, dock-cover, sub and hut | One explicit access region; patchwork before access, disabled targets; same 3×3 shared footprint afterward |
| Perimeter ornament | Production plants, crates, barrels, lanterns, signs and rocks | Roots strictly outside actual room edges, independent of all floor/capacity calculations; no entrance or panel-connection decoration |
| Inventory board / tabs / stock | Current approved continuous maple dock CSS and Blender goods | Working categories/scroll; four visible goods. Stool places on cleared floor; other goods link to the existing Shop review. These are review fixtures, not a cross-preview shared save |
| Access destination preview | Reused maple shell, existing sub/hut art and cream return capsule | Only verifies the newly enabled destinations; Workshop/expedition mechanics remain their own slices |

No new/revised raster UI surface is required: the shell, well, cream/primary/disabled controls, dock, grain and waves reuse the approved family. No ImageGen generation or new art direction was introduced. Full original production sources and their existing provenance remain in the repository; `source-assets.json` records reference hashes and `world-registration.json` records exact extracted frames, hashes, alpha bounds, roots and scale. `prepare-assets.py` recreates the unchanged first-frame crops. No nine-slice bitmap is newly introduced, and no whole generated panel/control is stretched.

## Interactions and illustrative data

Live and Edit can inspect neighboring patches in any order. Cancel, Escape and browser/system Back preserve the patch, coins and centered camera. Outside taps keep the modal. The disabled action retains its cost. Confirmation commits once even on rapid repeated input; the cleared IDs, coins, camera, mode and placed stools persist in a separate review-only localStorage key. Edit pauses the illustrative service clock.

`balance.js` keeps provisional region masks, costs, service earnings and perimeter positions separate from `model.js`. Regions intentionally include surrounding rubbish/floor in addition to the native object footprint; native artwork keeps its original size. Clearing grows *total cleared area*, not empty cells. The access region reserves the shared 3×3 dock/Workshop footprint. Clearing other regions does not unlock it. Newly cleared ordinary cells permit stool placement; occupancy does not reduce floor-based capacity. Review fixtures use 640 coins, while Starter earnings begins with the native starter's 120. A provisional 180 access cost takes five 14-coin sales (40 illustrative seconds), without expansion or another gate. These values demonstrate affordability, not approved native balancing or service timing.

Use the external review selector for Restaurant, Clearance, Edit, Not enough coins, Dock opened, Starter earnings and Shared components. Reset replaces only this prototype's fixture. Panning supports pointer/touch, wheel/Shift-wheel and arrow keys. Layout stool placement uses a separate four-stool fixture; other game systems remain representative context.

## Approval boundary

The game-ui-prototype skill requires approval of the deployed prototype before game implementation. The native game, engine, current native saves and content balance are unchanged. Review feedback authorizes another prototype revision; it does not itself approve native integration.
