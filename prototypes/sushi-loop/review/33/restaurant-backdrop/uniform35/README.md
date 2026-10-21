# Uniform wood backdrop review

[Published wireframe](https://6ad82c663b6fca86a2c0b538--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-restaurant). Defaults: **Wood wall · even light**, **Even ambient**.

Restores the earlier wall color #C6A267 and adds a continuous wooden baseboard.
All native backdrop surfaces use uniform ambient albedo, with no height darkening,
cast shadows or strong contrast grade. Small 4% normal tones preserve facets on
non-wall forms. Flat roof slabs and the measured 4/2/3-tile gate dimensions remain.

Validation:
- 192 engine/tooling tests, five relevant Playwright checks and Vite build passed.
- Phone 320×740, landscape 844×390 and desktop 1440×1000 screenshots checked.
- No page errors or horizontal overflow; all four artwork variants work.
- Blender front, side and three-quarter inspection plus final-camera renders checked.
- Geometry audit verifies uniform wall color and the continuous baseboard.
- Actual Godot Compatibility captures default to full even ambient light. Optional
  lantern energies are reduced from 0.40 to 0.12 and remain independently adjustable.
- Published PNG hashes match local gate, wall and all three native lighting captures.
- Production Godot files, tools and approved asset library have no changes.

See `browser-checks.json`, `published-check.json` and `deploy.json` for receipts.
Editable model, camera, material sources and provenance remain in
`assets/restaurant-backdrop/uniform35/`. Earlier review families are preserved.
