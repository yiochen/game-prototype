# Native prop silhouette revision

Editable recipes: `assets/production/source/blender/catalog_art_revision.py` and
`catalog_corner_supports.py`. This revision supplies actual native meshes and
pose callbacks. The shared capture pipeline supplies projection, lower-surface
material gradients and the approved 135% compositor grade.

## Applied feedback

| Family | Authored change |
| --- | --- |
| Walls | Panel, horizontal boards and blue coping use square mitered corner polygons. Every straight/corner endpoint has the same native cross-section; inner corner connects W/N, outer corner W/S. |
| Angular plant | Broad tapered pot plus two tiers of folded angular leaves. Complete crown spans approximately .95 × .96 cells. Native sway moves leaf ridges without changing its ground envelope. |
| Barrel | Fourteen coopered staves use five height rings. Middle diameter .87 cells, end diameter .67; the middle visibly bulges. |
| Crate | Complete body, braces and rails span .979 × .979 cells. |
| Slate | Broad uneven crown with a full 1 × 1-cell ground envelope and contact at the front edge. |
| Dock posts/rope | .306-cell posts, .35-cell caps, .072-cell rope. Half-post boundary meshes reconstruct one shared post. Rope ends are flush to native port planes. |
| Conveyor | .13-cell-wide, .19-cell-high red rails; .16 × .16-cell legs. Moving deck geometry, UVs, phase, speed, ports and orientation remain intact. Corner legs follow the curve; inner legs move to arc fractions .30/.70 so thick supports remain inside their cell. |
| Chef board | Blank dark face, one S/player-facing capture, native geometry confined to the front .23-cell band. No recipe/chalk/food geometry. The chef can share the same ground cell. Dynamic content belongs in a later 2D overlay. |
| Blank sign | One S/player-facing capture at the front edge; .90-cell blank wood face leaves the tile center available. |
| Sofa | Full-width 1.97-cell body, dull faded upholstery, torn seat and visible stuffing; existing 2 × 2 support and clearance states. |
| Wrecked car | Muted blue-gray body, rust, bent hood/bumper and real dark cabin openings with jagged retained glass. Existing 3 × 2 support and clearance states. |
| Collapsed shelf | Full-width 1.97-cell shelves, broad fallen boards and worn colors; existing 2 × 2 support and clearance states. |
| Cobalt wall | Full-width/depth contact mass and broad uneven crown, shared native port section across middle/edge/corner/end. |
| Dock cover | A 3 × 3 overhead weather tarp for the docked submarine/workshop. Larger stitched cloth panels, rolled hems, ridge support, corner ties and a deliberate peek opening clarify its purpose. Covered/uncover remain native animations; the contextual example should show it above the dock. |

## Verification

`native-prop-geometry.json` records a no-render Blender 5.2.2 geometry smoke
check of all 19 replacement props and all 20 directed conveyor modules.

- All 39 native builds and all pose callbacks complete without errors.
- Full idle support bounds remain within their declared integer tile width/depth,
  allowing only the documented tiny bevel/strata detail overhang.
- Every straight/corner wall end section exactly matches the shared section.
- Conveyor moving deck vertex and UV hashes remain unchanged by the revision
  and by pose execution.
- Blackboard and sign expose only the S/player-facing direction; no baked
  blackboard recipe or chalk geometry remains.

This geometry check is not visual approval. Fixed-camera rendered inspection and
the user's live-site review remain required before issue #33 closes.

Reproduce without rendering or changing the user's live Blender project:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python prototypes/sushi-loop/assets/production/source/blender/validate_art_revision.py -- \
  --output prototypes/sushi-loop/review/33/full-art-rollout/native-prop-geometry.json
```
