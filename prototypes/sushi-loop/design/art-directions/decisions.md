# Art revision decisions — issue 33

Decision checkpoint: 2026-10-18. Status: the three choices below are **locked by the user for the next asset revision**. Selection is not the same as production rollout: wait for the user's explicit instruction before updating the full asset library. Issue 33 remains open until the user approves the game-scene assets.

## Three locked decisions

| ID | Decision | Exact meaning | Current implementation |
| --- | --- | --- | --- |
| ART-01 | **70% environment front/height** | Preserve square ground tiles and their X/depth pitch. Project vertical height at 0.70 of the earlier environment baseline: `screenX = anchorX + cellSize*x`; `screenY = anchorY + cellSize*depth - 0.70*cellSize*height`. This is a projection coefficient, not a 70° camera, changed tile aspect, reduced physical model height, or a squeeze of finished PNGs. | Verified in the frozen [projection study](../../assets/projection-study/README.md); full production recapture pending. |
| ART-02 | **125% character size** | Use a true uniform native root scale of 1.25 relative to the B/C study's 100% base. Do not interpret this as another 25% increase over an already enlarged sprite. Ground root, camera and logical pixels per tile stay fixed. | Selected in the [character study](../../assets/character-scale-study/README.md); production characters not replaced yet. |
| ART-03 | **C / Chunky character proportions and revised head** | Use C as the proportion reference: chubby body, short leg stubs, tiny unobtrusive feet, full side depth, softened cheeks/chin and a less cubic face. Use the revised rounded crown, overlapping curls and fuller temple/back/nape hair volume. B remains a comparison reference, not an alternate selected production shape. Preserve each character's identity, costume and hair type when translating the proportions to the cast. | Native C revision 3 at 125%, retained at commit `a3d2a2d4c147d1b6347635e520a5a8cc0a48af7a`, is the accepted shape/scale reference. Other characters and animations await the authorized full pass. |

Reference: [live character study](https://deploy-preview-34--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?v=a3d2a2d&ntl-drawer-state=hidden#character-scale-study). At the selected scale, C is approximately **1.576 tiles tall including the hat**, with a conservative **0.814 × 0.814 tile turning envelope** across four cardinal views. Those are measurements of this chef reference, not required identical dimensions for every character or accessory.

## Existing constraints to carry forward

- **Characters keep the ordinary 35° orthographic camera**, with square pixels and no environment projection stretch. This is a retained camera constraint, not an additional character-size change.
- **One-cell character width and ground footprint.** Feet are anchored at the tile-center ground root. Head/hat may rise above the cell and overlap the row behind; horizontal extent and ground occupancy stay inside one cell. Keep collision, art bounds and support attachment points separate.
- **Minimal feet and short legs.** No return to the rejected bulky shoes. Preserve planted contacts when poses and animations are rebuilt.
- **Scene composition:** current restaurant and underwater review scenes use seven columns in portrait; preserve that review framing. The entrance is four tiles wide. Dense 2×4 and 3×3 decoration clusters can pack individual elements off-grid inside a registered cluster footprint. These are existing composition choices, not new universal object-size rules.
- **Connected assets and layering:** conveyor pieces must join with matching decks/edges and supports under their actual shapes; demonstrate straight–corner connections and connected wall runs. Food rides above belt surfaces. Character seats, hands and food must match explicit support points after the projection/scale change.
- **Source and review workflow:** retain editable Blender projects and reproducible capture sources in the repo; use registered high-resolution transparent captures; keep the concept art visible as reference. Recheck all four directions, repeated tile arrangements, interacting neighbors and animations. Earlier animation request remains at least six distinct frames per animation; the established capture timing is 12 fps.

## Still to resolve before the full asset pass

These are review topics, not newly approved changes:

1. **Lighting and shadow treatment.** Working direction: keep floor-contact shadows and broad ambient lighting adjustable in Godot rather than permanently baking them into every color sprite; retain useful internal form shading. Exact shadow strength, softness, occluders and optional auxiliary maps are not locked. This does not assume a shader can infer full 3D ambient occlusion from a color sprite.
2. **Environment finish and scene coherence.** Review the 70% projection with representative furniture, conveyors, terrain and dense decoration clusters together, including materials, color balance and how tightly the scene is dressed. The projection choice alone does not approve every existing mesh or material.
3. **Interaction fit at the selected settings.** Validate C at 125% beside the 70% belt, seated on stools and next to counters/doorways before applying the change to every animation. Recalibrate deck, seat, hand and held-item attachments; do not inherit the old height offsets blindly.

Do not infer authorization to remodel or recapture all assets from this decision record. Continue recording choices and small explicitly requested studies; begin the full production update only when the user sends it off. Scope remains issue 33 and eventual Godot Android delivery.
