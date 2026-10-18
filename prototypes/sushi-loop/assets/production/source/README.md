# Editable issue #33 Blender source

[blender/sushi-loop-world-library.blend](blender/sushi-loop-world-library.blend) is the editable native Blender project. It contains the Sushi33 production scene and its dependencies; the unrelated scene originally open on the user's computer was preserved. Enable an asset collection in the Outliner to inspect it. Each collection contains a separate ground root, modeled meshes, materials, and source metadata. Native belt material actions use 12 fps. Character rigs and actions are added with their export batches.

The companion Python builders are the authoring source executed through Blender MCP. Actual camera matrices are recorded in `records/<id>/camera.json`. Environment capture uses 512 source pixels per world unit at 4× scale for X, depth, and height. Runtime atlases uniformly sample the complete captures to 2× logical resolution, without alpha fitting or changes to pose framing. People and declared rounded food use a separate ordinary orthographic camera at 35° elevation.

`registered/` retains whole-frame layout guides and source SHA-256 hashes. Original 4× capture PNGs and redundant packed control sheets are retained locally in their guide folders and omitted from Git to avoid duplicating render intermediates. Representative unchanged native frames are versioned in `validation/`; runtime 2× atlases are versioned in `../sprites/`. Editable geometry, material nodes, camera records, action definitions, and deterministic builder recipes remain versioned for future iteration.

Each published object page offers the GitHub source reference and a direct `.blend` download. Open the file in Blender, select the object's collection, and use its recorded camera and action to inspect the native geometry or motion. The object's manifest `source` entry identifies its modeling script, camera record, capture guides, and asset record.

The website imports only the runtime `sprites/**/*.png` atlases. Source captures and the `.blend` file remain outside its client bundle. This is a native Blender review pass: final scene-art approval and any surface refinement remain pending, and issue #33 stays open.
