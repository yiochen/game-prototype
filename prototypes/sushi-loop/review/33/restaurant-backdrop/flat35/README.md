# Plain backdrop review

[Published wireframe](https://6ad8296319af3456dd6d7986--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-restaurant). Default artwork: **Plain wall · 35°**.

Native Blender revision: flat roof slabs, bright plain plaster, no wall windows or
extra posts. Gate dimensions remain four tiles outside, two tiles inside and
three tiles in projected height. Top three rows remain reserved in the wireframe.
Production Godot files, tools and approved asset library have no changes.

Validation:
- 191 engine/tooling tests passed; production Vite build passed.
- Five relevant Playwright browser checks passed, including touch scrolling and
  all lighting controls at phone, landscape and desktop sizes.
- Screenshots at 320×740, 844×390 and 1440×1000 have no page errors or horizontal overflow.
- Native Blender geometry audit verifies the 35° camera, square pixels, measured
  dimensions, transparent gutters, flat shingles and uniform plaster color.
- An isolated Godot Compatibility project captured actual independent PointLight2D
  lighting of the exported sprite. The left light can dim without changing the right.
- Published PNG hashes match the local gate, wall and all three Godot lighting captures.

`browser-checks.json`, `published-check.json` and `deploy.json` retain the receipts.
`lighting-*.png` show the website comparison controls. Native captures and pixel
measurements live under `assets/restaurant-backdrop/flat35/lighting-proof/`.
