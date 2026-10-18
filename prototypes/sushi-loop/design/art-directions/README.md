# Sushi Loop art direction

Accepted direction: colorful low-poly game art with a square-grid environment and undistorted characters. The four images below are the current references for both scenes.

## Final references

| Scene | Theme concept | Item catalog |
| --- | --- | --- |
| Restaurant | [restaurant-concept.png](restaurant-concept.png) | [restaurant-item-catalog.png](restaurant-item-catalog.png) |
| Underwater expedition | [underwater-concept.png](underwater-concept.png) | [underwater-item-catalog.png](underwater-item-catalog.png) |

The restaurant concept is the approved hybrid-projection image, preserved unchanged. The underwater concept was extracted and completed with imagegen from the right-hand gameplay example in the underwater catalog. The restaurant catalog includes UI states, characters, dishes, conveyor modules, furniture and scenery; the underwater catalog includes obstacles, scenery layers, grid rules and an assembled level example.

Concepts establish the scene treatment. Catalogs establish the visual vocabulary. Their sample titles, HUD values, extra controls and belt junctions are illustrative; the [spec](../../docs/spec.md), [art presentation requirements](../../docs/art-direction.md) and current wireframes govern gameplay and screen controls. These references are not production sprite sheets.

## Visual style

- Build forms from chunky, angular low-poly geometry with broad, readable facets, simple bevels and matte surfaces. Use flat shading, gentle ambient occlusion and soft grounding shadows.
- Keep surface detail sparse. Favor shape and color over painted texture, grain, fine engraving or smooth clay-like modeling. Scene objects use faceted silhouettes rather than heavy ink outlines.
- Characters have compact blocky bodies, angular hair and hats, tiny expressive eyes and mouths, and clear gestures. Faces, sushi and reactions must remain readable at phone size.
- Restaurant: pale cream square floor tiles, honey-brown wood, red and charcoal conveyor belts, warm golden lantern light, bright food and clothing accents, and angular green plants. Frame expansion areas with subdued slate rocks, crates and construction details while leaving aisles clear. Dining stools are backless.
- Underwater: turquoise floor and water, cobalt/navy rock walls, pale broken columns, bright pink/purple coral and green kelp, with a warm yellow submarine and blue window. Keep hazards and the route distinct from decorative scenery.
- UI uses clean cream or scene-colored rounded panels, crisp icons, dark rims and restrained depth. Strong outlines belong primarily to UI and facial details. Actual HUD controls and backing surfaces follow the accepted wireframes, even where a catalog shows another example.

## Environment projection

Use **square top/front oblique projection** for floors and objects: conveyor modules, furniture, architecture, crates, rocks and other environment pieces. Canonical coordinates are `(x, depth, height)`, with positive depth toward the viewer and height upward. One ground unit is one logical cell.

```text
screenX = anchorX + cellSize * x
screenY = anchorY + cellSize * depth - cellSize * height
```

- Floor cells are screen-aligned squares with equal horizontal and vertical pitch. Parallel edges stay parallel, with no distant shrinkage, vanishing-point convergence or diamond-grid rotation.
- Lengths and angles remain true within grid-aligned top and front planes. A unit top and a unit front each project to a square. A short object can have a square top and a shallow rectangular front.
- Height moves artwork straight upward over the row behind its footprint. It does not change the logical cell size or ground root.
- The end-on side plane can collapse. Do not force a conventional isometric third face onto aligned objects. Other face orientations and rounded volumes have no true-shape guarantee.

For a 3D capture, use a 45-degree orthographic environment view with a **sqrt(2) vertical projection stretch**, applied in the projection or pixel aspect before capture. Do not stretch finished sprites. In Blender Z-up coordinates, canonical `x = X`, `depth = -Y`, and `height = Z`; in Y-up coordinates, `depth = Z` and `height = Y`.

## Undistorted characters

Characters use a separate **ordinary orthographic art camera**, with square pixels and no vertical stretch. About 35 degrees elevation is a starting example, not a mandatory recovered camera angle. Keep its scale and camera fixed across poses and animations.

Place character art using the environment's projected ground roots and logical cell scale. Standing feet meet their floor root. Seated hips meet an explicit stool-seat support point, with hands and food aligned to the serving surface. Preserve natural head, body and limb proportions rather than applying the environment stretch to people. A sphere under the environment projection becomes sqrt(2) times taller than wide, which is why the character exception matters. Any additional ordinary-orthographic exception for a rounded prop should be recorded explicitly.

Keep footprint, support/collision, art bounds, ground root and visual height separate. Tall art may overlap neighboring rows without occupying those cells. Do not infer collision or seat placement from a sprite's bounding rectangle, or fit each pose independently into its frame.

## Geometry and generation sources

- [Environment projection profile](sources/projection.json): affine matrix, axis conventions, top/front examples and the sphere limitation.
- [Character registration](sources/character-registration.json): separate character-camera guidance and floor/seat attachment points for the restaurant composition.
- [Restaurant geometry guide](sources/geometry-guide.svg): authored square grid and furniture top/front planes. Its cyan crosses and orange dots are planning markers, not final artwork.
- [Generation prompts](sources/generation-prompts.json): exact built-in imagegen prompts for the four final references, including relevant refinements and historical input roles.

The stored restaurant guide uses 112-pixel cells on a 1024 × 1536 concept canvas. These are composition values, not a locked runtime resolution. Generated concepts can approximate geometry; use the authored profile and registered assets for exact joins and attachments in production. Historical input names remain inside verbatim prompts for provenance; superseded studies, non-low-poly references and intermediate image renders have been removed.
