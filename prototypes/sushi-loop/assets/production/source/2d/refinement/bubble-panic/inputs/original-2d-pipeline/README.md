# Flat artwork and Godot world effects

The user requested native 2D art for dishes and all bubbles. The eight original
transparent raster images in `generated/` were created through separate built-in
ImageGen calls. Exact prompts are saved in `prompts.json`. They are retained at
original resolution so later changes can use the original artwork.

`publish_2d.py` trims each input once, then packs a fixed complete canvas/root at
2× logical resolution. It creates the three dish sprites, recipe bubble variants,
happy/puzzled/panic feedback and underwater bubble trail. Bubbles retain at least
six distinct frames in each twelve-frame, 12 fps appearance, idle and fade clip.
Camera-facing sprites share the same art in all four world-facing contexts.
The empty preference balloon is composed with the same generated dish artwork;
recipe identity is not painted into a separate Blender mesh.

The five warning/current/electrical cues are flat procedural graphics. Their
editable Godot implementation is `world_effects.gd`; catalog PNGs are generated
from the equivalent Python drawing recipe for browser review. They are not
Blender objects. These effect pages review visual timing, not gameplay logic.
The GDScript parses with Godot 4.7.2 using `--headless --check-only --script`.

Run with the project's Pillow-capable Python:

```sh
python publish_2d.py                  # repack 13 objects; no manifest mutation
python publish_2d.py --merge-only --apply # merge after native publication
python audit_2d.py                    # source hashes, alpha, full frames, bounds
```

The merger removes the eight obsolete large garden clusters from the active
library, retains existing review comment IDs/storage, and declares the blackboard
and blank shop sign as one player-facing surface. It strips recipe-specific board
states because the board is now blank for dynamic content. Native source captures
for those two objects are maintained by the Blender pipeline.

ImageGen artwork already contains its painted palette and lower shading. It does
not receive an extra CSS contrast filter. Standalone world dish/bubble atlases retain the painted palette. Held sushi is a 2D textured plane inside the native character capture, so that combined character sprite receives the native 135% compositor grade; it is never graded again in the browser.
