# Native Blender backdrop at 35°

Wireframe comparison only. Godot and the approved production library are unchanged.

[Open the published Blender / ImageGen comparison](https://6ad824637a111147e27dc479--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-restaurant).

Open [the editable Blender project](source/restaurant-backdrop-35.blend).
The gate, plain wall, window wall and complete seven-tile assembly are separate
collections. Meshes, roof tiles, joinery, cloth panels, the white fish curves and
faceted lanterns remain editable. The original ImageGen art is a design reference;
these exports are native Blender renders without an ImageGen reskin.

- Ordinary orthographic camera at **35° elevation**, zero yaw, square pixels,
  exactly the character camera convention. No 70% environment projection or
  finished-sprite stretch.
- One world unit per tile; **4-unit outer gate and 2-unit clear inner aperture**.
  Wall modules are one unit wide. Four ceramic roof tiles per unit preserve the
  same roof profile and detail pitch across gate/wall joins.
- One common **three-tile projected registration**. Native mesh Z is calibrated
  before capture; small corner bevels can trim less than one logical pixel off
  a wall's silhouette. Roof depth is included in the projected height.
- The approved native Faceted light rig, matte material treatment, darker lower
  surfaces and 135% sRGB contrast run in Blender. Renders use 256 EEVEE samples.
- Full transparent captures retain a 32-logical-pixel gutter on every side.
  Camera frames are 576×448 for the gate and 192×448 for each wall, captured at
  3×. The wireframe uses the authored camera content rectangle at a shared
  128 px pitch; it never fits alpha bounds or stretches the native PNGs.

`camera.json` records the full frame, registered viewport, actual camera world
matrix and measured unit projections. `geometry-audit.json` records the evaluated
native aperture/width/height, measured elevation and transparent frame edges.
`render-receipt.json` records model, recipe and PNG hashes.

Rebuild via Blender MCP using `source/build_backdrop.py`; it creates one isolated
study scene and preserves existing scenes. Capture and verify in a separate
Blender process:

```sh
blender -b source/restaurant-backdrop-35.blend -P source/render_backdrop.py
blender -b source/restaurant-backdrop-35.blend -P source/audit_backdrop.py
```

The builder reuses this repository's `prop_builders.py`, `catalog_style.py` and
`catalog_faceted.py` without editing them. The renderer finalizes a normal `.blend`
with the study and gate camera active, so the project opens ready for inspection.

In the wireframe restaurant scene, **Backdrop → Blender · 35° / ImageGen** switches
both the full scene and the standalone asset study. The native assembly expander
shows a single complete Blender render independently of sprite compositing.
