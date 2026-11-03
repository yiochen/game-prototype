# Underwater map designer · review evidence

[Open the map designer](https://underwater-map-designer--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/underwater-map-designer/). This is a stable draft alias on the configured game-prototypes Netlify site. Keep this hostname for subsequent editor updates so local browser saves remain on the same origin. Production is not replaced.

Implemented: 30 registered obstacle/decor types and all authored cardinal facings, independent obstacle/decor painting, continuous strokes, rectangle fill, layer-specific erasing, right-click erase, rotation, eyedropper, undo/redo per stroke, scroll/pan/zoom, viewport rendering, map name/dimension editing, new/example maps, resize/crop with undo, local autosave, JSON download and validated JSON import. No native gameplay or save integration is claimed.

Model checks: **7 passing** checks in `tests/underwater-map-designer.test.js`, including independent cell layers, sparse stroke interpolation, clipped rectangles, exact export/import roundtrip, invalid import rejection, resize semantics, registered art, example map validity and a maximum supported dense map fitting inside its own import limit.

Build: `npm run build` passes. The existing chunk-size warnings remain. Last full repository engine run: **225 passed / 2 failed** before adding the separate maximum-map check. Both failures are the same untouched historical refinement fixture failures: `belt-straight-n/candidates/round-09/consumer/.godot/.gdignore` and `coin-pop/final/original-catalog-object.json` in `tests/refinement-rollout.test.js`.

Browser verification: `design/underwater-map-designer/capture.mjs` tests actual mouse/touch authoring, undo/redo, fill, cardinal direction, overlapping layers, layer-only erase, eyedropper, map scroll coordinates, pan and zoom without edits, actual JSON download, valid/invalid import, local reload restoration, resize undo, cancelled touch rollback and storage/quota failure with working export. It also verifies 390×844, 320×720, 844×390 and 1440×1000 layouts, 44px buttons, page containment and palette collapse. `verification.json` records the checked host. The same workflow is run against the deployed alias.

Visual inspection caught and corrected compact touch targets and compressed tile thumbnails. Final palette buttons preserve full thumbnail height; world tiles preserve square grid pitch, original frames and registered roots. The landscape default zoom keeps several rows usable, and the narrow portrait palette can collapse to enlarge the playfield. `exported-map.json` is an actual browser-downloaded authoring document, not a hand-authored fixture.

The source README documents the schema, zero-based top-left coordinates, local-storage key, shortcuts, source hashes and exact first-frame asset preparation. User maps stay in their browser and can be backed up with Export JSON; the export contains tile IDs, integer cells, facing, footprint, grid and explicit collision-layer semantics.

## Schematic block revision

The user requested color coding without distinguishing individual decor. The current designer therefore has exactly two generic paint options: orange Obstacle and green Decor, with blue empty water. A green corner marker keeps both layers legible when they share a cell. No world sprites, sprite thumbnails, asset family filters or rotation controls are used by this view. Previously saved tile variants and facings survive unchanged in local storage and JSON; new paint uses representative compatible IDs.

The updated browser workflow verifies the exact canvas colors, that different decor IDs have the same color, that no world sprite images are requested, that the palette has only two choices, and that legacy data survives reload unchanged. Painting, fill, layer-only erase, block picking, undo/redo, JSON, autosave, storage failure and all four layouts are rechecked. Earlier `palette-layout` and `first-row-boulder` images are historical; the normal example/painted captures and `verification.json` describe the current color view.

## Bottom-first numbering

The user's submarine starts at the bottom and travels up. The editor now opens at the bottom on launch/reload, import, new map and resize. Rulers and cell readouts show row 1 at the bottom, 2 above it, and count down toward the starting edge. The keyboard cursor starts at bottom center and Arrow Up advances to row 2. Saved/exported positions keep their existing top-left coordinate system; the row-label mapping is `rows - y`.

The updated model/browser checks verify bottom scroll position, restoring an existing map without moving blocks, returning to the bottom after reload even if the previous view was at the top, bottom-center keyboard painting, upward row readouts, JSON compatibility and phone/landscape layouts. The `*-bottom-start.png` captures show the actual starting view.

## Row-by-row navigation

The up/down buttons now move one row per press, using the current displayed cell size rather than jumping to the map ends. Repeated presses step repeatedly, top/bottom bounds clamp normally, and navigation changes no map data. The browser workflow verifies both directions, repeated presses, bounds and zoom-adjusted distance on desktop, phone and landscape.
