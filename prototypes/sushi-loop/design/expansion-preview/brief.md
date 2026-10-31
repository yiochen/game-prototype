# Issue 19 · Revised clearance and perimeter composition

This is the eighth UI review. The latest instruction requires every surrounding trash object to be removed before uncovering the submarine. The prerequisite is now derived from the one-cell border around the covered dock footprint, including corner cells, rather than a single access-car ID. The accepted edge-to-edge composition and stationary camera remain. `?state=partial` shows a cleared car with other neighbors still blocking the cover; `?state=almost` leaves one final required object. Pre-change snapshots are in `../../review/19/revision-8/source-before/`. The user subsequently approved this revision for Godot implementation; see [native contract and evidence](../../review/19/native/README.md).

## Covered submarine feedback

An attempt to use the still-covered submarine shows **Clear all surrounding trash first.** The toast reuses the cream material, inset highlight, lower rim and shadow of the existing People/chef `.notice` surface. Its live text wraps inside symmetric padding below the HUD, with polite status feedback and no focus transfer or pointer interception. It dismisses after 3.2 seconds; repeated attempts restart that interval. Reset, inspecting trash or opening the uncovered destination clears it.

All seven ordinary trash footprints touching the border are prerequisites: `armchair-west`, `dock-access`, `trash-9-4`, `trash-8-5`, `trash-10-6`, `trash-10-8` and the diagonal `trash-10-9`. `dockBlockers()` and `dockReady()` in `model.js` supply one shared rule for the cover, interaction guard and reserved platform. Each required object must be cleared in full; any one remaining object keeps the dock covered. Trash farther away is unrelated. The final required clearance reveals both the submarine and Workshop; no extra reveal charge is added. Existing partial saves retain their cleared objects and are re-evaluated against this complete prerequisite.

A rejected uncover attempt changes no coins, save data, camera, placement or access state. The cloth shares the rendered-alpha, depth-ordered pointer selection with trash, preserving artwork drawn in front. A named **Uncover submarine** target supports keyboard activation. Once all required trash is cleared, **Open Submarine** and **Open Workshop** work normally. Prices and artwork are unchanged.

## Edge-to-edge alternative

The undecorated composition omits all perimeter props and their ground bed. The existing 21×13 room covers the viewport with no added floor cells or capacity. One uniform tile pitch is the larger of viewport width / 7 and viewport height / 13, so the room fills tall phones as well as shorter windows while keeping square tiles and undistorted sprites. Manual pointer/touch, wheel and keyboard pan, saved view recovery and resizing use actual rendered room bounds. Garbage interaction never changes the camera: selection highlights the object in place, the popup shows its full matching preview, and Cancel, Back and successful Clear preserve the same view. The former centering and post-clear camera restoration are removed. Input remains shielded through the 260ms removal transition; focus returns without browser scrolling afterward. The entrance/backdrop and its attached lanterns remain part of the restaurant. No new artwork or model changes are needed.

The remaining sections describe the shared behavior and the retained decorated comparison. Revision 8 captures are in `../../review/19/revision-8/`.

## Corrections and composition

Each trash object now owns exactly its registered ground footprint, rotated for its native facing. The old 3×3 / 4×4 surrounding clearance regions are removed. A deterministic authored packing contains **41 individual objects** in the two future panels: broken sofas, cars, shelving, new mustard armchairs and new low honey-wood cabinets. The ordinary occupied masks cover 131 cells exactly once; the visible covered 3×3 dock is separate. Nothing stretches a model or grants an invisible surrounding clearance area. Source sprites retain their entire calibrated frame and ground-root registration; sprite height can rise above its ground cells. Pointer/touch selection reads actual rendered sprite alpha in depth order, including raised artwork, while stable named buttons preserve keyboard access.

The screen retains the current cream coin/Editing capsules, Edit/Live control, continuous square floor and current back wall. The accepted composition has no perimeter decor; the historical Decor comparison uses decor objects alone along the left edge. The Live/Edit camera keeps a fixed tile pitch while panning, with the viewport-fit scale described above. Native model roots sit at their footprint centers. Opening the clearance card highlights that object in place and shows the same maple shell: title, matching whole-object preview, Cancel and priced Clear only. Nothing is baked into a shared text/image composite.

In the historical Decor comparison, the actual left boundary has a continuous outer bed, staggered depth lanes, varied native facings, exposed rock faces, attached crevice foliage and separated potted plants, crates, barrels, lanterns and sign. The corner wraps into the bottom edge; right and bottom edges also have independent dressing. Roots and physical silhouettes stay outside usable floor, entrances and panel connections. The user requested removal of the side wall in revision 3 and then accepted removal of all perimeter dressing in revision 5. Normal states now omit both the props and bed. There are no decorative walls at panel or viewport divisions.

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
| Floor / backdrop | Existing floor and `RestaurantBackdrop` | 21×13 continuous floor, top three rows are backdrop; square cells and fixed world roots; left side wall removed |
| Dock / Workshop | Existing separate floor, cover, sub, hut | Covered 3×3 platform is separate from ordinary trash; every side/corner neighbor must be cleared to reveal both targets |
| Blocked submarine toast | Existing People/chef notice material in CSS, live HTML text | Below the HUD; polite status; no focus/input interception; 3.2-second dismissal and refreshed duration on repeated attempts |
| Historical perimeter comparison | Native rockery variant + current plants, slate, barrels, crates, lanterns, sign | Only shown in Decor comparison; independent registered props, neutral mechanics; normal states omit the dressing |
| Trash variety review | Reused maple/cream component family | Five models × four native facings, footprint labels in review chrome, scrolling and direct access to shared clearance preview |
| Edge comparison | Live scene beside the full original ImageGen target | Side-by-side on wide windows; Target/Objects toggle on phone; preserves the same saved scene/camera |
| Edit inventory | Current continuous maple dock and Blender goods | Working categories/scroll, separate four-stool placement fixture; other goods link to the existing Shop review |

`world-registration.json` binds exact consumed bytes, source hashes, measured visible bounds, full logical frame, root, facing and model footprint. `prepare-assets.py` extracts unchanged production facings and retains approved variant records; it never re-renders or retouches approved models. `source-assets.json` records UI references and model lineage. Existing UI textures and surfaces are reused; all new raster targets use the built-in image generation tool.

## Behavior and data boundary

`balance.js` holds the fixed packing, per-object prices, prototype economy and decor placements. `model.js` owns clearing, pause, placement, save/restore and capacity transitions. Inspection, Cancel/Escape/browser Back and Clear preserve the current camera; outside taps keep the card. Repeat input cannot pay twice. Edit pauses earnings; clearing persists across reopening. Newly freed ordinary cells accept placement. Capacity/arrival potential depend on cleared ordinary floor area, not empty cells; reserved dock cells never accept inventory placement. The dock's nine visibly covered cells are separate from the access car's six-cell clearance mask and do not become hidden extra trash area.

The new masks use an isolated v2 review save key; incompatible old rectangular-region saves reset only in this prototype. Current partial saves are preserved and re-evaluated by the complete surrounding-trash rule. Native installed saves remain untouched. The seven required objects total 820 coins at unchanged prices. With 120 starter coins, 50 provisional 14-coin sales fund all seven; tests verify a reachable clearance sequence while the dock remains covered. The approved native integration now validates actual service, arrival routing, staff limits and save migration; its controlled starter funds the seven objects after 194 simulation seconds / 54 real sales. See `../../review/19/native/`.

The external review selector includes Edge comparison, Trash variety, Restaurant, Clearance, Edit, Not enough coins, Dock opened, Starter earnings and Shared components. Reset replaces only this review fixture. The real scene supports touch/pointer pan, wheel/Shift-wheel and arrow keys. The comparison and variety labels are review controls, not added game controls.

## Reference contract and approval

Applicable catalog sections: **1–2 and 15** for square-grid objects, footprints and materials; **3–5 and 8** support the reused HUD, action states and popup family. Current B/maple amendments and current native #18 UI supersede historical wireframe materials. Revisions 3–5 supersede the wall/perimeter treatment, revision 7 removes automatic centering, and revision 8 requires every surrounding trash object. Current captures are in `../../review/19/revision-8/`.

The user approved the deployed revision-8 prototype and explicitly requested native Godot implementation. That approval milestone is fulfilled; [native delivery](../../review/19/native/README.md) contains the signed release and verification. Issue 19 remains open for user verification.

The 0.11.2 feedback amendment shades only unreachable trash sprites and the unrevealable cover, with no tile tint. Blocked trash stays tappable and says “Clear trash beside the open floor first.” The cover hint and accessible name do not identify the hidden destination. Eligible objects brighten as adjacent space is cleared; affordability remains in the existing confirmation. See [native feedback evidence](../../review/19/native/blocked-feedback/README.md).

The 0.11.3 confirmation amendment supersedes automatic uncovering: all seven neighbors only make the cover ready. Tap it to see “reveal?” with Cancel/Reveal, no preview or price. Confirming saves the reveal, plays the existing native roll-up and removes the whole cover/frame. Pending readiness survives reload; old already-revealed progress remains revealed. See [native confirmation evidence](../../review/19/native/reveal-confirmation/README.md).
# Proposed Exhibition Unlocked amendment

The new post-reveal popup composition and state inventory are recorded in [the amendment brief](../../review/19/exhibition-unlocked/brief.md). It reuses the approved shared maple/cream controls and adds separately generated underwater concept art. This amendment awaits prototype approval before native integration; the earlier approved revision-8 and native 0.11.3 contracts remain historical implementation evidence.

