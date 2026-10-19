# Selected 135% contrast — native Blender compositor proof

The user selected the 135% preview and asked how to produce it in Blender. This isolated project demonstrates the same global grade as a native render pass, retaining the direction-free materials and lighting. It is a small proof, not a production-library recapture or approval of asset shapes.

## Editable Blender setup

`native-contrast.blend` contains the complete native concept-decoration scene and an editable compositor group named with `sRGB Contrast 135`. The pipeline is:

1. Render Layers → Alpha Convert **To Straight**.
2. Convert Color Space **Working Space (`scene_linear`) → sRGB**.
3. Separate RGB. Each channel uses a clamped Multiply Add: **factor 1.35, offset -0.175**. This is `clamp((c - 0.5) × 1.35 + 0.5, 0, 1)` in display sRGB, matching the browser contrast preview. Blender's generic contrast-slider value is not assumed equivalent.
4. Combine the graded RGB with **the original Render Layers Alpha**.
5. Convert **sRGB → Working Space**, then Alpha Convert **To Premultiplied**, then the scene compositor output.
6. Export RGBA PNG with the same **Standard / None / exposure 0 / gamma 1** color-management setup as the source captures. The baked PNG is displayed without an additional contrast filter.

The working/display conversion matters because [Blender's compositor uses linear working colors](https://docs.blender.org/manual/en/5.0/render/color_management/color_spaces.html), while the browser preview grades sRGB values. [Convert Colorspace](https://docs.blender.org/manual/en/5.0/compositing/types/color/convert_colorspace.html) makes that conversion explicit. Alpha is separated from the RGB calculation to preserve coverage at transparent edges.

Keep object captures separate from shared floors and references: floors remain ungraded. The saved scene has no lights and zero world illumination; neither was changed to get the stronger result. Existing height-based lower darkening remains in the materials. A global post-render grade strengthens that existing shading; selective face/base changes can still be made in materials later.

## Reproduction and validation

`source/create_native135.py` imports the retained concept-decoration recipe, creates an isolated fresh scene, adds the compositor and saves with `bpy.data.libraries.write`. It never saves over the user's active Blender file. Run `create(NEW_EMPTY_PATH, ABSOLUTE_CONCEPT_RECIPE_PATH)` through Blender MCP. Capture using Blender CLI with the saved `native-contrast.blend`, `--python source/create_native135.py -- --capture OUTPUT_DIR CONCEPT_RECIPE_PATH`.

Four representative objects (cobalt crags, pink/violet coral, wooden planter and pale column) are captured in S/E/N/W, using each object's selected camera. There are 16 original/native pairs, 32 full 768×3072 RGBA PNGs. Source manifests/project, main recipe, images, camera receipts and evaluated capture-geometry digests are recorded in `proof.json`; the original model scene snapshot is retained under `authored/`.

`source/audit.py OUTPUT_DIR CONCEPT_ASSET_DIR` (NumPy/Pillow) verifies hashes, exact original/control pixel equality with the existing concept sprites, unchanged alpha, complete frames and native output versus the 1.35 sRGB formula. Across all 16 pairs, alpha is byte-identical, mean opaque RGB error is below 0.42 of one 8-bit channel unit, and maximum error is 1.125 units—consistent with quantizing the input and output to 8 bits. The audit is numerical evidence, not a claim that every art design is visually approved. The source scene's compositor/lighting inspection is saved as `graph-audit.json`.

The live review defaults to 135%, retains the earlier three-grade comparison, and adds a browser/native comparison with selectable object and facing. Browser side: the original control plus one 135% display grade. Native side: the baked PNG plus **no** display grade. This avoids double contrast. Both scene sets remain available, with unchanged floors, references and source geometry. Native assets beyond these proof samples remain at their original grade until the authorized full recapture.
