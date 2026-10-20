# Sushi Loop art direction

Accepted direction: colorful low-poly game art with a square-grid environment and undistorted characters. The four images below are the current references for both scenes.

## Locked revision decisions

The [decision record](decisions.md) is the authoritative checkpoint: **70% environment front/height, 125% character scale, C / Chunky proportions with rounded cheeks and fuller layered hair, layered full-footprint tile decoration with varied heights, and Faceted Blender lighting**. Characters retain their ordinary 35° camera. On 2026-10-19 the user approved the quieter matte wood and muted-clay conveyor materials and authorized regeneration of the complete native sprite library. Issue 33 can close after the completed rollout is published and verified.

## Character proportion exploration

[Character proportions v1](character-proportions-v1.png) compares four new anatomy directions—A Compact, B Playful, C Chunky and D Super Chibi—with an illustrative redraw of the current chef. The same Lena identity and outfit are retained. These ImageGen concepts target the same ordinary 35-degree character camera; they are not calibrated or registered sprite captures. The existing native reference remains under `assets/projection-study/sprites/chef-lena/ordinary-35.png`.

The user selected **70% projected environment height** and retained the **35-degree ordinary character camera**. The locked **C / Chunky at 125%** uses minimal feet, short legs, rounded cheek/chin corners and the fuller hair from native character-study revision 3. The version-12 native project translates these choices across the cast while preserving character identities. Historical comparison captures remain unchanged. Exact concept prompt, reference roles and SHA256 values are retained in [the generation record](sources/character-proportions-v1.json).

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
- Characters use the selected compact, chubby C proportions, softly rounded cheeks/chin, fuller layered hair, minimal feet, tiny expressive eyes and mouths, and clear gestures. Retain readable low-poly costumes while avoiding a cubic face or flat hair cap. Faces, sushi and reactions must remain readable at phone size.
- Restaurant: pale cream square floor tiles, warm matte wood, muted-clay and charcoal conveyor belts, warm golden lantern accents, bright food and clothing accents, and angular green plants. Conveyor rails use sRGB `#966B60`; crate wood retains its warm hue at the approved lower linear albedo. Other wood colors, including conveyor legs, retain their original albedo under the Faceted lighting. Frame expansion areas with subdued slate rocks, crates and construction details while leaving aisles clear. Dining stools are backless.
- Underwater: turquoise floor and water, cobalt/navy rock walls, pale broken columns, bright pink/purple coral and green kelp, with a warm yellow submarine and blue window. Keep hazards and the route distinct from decorative scenery.
- UI uses clean cream or scene-colored rounded panels, crisp icons, dark rims and restrained depth. Strong outlines belong primarily to UI and facial details. Actual HUD controls and backing surfaces follow the accepted wireframes, even where a catalog shows another example.

## Environment projection

Use **square top/front oblique projection** for floors and objects: conveyor modules, furniture, architecture, crates, rocks and other environment pieces. Canonical coordinates are `(x, depth, height)`, with positive depth toward the viewer and height upward. One ground unit is one logical cell.

```text
screenX = anchorX + cellSize * x
screenY = anchorY + cellSize * depth - 0.70 * cellSize * height
```

- Floor cells are screen-aligned squares with equal horizontal and vertical pitch. Parallel edges stay parallel, with no distant shrinkage, vanishing-point convergence or diamond-grid rotation.
- Grid-aligned top planes retain their true shape. Front-plane vertical lengths use the selected 0.70 factor: a unit top remains square, while a unit front becomes 0.70 cell tall. Front planes are no longer true-shape squares.
- Height moves artwork straight upward over the row behind its footprint. It does not change the logical cell size or ground root.
- The end-on side plane can collapse. Do not force a conventional isometric third face onto aligned objects. Other face orientations and rounded volumes have no true-shape guarantee.

For a 3D capture, apply the selected 0.70 profile in the native camera/projection before rendering, preserving square ground cells. Use the verified 70% camera and calibration receipts; do not stretch finished sprites. The earlier 45-degree / sqrt(2) profile in stored concept-source records is the historical 100% baseline, superseded by the version-12 recapture. Tall concept decoration uses the documented upper35/square-footing exception when its complete 70% silhouette exceeds two tiles. In Blender Z-up coordinates, canonical `x = X`, `depth = -Y`, and `height = Z`; in Y-up coordinates, `depth = Z` and `height = Y`.

## Undistorted characters

Characters use a separate **ordinary orthographic art camera**, with square pixels and no vertical stretch. The selected elevation is **35 degrees**, retained from the approved study. Keep its scale and camera fixed across poses and animations.

Place character art using the environment's projected ground roots and logical cell scale. Standing feet meet their floor root. Seated hips meet an explicit stool-seat support point, with hands and food aligned to the serving surface. Preserve natural head, body and limb proportions rather than applying the environment stretch to people. The environment projection distorts rounded anatomy (the historical 100% profile made spheres sqrt(2) times taller than wide), which is why the character exception matters. Any additional ordinary-orthographic exception for a rounded prop should be recorded explicitly.

Keep footprint, support/collision, art bounds, ground root and visual height separate. Tall art may overlap neighboring rows without occupying those cells. Do not infer collision or seat placement from a sprite's bounding rectangle, or fit each pose independently into its frame.

## Geometry and generation sources

- [Historical environment projection profile](sources/projection.json): original 100% affine matrix, axis conventions, top/front examples and sphere limitation. For the selected next revision, use ART-01 and the 70% native study receipts.
- [Character registration](sources/character-registration.json): separate character-camera guidance and floor/seat attachment points for the restaurant composition.
- [Restaurant geometry guide](sources/geometry-guide.svg): authored square grid and furniture top/front planes. Its cyan crosses and orange dots are planning markers, not final artwork.
- [Generation prompts](sources/generation-prompts.json): exact built-in imagegen prompts for the four final references, including relevant refinements and historical input roles.

The stored restaurant guide uses 112-pixel cells on a 1024 × 1536 concept canvas. These are composition values, not a locked runtime resolution. Generated concepts can approximate geometry; use the authored profile and registered assets for exact joins and attachments in production. Historical input names remain inside verbatim prompts for provenance; superseded studies, non-low-poly references and intermediate image renders have been removed.

## Tile-based decoration

The [locked ART-04 decision](decisions.md#decoration-design-contract-art-04) uses continuous restaurant ground/floor tiles or ocean-bed tiles beneath separate decoration objects. Each primary decoration tile should substantially fill its full cell width and depth; avoid small centered objects floating in empty tile space. Use broad rocks or composed vegetation/coral groups with natural silhouettes, layered above the common ground.

Vary low, medium and tall forms, top profiles and internal arrangement across neighboring cells while preserving compatible boundary joins. Continuity comes from the shared ground and connected forms; variation comes from the tile objects. Large repeated 2×4 or 3×3 patches are removed from the active catalog. Small accent objects may supplement the full-footprint pieces. Keep complete decoration silhouettes below three projected tiles across every facing. Individual designs remain subject to the user's visual approval.

## Lighting and shadow separation

Reserve floor-contact shadows, broad ambient shading and scene lighting for the Godot renderer. Keep these effects separate from reusable color sprites so characters, furniture and scenery share one adjustable lighting setup. Start with inexpensive soft contact-shadow layers for the Android target; use selective 2D lights and authored occluders where needed.

Subtle shading within an object can remain in its art to describe faces, bevels and crevices. A color sprite alone does not provide the geometry needed for accurate three-dimensional ambient occlusion. If stronger dynamic surface lighting is required, export registered normal/specular or occlusion data from Blender using the same camera, frame, facing and animation samples. Existing native previews contain rendered form shading; they are not claimed to be pure albedo or to include auxiliary lighting maps.

The wireframe scene review should establish a coherent seven-column portrait composition and readable native silhouettes. Runtime shadow work does not replace the character proportion, acting, material and environment-shape refinements still needed to approach the concept art.

Godot implementation reference: [2D lighting and shadows](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html), including authored occluders and optional normal/specular maps via CanvasTexture.


### Universal production finish (approved 2026-10-19)

Every Blender object follows [ART-05 through ART-09](decisions.md#authorized-production-rollout--2026-10-19), as amended by [the selected Faceted finish](decisions.md#selected-faceted-lighting--2026-10-19): native 135% sRGB contrast, material-driven darker lower surfaces (including restaurant objects), matte Principled surfaces, a centered 140 W overhead area light and four equal 100 W cardinal fills. These lights separate top planes from sides without a preferred horizontal direction. The approved crate-wood material adjustment applies to the crate; muted-clay rails apply to all conveyor modules. Do not add a browser contrast grade.

The former zero-light emission treatment remains historical only. Retain the 70% environment camera, selected C125 cast, concept-specific full-footprint decorations, height-dependent decor camera and maximum three-tile complete decoration silhouette. Use ImageGen 2D sushi/bubbles and procedural 2D current/eel effects. The full-library recapture is authorized; its publication and validation are recorded in [the Faceted rollout review](../../review/33/faceted-rollout/README.md).

## UI reference workflow (ART-10, approved 2026-10-19)

For **every ticket that adds or changes UI**, inspect the unchanged [Restaurant UI & item catalog](restaurant-item-catalog.png) before drawing controls. Its stable review page is [Restaurant UI & item catalog](https://game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#concept-doodle-catalog). For expedition work, inspect the [underwater item catalog](underwater-item-catalog.png) and [underwater concept](underwater-concept.png) as well; restaurant-derived shared controls retain one consistent vocabulary across modes.

1. Read the ticket's relevant current wireframe scenes and shared component pages alongside the catalog. Record which numbered catalog sections guide each affected control, surface, icon or state. The wireframe governs behavior, control set, composition and accessible names; the catalog governs visual finish. Its illustrative branding, sample values, Map/Settings/level controls and T/cross junctions add no requirements.
2. Reuse approved production UI artwork where it fits. Generate missing or substantially revised UI artwork through **ImageGen**, using the catalog image and relevant existing approved assets as explicit references. Do not substitute arbitrary vector glyphs, generic engine buttons, wireframe dashed placeholders or unrelated stock art for the requested catalog-derived finish. Preserve a transparent restaurant HUD; a catalog panel does not authorize adding HUD backing.
3. Keep dynamic labels, prices, counts, status and badges separate from reusable artwork. Save the actual ImageGen output, exact prompt, reference paths/hashes and generation provenance in the repository. Put runtime assets in the game's asset tree, retain clean alpha and sufficient pixel resolution, and use deliberate scalable framing or padding so text and touch targets remain crisp. Baked sample text and reference-sheet crops are not production controls.
4. Implement the relevant **normal, pressed, disabled and selected** states, plus NEW/MAX/badge states where specified. Derive state treatment from the catalog: warm beveled material surfaces and crisp dark rims, readable icon relief and highlights, inset press feedback, a restrained selection accent, and visibly muted disabled controls. Keep icons, text and hierarchy readable over actual gameplay; preserve at least 44 px touch targets and accessible names/focus/system Back.
5. Reuse the same UI presentation in gameplay and the **native Shared component/gallery**. Capture affected states over their full scene on a narrow phone and a wider window with portrait containment; check pressed/disabled/selected behavior, clipped or overlapping labels, icon contrast and touch targets against the original references. Update the ticket's review evidence before marking the UI complete.

For issue #12, use sections **2, 5, 6, 8 and 14** to finish the accepted editor controls, layer stack, compact roster/inventory paging rails, selection Rotate/Remove controls and brief placement feedback. Catalog wood/cream surfaces guide controls only where the wireframe calls for a surface; top-right Live and transparent fixed HUD remain in their accepted positions. People/Layout/Floor behavior, two inventory items or three profiles per page, edge carets and the absence of Save/Done/Cancel/Undo/page numbers remain unchanged.
