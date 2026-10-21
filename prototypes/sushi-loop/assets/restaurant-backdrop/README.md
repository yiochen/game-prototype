# Restaurant backdrop study

[Open the current catalog](https://6ad83979c722d341e3175395--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library).

The latest preview defaults to [wood walls with uniform lighting](uniform35/README.md):
the original honey-wood wall color, a continuous wooden baseboard and flat angular
roof tiles. Strong directional shadows and height darkening are removed throughout
the backdrop. The optional Godot lantern comparison starts with even ambient light.
Earlier Blender and ImageGen variants remain selectable on the same scene.

The approved uniform-light gate and wall are now in the production catalog and
Godot game. The layout uses three blank walls, the entrance, then blank walls
across the remaining world width. Integration evidence is in
[`../../godot/review/33/backdrop/`](../../godot/review/33/backdrop/). Earlier study evidence is in
[`../../review/33/restaurant-backdrop/uniform35/`](../../review/33/restaurant-backdrop/uniform35/).

## Earlier ImageGen family

Wireframe scene preview only, awaiting visual review. Godot remains unchanged.

The former `entry-finished` model and its active sprite exports have been retired.
The new artwork follows the user's original restaurant concept, preserved as
[`original-concept-reference.jpg`](original-concept-reference.jpg).

| Asset | Projected dimensions | Use |
| --- | --- | --- |
| [`raw/gate.png`](raw/gate.png) | 4 × 3 tiles; centered 2-tile opening | Restaurant entrance facade |
| [`raw/wall-plain.png`](raw/wall-plain.png) | 1 × 3 tiles | Repeating honey timber wall |
| [`raw/wall-window.png`](raw/wall-window.png) | 1 × 3 tiles | Matching lattice window variation |

The earlier family below was generated with the built-in ImageGen tool. The complete original
PNGs retain their alpha and source pixels. No source crop or finished-sprite
projection stretch was applied. The first gate draft is retained as history.
[`generation.json`](generation.json) records every exact prompt, source/reference
hash and original output path.

The wireframe uses one 128 px square cell, reserves rows 0–2 for this wall plane,
and starts object ground footprints at row 3. The gate is centered in the
seven-column scene. Wall modules continue underneath it so silhouette notches
cannot expose holes. The wall is drawn before the scene's ordinary depth-sorted
sprites; their raised art can overlap the backdrop naturally.

Review the [published wireframe assembly](https://6ad81d990c927c86992eaa16--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-restaurant); enable **Tile grid** to inspect pitch,
and use **Fit / 2× / 4×** for detail. The section below the full scene shows the
unobstructed assembled wall and links to each original image. Existing 3D entrance
exports remain available in the object library.

Validation: 190 engine/tooling tests, five scene browser tests, production build,
and screenshots at 320×740, 844×390 and 1440×1000. Evidence is in
[`../../review/33/restaurant-backdrop/`](../../review/33/restaurant-backdrop/).
