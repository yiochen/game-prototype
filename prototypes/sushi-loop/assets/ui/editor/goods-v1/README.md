# Editor merchandise views

Six inventory thumbnails use the approved native production models and materials
from `assets/production/source/blender/sushi-loop-world-library.blend`. The user
explicitly requested Blender renders with a three-quarter merchandise view, so
these are direct native renders, without an ImageGen style pass. Their ordinary
orthographic camera has 35° elevation and 35° azimuth from front toward right,
square pixels, and native 384 × 384 RGBA canvases. Top, front and right side are
visible. Each object fills about 82% of its authored canvas dimension.

The cream floor is the sole geometry exception: a **UI-only .12-cell slab** with
a .018-cell bevel and the saved approved cream floor material. This gives the
sample visible thickness. It does not replace the flat registered world floor.
The other five models retain their production meshes and saved static transforms,
with their ground roots facing south. The wood stool remains the approved plain
wood stool; the concept's blue upholstery is not substituted.

The finish preserves the approved Faceted 140 W overhead key, four equal 100 W
cardinal fills, matte wood/clay materials, native lower-height material ramps and
135% sRGB compositor grade. There is no added browser/runtime contrast grade.
The reference composition is `assets/ui/editor/v4/raw/b-indigo-ceramic.png`;
restaurant catalog sections 10, 11 and 15 guide the goods silhouettes, while the
catalog's UI surfaces and labels are authored separately in the editor family.

`source/editor-goods.blend` contains six isolated editable camera scenes. Source
collections were appended from the saved production file through Blender MCP;
the user's active file and scene were restored after each operation, and no main
file save or production overwrite was performed. `records/captures.json` retains
camera matrices, geometric bounds, mesh hashes, material settings, lighting,
render hashes and the original production file hash.

To reproduce through Blender MCP, import `source/capture_goods.py` as a module,
call `build('/absolute/path/to/game-prototype')`, then call `render_one(art_id)`
for each of its six IDs and `save_project()`. This adds new isolated scenes and
restores the previously active scene after each operation. Never open or save
over the user's current main file. Packing is a separate Python/Pillow step:
`python source/pack_goods.py`.

The runtime atlas and manifest live at `godot/assets/ui/editor-goods/`. The atlas
packs the six complete native canvases without cropping, resizing, color changes,
or alpha masks. Each cell has four transparent padding pixels on each side.
`records/contact-sheet.png` is a review composite on a cream background, not a
runtime asset. People continue to use their approved ordinary character camera.
