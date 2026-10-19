# Art revision decisions — issue 33

Decision checkpoint: 2026-10-18. Status: the four choices below are **locked by the user for the next asset revision**. Selection is not the same as production rollout: wait for the user's explicit instruction before updating the full asset library. Issue 33 remains open until the user approves the game-scene assets.

## Four locked decisions

| ID | Decision | Exact meaning | Current implementation |
| --- | --- | --- | --- |
| ART-01 | **70% environment front/height** | Preserve square ground tiles and their X/depth pitch. Project vertical height at 0.70 of the earlier environment baseline: `screenX = anchorX + cellSize*x`; `screenY = anchorY + cellSize*depth - 0.70*cellSize*height`. This is a projection coefficient, not a 70° camera, changed tile aspect, reduced physical model height, or a squeeze of finished PNGs. | Verified in the frozen [projection study](../../assets/projection-study/README.md); full production recapture pending. |
| ART-02 | **125% character size** | Use a true uniform native root scale of 1.25 relative to the B/C study's 100% base. Do not interpret this as another 25% increase over an already enlarged sprite. Ground root, camera and logical pixels per tile stay fixed. | Selected in the [character study](../../assets/character-scale-study/README.md); production characters not replaced yet. |
| ART-03 | **C / Chunky character proportions and revised head** | Use C as the proportion reference: chubby body, short leg stubs, tiny unobtrusive feet, full side depth, softened cheeks/chin and a less cubic face. Use the revised rounded crown, overlapping curls and fuller temple/back/nape hair volume. B remains a comparison reference, not an alternate selected production shape. Preserve each character's identity, costume and hair type when translating the proportions to the cast. | Native C revision 3 at 125%, retained at commit `a3d2a2d4c147d1b6347635e520a5a8cc0a48af7a`, is the accepted shape/scale reference. Other characters and animations await the authorized full pass. |
| ART-04 | **Layered, full-footprint tile decoration with varied heights** | Use continuous restaurant ground/floor tiles or ocean-bed tiles beneath separate decoration sprites. Each decoration tile must substantially occupy the full width and depth of its cell, with a broad readable mass rather than a small centered prop surrounded by padding. Keep tile-based assembly; vary the decoration silhouette, composition and height across neighboring cells. | Direction locked; ground variants, decoration meshes and height families remain to be designed and reviewed before the full asset pass. |

Reference: [live character study](https://deploy-preview-34--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?v=a3d2a2d&ntl-drawer-state=hidden#character-scale-study). At the selected scale, C is approximately **1.576 tiles tall including the hat**, with a conservative **0.814 × 0.814 tile turning envelope** across four cardinal views. Those are measurements of this chef reference, not required identical dimensions for every character or accessory.

## Existing constraints to carry forward

- **Characters keep the ordinary 35° orthographic camera**, with square pixels and no environment projection stretch. This is a retained camera constraint, not an additional character-size change.
- **One-cell character width and ground footprint.** Feet are anchored at the tile-center ground root. Head/hat may rise above the cell and overlap the row behind; horizontal extent and ground occupancy stay inside one cell. Keep collision, art bounds and support attachment points separate.
- **Minimal feet and short legs.** No return to the rejected bulky shoes. Preserve planted contacts when poses and animations are rebuilt.
- **Scene composition:** current restaurant and underwater review scenes use seven columns in portrait; preserve that review framing. The entrance is four tiles wide. Existing 2×4 and 3×3 cluster studies remain historical references, but large repeated decorated patches are not the primary continuity solution. ART-04 now governs decoration: continuous ground plus full-footprint tile-based objects. Optional larger compositions can reuse those pieces. These scene dimensions are existing composition choices, not new universal object-size rules.
- **Connected assets and layering:** conveyor pieces must join with matching decks/edges and supports under their actual shapes; demonstrate straight–corner connections and connected wall runs. Food rides above belt surfaces. Character seats, hands and food must match explicit support points after the projection/scale change.
- **Source and review workflow:** retain editable Blender projects and reproducible capture sources in the repo; use registered high-resolution transparent captures; keep the concept art visible as reference. Recheck all four directions, repeated tile arrangements, interacting neighbors and animations. Earlier animation request remains at least six distinct frames per animation; the established capture timing is 12 fps.

## Decoration design contract (ART-04)

- **Ground first:** floor/ground and ocean-bed tiles make a continuous foundation under decoration. Keep the ground layer independently reusable; do not bake an isolated rectangular platform into every rock, plant or coral sprite.
- **Fill the tile in both ground axes:** author the decoration's mass across its one-cell width and depth. Do not achieve a nominal one-cell measurement with a tiny extremity while the main shape remains sparse. This refers to the modeled footprint and coverage, not fitting a PNG's alpha bounds or making every silhouette a solid square. Natural contour notches and small gaps can reveal the continuous ground beneath.
- **Tile-based objects are the building blocks:** a tile can contain one broad rock formation or a deliberately composed grouping of coral/vegetation and supporting smaller forms. The grouping should read as a substantial decoration tile, not scattered miniature props. Small accent props can remain separate supplements; they do not substitute for full-footprint primary decoration.
- **Vary height as well as outline:** prepare low, medium and tall forms, with different top profiles and asymmetrical groupings. Exact heights, family counts and distribution are still review choices. Keep the 70% environment projection fixed so height variation comes from the authored geometry.
- **Connected without a repeated bundle:** neighbors share compatible ground/boundary joins, while silhouette, height and internal arrangement vary. Avoid reusing one complete garden at a fixed interval or synchronizing the same sequence on both sides. Do not require every adjacent top to have the same height to achieve continuity.
- **Preserve readability:** depth-sort above the common ground with registered roots; taller decoration may overlap scenery behind it. Keep gameplay lanes, interaction targets and the visible collision boundary readable. Ground coverage, artwork height and collision remain separate.
- **Approval views:** compare a dense 3×3 arrangement and a longer connected edge with a corner at phone size, including mixed heights and repeated source pieces. Judge coverage, seams, repetition and actor occlusion together. These views are the proposed validation for the next authorized study, not an instruction to start the full asset update now.

## Still to resolve before the full asset pass

These are review topics, not newly approved changes:

1. **Lighting and shadow treatment.** Working direction: keep floor-contact shadows and broad ambient lighting adjustable in Godot rather than permanently baking them into every color sprite; retain useful internal form shading. Exact shadow strength, softness, occluders and optional auxiliary maps are not locked. This does not assume a shader can infer full 3D ambient occlusion from a color sprite.
2. **Environment finish and scene coherence.** Review the 70% projection with representative furniture, conveyors, terrain and ART-04 layered decoration tiles together, including materials, color balance, height ranges and representative arrangements. The decoration architecture and full-footprint coverage are now locked; the individual designs remain subject to visual review. The projection choice alone does not approve every existing mesh or material.
3. **Interaction fit at the selected settings.** Validate C at 125% beside the 70% belt, seated on stools and next to counters/doorways before applying the change to every animation. Recalibrate deck, seat, hand and held-item attachments; do not inherit the old height offsets blindly.

Do not infer authorization to remodel or recapture all assets from this decision record. Continue recording choices and small explicitly requested studies; begin the full production update only when the user sends it off. Scope remains issue 33 and eventual Godot Android delivery.


## Decoration height experiment — pending review

After the full-tile density patch, the user requested taller decorations and specifically encouraged 3–4 tile projected heights. The decoration study now compares the original, a moderate 1–1.6 tile set, and a bold set: rock 1, coral 1.8, column 2.5, kelp 3, peaks 4 projected tiles. The 70% camera and one-cell X/Y footprints are retained. These numeric bands are experimental, not locked; full production remodeling still awaits the user's go-ahead. Review evidence: `../../review/33/decoration-study/heights/README.md`.


### Height construction correction

User feedback supersedes the stretched height experiment: raise the supporting rock base; keep coral, kelp and other decoration at their original proportions on top. Rock crowns should be broad and relatively flat, rather than pointed. The updated study keeps the previous total projected heights to isolate this construction change. The numeric heights are still pending approval. The current page compares corrected raised bases with the original low patch; previous stretched variants remain historical only. Evidence: `../../review/33/decoration-study/rock-bases/README.md`.


### Living ledges and camera hypothesis — pending visual review

Follow-up feedback clarifies the desired direction: broad but uneven rock crowns, compact kelp/coral distributed on lower, middle and upper ledges, varied coral colors, and dark lower rock faces graduating toward bright tops. The living-ledges study implements these traits in native geometry and materials.

The user hypothesized a lower camera for objects covering more than two vertical tiles. The study compares the same geometry in the established 70% oblique profile and ordinary 35° orthographic profile. Its experimental mixed rule uses the S-facing complete reference silhouette (>2 tile heights), with square floors and fixed world roots. This camera exception is not locked and does not supersede ART-01 for production. The preserved original concept is visual guidance, not proof of a specific camera or angle. Evidence: `../../review/33/decoration-study/living-ledges/README.md`.
