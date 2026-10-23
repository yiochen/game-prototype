# Native refinement choices

Start with the largest visible gap. A low-poly style may need deliberate face normals; clay needs broad curvature; enamel needs a reflection environment. Not every technique belongs on every asset. Inspect actual before/after exports at use size.

## Geometry and dead spots

- Intersecting bars can create coplanar top faces and black corner patches under ray tracing. Use a continuous rim or clean non-overlapping joins, verify normals and inspect required facings. A new renderer can expose an existing mesh defect.
- Shader bevel changes shading normals, not silhouette/thickness. Real bevel/profile geometry establishes a rounded contour or wide edge band. Continuous rails need matching positions and normals at connectors.
- Flat leaves cannot gain folded volume from more specular alone. Curvature, cross-section, thickness, taper and overlap establish light-facing and turning planes. Similar reasoning applies to fabric or thin panels.
- Smooth shading can smear intended planes; flat shading can fragment a curve. Inspect orientation, smoothing boundaries, custom/weighted normals and modifier behavior. Diagnose coincident faces, reversed normals and material assignment before cosmetic compensation.

## Color, material and light

- Palette and material response interact. Warm light or reduced contrast alone can make a vivid model dull. Useful color variation may belong in the material as well as the light.
- Edge reflections need curvature/appropriate normals and something useful to reflect. Roughness, specular, coat and reflection shape interact; maximal gloss is not always closer to the target.
- Grazing reflections can wash warm material toward gray/pink. Inspect base color, roughness, reflection intensity/color and color management separately rather than recoloring the exported PNG.
- Keep contact darkness local and preserve readable turning planes through overlaps. Avoid large merged black hubs or inert patches; do not remove an intentional dark material just because it is dark.
- If the brief requires no preferred horizontal light direction, a broad overhead source and horizontally symmetric world/reflection treatment can supply depth. Do not reintroduce per-view corrections. Directional light is valid when permitted.

## Capture and modular assets

Retain the established camera, frame, pixel aspect, world scale and root. Follow project conventions for rotating a common root. Record actual Blender values; inspect node types instead of localized names and check supported RNA/enums.

Matching connector geometry alone cannot certify seam-free alpha compositing. Assemble independently captured tiles at runtime pitch as well as rendering a connected scene. Check silhouette, UV/material/normal continuity, alpha cut edges and lighting across joins. A measured render-only overlap can address an antialias gap if the runtime supports it and logical ports/UV travel remain correct; no universal overlap amount or painted seam repair.

For motion inspect playback, representative frames, contacts and loop boundaries. One connected still cannot certify every independently exported animated tile combination. State exactly which combinations were checked.

Discover the installed Blender executable/interfaces rather than assuming a machine-specific path. Prefer isolated processes or restore live-scene inspection state. Keep source/recipe versions and resource dependencies; pack new resources into the edited copy where appropriate, never by resaving the untouched original.
