# Seven-column portrait scene review

Final authored cameras: restaurant[0,0,7,13], underwater[0,0,7,14]. Native sprite scale and source PNGs are unchanged. The camera deliberately cuts border overhang; the central composition was rebuilt for seven columns rather than zooming the old map.

Focused browser review passed in9.05seconds: both scenes at390px phone,844px landscape and1440px desktop; twelve desktop timeline positions and four positions per smaller viewport; native image decoding, stable camera, no pending sprites, no page overflow or nested vertical scrollers. Measured tile pitch:52.3px phone,110px landscape and115.1px desktop. Prior phone fit was24.7px restaurant/21.7px underwater because full sprite canvases expanded the fitted bounds.

The existing five showcase tests passed in21.8seconds after adding persistent actual-viewBox/896px camera assertions. They include playback, scrubbing, root/grid controls, Fit/2× pan, route links and phone document touch scrolling.

Actual screenshots were inspected for entrance framing, food above the conveyor, diner/stool contact, chef boards, June's full walking route and bank/actor occlusion. The eel's short East/West turns were additionally captured at5.25s and17.25s; both clear the native cliff faces. Native topology/577-frame attachment checks are owned by the coverage agent and reported separately.

Remaining native-art differences are visible at this larger scale: recipe boards appear as edge-on easels instead of reference worktables; the models/materials remain flat and faceted. Ambient/contact shading is deferred to Godot, as requested. No CSS shadow or new asset baking was introduced.

Representative final evidence: restaurant-phone-t0.png, underwater-phone-t0.png, restaurant-desktop-t0.png, underwater-desktop-t24.png. Complete route sheets: restaurant-route-sheet.png and underwater-route-sheet.png. Exact measurements and image counts: report.json. Scripts are in../seven-columns/.


The shared renderer accepts an authored camera rectangle in world cells only for composed scene views. Individual object pages keep full capture bounds. Persistent browser assertions verify 896 logical pixels across the camera, equivalent to seven 128-pixel cells. The scene topology audit checks all 16 conveyor modules, both continuous wall/bank assemblies and their projected off-camera end rings; paired moving effects retain their native ground roots through all facings.

This is a framing/composition revision. The native 125-object library, editable Blender project and sprite sheets are unchanged. Remaining art priorities include proper chef prep tables (the current recipe-board asset is an easel), stronger character proportions/expressions/poses, varied broad environment silhouettes, quieter floor values and richer shared material colors. Ground-contact shadows and broad ambient lighting are planned as Godot runtime effects; no shadow layer or auxiliary normal/occlusion atlas was generated in this pass. Final asset approval is still pending and issue #33 remains open.
