# Ribbon Ray (issue #69)

Concept model only. The creature's mechanics are not approved, so it has **no rig, no clips and no game integration** yet.

Indigo diamond ray, dashed spots, two trailing ribbons. Low-poly, flat-shaded, flat colours, in the Storm Eel and Inkfin Cuttlefish style.

- **Size:** 4.5 × 6.4 cells (X × Y), 509 / 701 vertices / faces.
- **Axes:** X right, +Y north (travel direction), Z up, 1 unit = 1 cell.
- `source/build_model.py`: run in Blender with `ASSETS` set to the `assets` folder; it uses `../creature-kit/kit.py`.
- `source/ribbon-ray.blend`, `export/ribbon-ray.glb`: the result.
- `validation/game-view.png`, `validation/three-quarter.png`: renders.
- `concept/issue-69-concept.jpg`: the issue's inspirational mock.
