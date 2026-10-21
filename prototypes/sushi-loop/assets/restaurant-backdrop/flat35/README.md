# Plain Blender backdrop at 35°

[Open the current wireframe preview](https://6ad8296319af3456dd6d7986--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-restaurant).

Current wireframe revision. The production Godot game and approved asset library
remain unchanged. Open [the editable Blender model](source/restaurant-backdrop-35.blend).
The source contains separate gate, plain wall and seven-tile assembly collections.

- Flat closed roof slabs and an angular ridge cap; no rounded shingles.
- One plain plaster surface, without window recesses, extra wall posts or trim.
  The two structural entrance jambs remain part of the gate. Windows and paintings
  can later be placed as separate decorations.
- Bright, uniform plaster albedo. The height-dependent darkening and baked cast
  shadows are removed from the wall face. Roof and joinery retain faceted shading.
- Ordinary orthographic camera at 35° elevation, zero yaw, square pixels and the
  character camera convention. Four-tile gate, two-tile clear opening, one-tile
  wall and three-tile projected height. No finished-sprite projection stretch.
- Full transparent PNGs retain 32 logical pixels of padding; capture scale is 3×,
  with a registered 128 px tile pitch. The wireframe uses the fixed content viewport.

`geometry-audit.json` measures evaluated model dimensions and checks the absence
of wall decorations, eight-vertex roof slabs and identical plaster colors at three
heights. `camera.json` also records the projected lantern centers.
`render-receipt.json` and `provenance.json` record native source and output hashes.

## Native Godot lighting proof

The page includes actual Godot captures for even ambient light, both lanterns
on, and the left lantern dimmed. These use Sprite2D, CanvasModulate and two
independent PointLight2D nodes in the same Compatibility renderer as the game.
No normal map, bloom or post-process is needed to brighten the flat wall sprite.
Blender's uniform-albedo material is baked into the PNG; the Godot Sprite2D is
light-receiving, not an unshaded CanvasItem material.

`source/test_lighting.py` makes a temporary isolated Godot project, imports only
the assembled PNG and camera metadata, captures the three states, measures wall
pixels and removes the temporary project. `lighting-proof/lighting-check.json`
verifies that each light brightens the sprite and left dimming leaves the right
wall unchanged. This is an isolated proof, not a change to the production game.
Normal maps can later add directional surface response; shadow casting would
require separately authored occluders.

Rebuild the model through Blender MCP with `source/build_backdrop.py`; it preserves
other live scenes. Render and audit in a separate Blender process, then rerun the
isolated Godot proof:

```sh
blender -b source/restaurant-backdrop-35.blend -P source/render_backdrop.py
blender -b source/restaurant-backdrop-35.blend -P source/audit_backdrop.py
python3 source/test_lighting.py
```

The wireframe defaults to **Plain wall · 35°**. The earlier Blender and ImageGen
families remain selectable for comparison. The top three tile rows stay reserved
for the backdrop; scene object roots start at row three.
