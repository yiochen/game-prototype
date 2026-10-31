# Issue 19 · Revised clearance and perimeter composition

This is the second UI review, responding to the user's 2026-10-29 feedback. The first draft and its evidence remain in `../../review/19/prototype/`; its source snapshots are in `../../review/19/revision-2/`. Native Godot integration remains pending approval of the deployed UI.

## Corrections and composition

Each trash object now owns exactly its registered ground footprint, rotated for its native facing. The old 3×3 / 4×4 surrounding clearance regions are removed. A deterministic authored packing contains **41 individual objects** in the two future panels: broken sofas, cars, shelving, new mustard armchairs and new low honey-wood cabinets. The ordinary occupied masks cover 131 cells exactly once; the visible covered 3×3 dock is separate. Nothing stretches a model or grants an invisible surrounding clearance area. Source sprites retain their entire calibrated frame and ground-root registration; sprite height can rise above its ground cells. Pointer/touch selection reads actual rendered sprite alpha in depth order, including raised artwork, while stable named buttons preserve keyboard access.

The screen retains the current cream coin/Editing capsules, Edit/Live control, continuous square floor and current back/left wall. The Live/Edit camera pans at a fixed seven-cell pitch. Native model roots sit at their footprint centers. Opening the clearance card centers/highlights that object above the same maple shell: title, matching whole-object preview, Cancel and priced Clear only. Nothing is baked into a shared text/image composite.

The actual left boundary now has a continuous outer bed, staggered depth lanes, varied native facings, exposed rock faces, attached crevice foliage and separated potted plants, crates, barrels, lanterns and sign. The corner wraps into the bottom edge; right and bottom edges also have independent dressing. Roots and physical silhouettes stay outside usable floor, entrances and panel connections. The finished wall is retained behind the decor. There are no decorative walls at panel or viewport divisions.

## ImageGen first, native reconstruction second

The user explicitly requested ImageGen followed by reconstruction with decor objects. `../../review/19/revision-2/targets/left-edge-imagegen.png` is the full original generated scene target. Its exact prompt and reference hashes are beside it. The current screenshot was the edit target; the restaurant concept and catalog were separately identified style references. This target is shown only in the review comparison, never as the runtime restaurant background.

The first reconstruction with existing props is retained in `edge-existing-props.png`. It filled the edge but exposed a concrete gap: the old pale flat slate slab could not provide the target's layered blue/violet rock shoulders and crevice foliage. A native rockery variant refines that existing source. The new armchair and cabinet similarly refine the existing sofa/shelf sources to provide new physical sizes and silhouettes rather than mere recolors. All three use the **refine-3d-model** workflow with a fresh independent editor/judge pair per object, untouched native backups, fixed ImageGen targets, exact prompts/reference hashes, frozen criteria, native four-facing exports, phone consumers and hash-bound independent reviews. Full originals and round evidence remain under `experiments/`.

Source camera/frame/root/pixel aspect remain measured technical locks. ImageGen's occasional lower view or halo does not override them. The two furniture variants intentionally change the old source footprints to 1×1 and 2×1; this is recorded modeling freedom. All production sources remain untouched. Final prototype sprites are exact independently approved Blender render bytes, with no paint-over, target-facing cards or post-approval recoloring.

## Surface / source inventory

| Piece | Source | Composition and state handling |
| --- | --- | --- |
| Coin, Editing, Edit/Live | Current #18 CSS/SVG HUD family | Live HTML amounts; normal/pressed; unchanged capsule geometry and no shared HUD backing |
| Clearance shell / preview well | Shared maple `.wr-panel` / cream `.wr-catalog` material | Fixed rounded geometry and symmetric insets; wood grain tiles; separate uniformly scaled object preview |
| Cancel / Clear | Existing cream capsule and vermilion `.wr-prepare` | Normal, press-in, disabled; cost remains readable; live labels/coin; 48px minimum action height |
| Broken sofa/car/shelf | Existing exact production captures, all four native facings | Real registered model footprints, no surrounding region; world and preview use same recognizable bytes |
| Broken armchair/cabinet | Independently refined native variants | New 1×1 / 2×1 physical envelopes; four facings, standalone editable model and recipe; alpha-fitted uniform preview only |
| Selection / clearance reveal | CSS selection fill and 260ms opacity/lift | State commits/debits/saves before animation; reduced motion removes travel |
| Floor / wall | Existing floor, `RestaurantBackdrop`, native side-facing wall | 21×13 continuous floor, top three rows are backdrop; square cells and fixed world roots |
| Dock / Workshop | Existing separate floor, cover, sub, hut | Access car is a 3×2 object directly below the separately covered 3×3 platform; exact explicit access ID controls both targets |
| Perimeter | Native rockery variant + current plants, slate, barrels, crates, lanterns, sign | Independent registered props; varied native facings, layered depth and heights; collision/capacity/earnings never include decorations |
| Trash variety review | Reused maple/cream component family | Five models × four native facings, footprint labels in review chrome, scrolling and direct access to shared clearance preview |
| Edge comparison | Live scene beside the full original ImageGen target | Side-by-side on wide windows; Target/Objects toggle on phone; preserves the same saved scene/camera |
| Edit inventory | Current continuous maple dock and Blender goods | Working categories/scroll, separate four-stool placement fixture; other goods link to the existing Shop review |

`world-registration.json` binds exact consumed bytes, source hashes, measured visible bounds, full logical frame, root, facing and model footprint. `prepare-assets.py` extracts unchanged production facings and retains approved variant records; it never re-renders or retouches approved models. `source-assets.json` records UI references and model lineage. Existing UI textures and surfaces are reused; all new raster targets use the built-in image generation tool.

## Behavior and data boundary

`balance.js` holds the fixed packing, per-object prices, prototype economy and decor placements. `model.js` owns clearing, pause, placement, save/restore and capacity transitions. Cancel/Escape/browser Back preserve the trash and centered camera; outside taps keep the card. Repeat input cannot pay twice. Edit pauses earnings; clearing persists across reopening. Newly freed ordinary cells accept placement. Capacity/arrival potential depend on cleared ordinary floor area, not empty cells; reserved dock cells never accept inventory placement. The dock's nine visibly covered cells are separate from the access car's six-cell clearance mask and do not become hidden extra trash area.

The new masks intentionally use an isolated v2 review save key; incompatible old rectangular-region saves reset only in this prototype. Native installed saves remain untouched. The Starter fixture has the native starter's 120 coins; five provisional 14-coin sales reach the 180 access price without expansion. Native service timing, arrival routing and staff limits still need integration/validation after UI approval.

The external review selector includes Edge comparison, Trash variety, Restaurant, Clearance, Edit, Not enough coins, Dock opened, Starter earnings and Shared components. Reset replaces only this review fixture. The real scene supports touch/pointer pan, wheel/Shift-wheel and arrow keys. The comparison and variety labels are review controls, not added game controls.

## Reference contract and approval

Applicable catalog sections: **1–2 and 15** for square-grid objects, footprints, materials and actual perimeter dressing; **3–5 and 8** support the reused HUD, action states and popup family. Current B/maple amendments and current native #18 UI supersede historical wireframe materials. Full-scene narrow phone, landscape and wider portrait-contained captures plus shared component states are saved under `../../review/19/revision-2/`.

The game-ui-prototype skill requires approval of the deployed prototype before game implementation. Review feedback authorizes this prototype revision, not native integration. Issue 19 is not marked complete; the acceptance audit distinguishes verified prototype behavior from the remaining native work.
