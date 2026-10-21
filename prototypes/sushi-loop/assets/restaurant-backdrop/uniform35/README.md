# Wood backdrop with uniform lighting

[Open the current catalog](https://6ad83979c722d341e3175395--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library).

Latest wireframe revision. Promoted into the production catalog and Godot game after user approval.
The current room uses three blank walls, the entrance, then blank walls.
Earlier captures below record the original centered lighting study. [Editable Blender project](source/restaurant-backdrop-35.blend).

- Restore the earlier wall's honey-wood color, **#C6A267**.
- Add a continuous wooden baseboard and cap, matching the gate's wood palette.
  Wall and gate segments share the same profiles. No built-in windows or extra posts.
- Use a uniform ambient albedo pass across the complete backdrop: no lower-half
  darkening, cast shadows, spot lighting or 135% contrast grade baked into sprites.
  A subtle, direction-free view-normal tone of at most 4% preserves facet readability
  on non-wall surfaces; the wood wall field has constant color.
- Retain flat angular roof tiles, the native 35° orthographic character camera,
  square pixels, four-tile gate, two-tile opening and three-tile projected height.
  PNGs keep their complete authored frames, 3× capture and transparent padding.

The wireframe defaults to **Wood wall · even light** and the Godot capture defaults
to **Even ambient**. Optional lantern lighting is gentler: energy 0.12 per lantern
rather than the preceding 0.40. The earlier variants remain available for comparison.

The isolated Godot proof uses the current assembled PNG, full even CanvasModulate
ambient, and two optional PointLight2D nodes. No production scene, game scripts,
UI, save data or game assets are modified. Pixel checks verify independent dimming.

`geometry-audit.json` verifies native dimensions, flat roof slabs, the baseboard,
undecorated wall and equal colors at three wall heights. `camera.json` records the
registered camera crop and lantern centers. `render-receipt.json` and
`provenance.json` retain source and output hashes.

Build through Blender MCP with `source/build_backdrop.py`, which creates an isolated
study and preserves other scenes. Render and verify in a separate Blender process:

```sh
blender -b source/restaurant-backdrop-35.blend -P source/render_backdrop.py
blender -b source/restaurant-backdrop-35.blend -P source/audit_backdrop.py
python3 source/test_lighting.py
```

The reusable one-tile wall and centered gate cover the reserved top three rows.
Other scene object roots start at row three. Future wall decorations remain separate.
