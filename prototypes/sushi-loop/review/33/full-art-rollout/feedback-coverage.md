# Final request coverage and source provenance

The final catalog contains **117 active objects: 104 native Blender objects,
eight ImageGen 2D objects and five procedural 2D effects**. All 104 native runtime
entries reference the frozen version-12 project
`c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`.
Required state IDs resolve to published clips, every clip runs at 12 fps, and
declared facings match the exported artwork. The blackboard and sign are S-only.
No request-coverage blocker was found. User visual approval remains pending;
issue 33 must stay open.

## Pasted feedback

| Item | Actual version-12 implementation and evidence |
| --- | --- |
| 1 | All four reaction bubbles and ambient bubbles use retained transparent ImageGen originals in `source/2d/generated/`, with prompts and fixed-frame 2D atlases. No active native bubble records remain. |
| 2, 13 | Chef blackboard is blank, S/player-facing only, modeled in the front tile band, with no baked recipe tokens. Its interaction shares the chef cell and uses a foreground overlay. |
| 3, 4 | Inner/outer wall corners use matching native miter sections, including panel, boards, cap and coping. Each interaction includes correctly oriented straight neighbors. Native section tests cover the revised profiles. |
| 5 | Angular plant has a broad pot and dense layered leaf crown spanning the cell width/depth; the mesh audit measures its complete support. |
| 6 | Barrel staves use five real radius rings: approximately .87-cell middle versus .67-cell ends. |
| 7 | Crate body, end rails and braces span approximately .979 × .979 cells. |
| 8 | Blank shop sign is S-only, modeled at the front tile edge, and shown sharing a planted tile. Dynamic text is not baked. |
| 9 | Slate rock has a broad uneven crown and full one-cell footing, including its front edge. |
| 10 | Dock posts are approximately .306 cells thick and rope .072 cells thick. Matching half-posts join at tile boundaries. |
| 11, 12 | All 20 directed belt modules have .13-cell-wide red rails and .16-cell leg sections. Curved legs remain below the curve. Connected fixtures include straight/corner joins and separate staged food travel; deck UV flow remains native and animated. |
| 14 | All three sushi dishes use retained ImageGen 2D art. Held dishes use the same images on camera-facing planes attached to evaluated palms; sushi is not reconstructed as 3D food geometry. |
| 15 | Whole sofa spans approximately 1.97 cells of its declared two-cell width, with faded upholstery, a torn seat and stuffing. |
| 16 | Wrecked car uses muted colors, jagged retained glass around dark cabin openings, rust and bent parts. |
| 17 | Shelving spans approximately 1.97 cells of its declared two-cell width, with warped shelves and fallen boards. |
| 18 | Live catalog names the object **Dock weather tarp** and explains its 3 × 3 overhead shelter, rolled hems, ridge, ties and fold-back animation. Its interaction places it over the dock, submarine and workshop. |
| 19, 20 | Cobalt wall modules have full-cell contact mass and shared native port profiles; middle/edge/corner/end fixtures demonstrate joined neighbors. |
| 21, 22 | Lateral current and swirl use flat procedural 2D atlases with editable Godot `Node2D` drawing source. |
| 23 | Eel warning hatch is a procedural 2D strip, with direct Godot drawing source. |
| 24, 25 | Lightning and discharge have no active Blender model entries; their flat effects and animation are supplied by the Godot 2D source and review atlases. |
| 26–33 | All eight named restaurant/underwater A/B garden bundles are absent from the active catalog and both complete scene placements. Superseded records remain historical provenance only. |
| 34 | All four production floor styles have native narrow tile borders. Continuous floors remain independent of decoration. |

The modeling measurements and exact recipes are retained in
[native-prop-geometry.json](native-prop-geometry.json),
[catalog_art_revision.py](../../../assets/production/source/blender/catalog_art_revision.py)
and the source records. The [2D audit](../../../assets/production/source/2d/audit.json)
checks original image hashes, alpha and complete atlas registration.

## Locked decisions carried through

- Environment cameras preserve 128 logical pixels per ground unit and use
  89.6 pixels per vertical unit. Characters retain ordinary 35° square pixels,
  uniform 1.25 scale, C anatomy, short legs, tiny feet and fuller identity-specific
  hair. Native anatomy and knife poses fit their one-cell envelope.
- Every native object receives the scene-local 135% sRGB compositor with alpha
  bypassing RGB grading. Native world-height material tone darkens lower surfaces
  across restaurant and underwater objects. Emission surfaces, zero world strength
  and zero-energy lights eliminate a fixed directional light source.
- Tall concept decorations use the documented ordinary35 upper view/square-footing
  transition. Complete projected silhouettes stay below three tiles across facings;
  the largest independently measured concept decoration is approximately 2.585.
- Individual full-footprint pieces layer over continuous ground. The restaurant
  and underwater scenes retain seven-column framing and original concept references;
  the entrance remains four cells wide. Connected assets and support offsets use
  the revised projection. Food and front-edge signs have explicit draw order.
- Every native animated clip/facing has at least six distinct visible frames.
  Conveyors retain 24 frames over two seconds. All **9,390 native captures** pass
  the [complete pixel audit](independent-pixel-audit.json). A separate
  [runtime atlas check](runtime-atlas-audit.json) verifies all 117 objects and
  11,082 frame/facing contexts after 2× sampling, including the flat effects;
  every animated context still has at least six distinct visible frames.

Standalone 2D dish/bubble atlases retain their painted palette. Held 2D food is
inside the combined native character capture and therefore receives its native
135% grade; the browser does not grade it again. The hybrid decoration camera,
submarine's 65° exception and 2D representations are documented exceptions rather
than silent changes to the environment projection.

## Provenance and remaining limits

The canonical editable project hash matches the frozen capture project. The
native index's 312 active model/camera/rig record hashes match their files. Every
runtime source path and declared source hash resolves correctly, including
retained immutable project/recipe revisions and the original ImageGen images.
The [native audit](independent-native-audit.json) checks 104 objects, 525 used
materials and 2,580 evaluated pose/facing combinations without saving the project.

Per-rig `sourceFiles` include intermediate global script hashes recorded while
the native batch was being authored. Nine earlier versions are unavailable after
searching current scripts, local history/revision files, all reachable Git blobs
for the affected script basenames, and 110 source/backup files under 107
Sushi-named temporary entries. Their original hashes are preserved in the records.
The [availability report](intermediate-source-availability.json) lists the exact
hashes and affected records; the [bounded temporary-source search](tmp-source-recovery.json)
also found no exact matches. This limits exact reconstruction of
those intermediate authoring states; it does not invalidate the retained frozen
project or the final capture-helper provenance. Later source files are not
presented as evidence of the unavailable earlier versions.

This pass supplies editable native models/actions, 2D originals/effects and a
wireframe review catalog. It does not claim ImageGen surface refinement of every
native mesh, a completed Godot game, or an Android APK from this art-review pass.
Browser checks and structural tests support review; final aesthetic approval
belongs to the user.
