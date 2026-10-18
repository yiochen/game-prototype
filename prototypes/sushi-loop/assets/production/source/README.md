# Editable issue33 Blender source

`blender/sushi-loop-world-library.blend` is the real, editable native Blender project. It contains only the Sushi33 production scene and its dependencies; the unrelated scene that was open on the user machine was preserved. Enable an asset collection in the Outliner to inspect it. Each collection has a separate ground-root object, modeled mesh/material parts, and source metadata. Native belt material actions are retained at12fps; character actions/rigs are added with their export batches.

The companion Python builders are the exact authoring source executed through Blender MCP. Cameras use the recorded actual matrices in `records/<id>/camera.json`. Environment calibration is512source pixels/unit at4× capture for X,depthandheight; final atlases are uniformly sampled to2× logicalresolution with no alpha fitting. People and declared rounded food use a separate ordinary orthographic35°camera.

`registered/` retains whole-frame layout guides and source SHA256 hashes. Original4×capture PNGs and redundant packed control sheets are retained locally inside their guide folders but omitted from Git to avoid duplicating render intermediates. Representative unchanged native frames are versioned in `validation/`; runtime2×atlases are versioned in `../sprites/`. The editable geometry, material nodes, camera records, action definitions and deterministic builder recipes are versioned for future iteration.

The website imports only `sprites/**/*.png`; none of these source controls or the blend file are included in its client bundle. This is a native Blender review pass. Final scene-art approval and any surface-refinement pass remain pending; issue33 stays open.
