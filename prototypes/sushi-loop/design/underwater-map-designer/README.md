# Underwater map designer · issue 21

A working browser authoring tool for the underwater tile kit. It is separate from expedition simulation and Godot saves. The current tunnel is shown schematically as the initial example; **New map** can start an empty seabed, restore that example, or load **Organic passage · 80 rows**, generated from the user’s painted opening. See `maps/README.md` for the importable JSON and design/clearance notes.

The artwork and expedition previews were reverted at the user's request. This
designer owns its example layout in `example-layout.js` and has no dependency
on those previews. Their former hosted URLs redirect here. The original concept
references and native game artwork remain independent of this authoring tool.

## Editing

The map opens at its bottom edge, including after reload, import, creating a map or resizing. Displayed row numbers count down as you look downward: the bottom is **row 1**, with row 2 directly above it and the highest row at the top. The keyboard cursor starts in the bottom-center cell; Arrow Up moves to the next higher row number, matching the submarine’s upward travel.

Choose **Obstacles** or **Decor**, then a tile. Drag to paint; sparse pointer events fill the crossed cells. **Fill** paints a rectangle. **Erase** or right-click removes only the active layer. A cell can independently contain one obstacle and one decor tile. Painting the same layer replaces its existing tile. Obstacles are collidable; decor never collides.

The palette has three generic block types: **Obstacle** (orange, `#e3a073`), **Decor** (green, `#75b8a3`) and **Gold** (yellow, `#f2c230`, chunk pickups). Empty water is blue (`#174b5b`). All obstacle variants share the same color, and all decor variants share the same color. A green corner marker indicates decor on a cell that also contains an obstacle. Layer visibility can isolate either type.

The designer renders flat square blocks and loads no world sprite images. Individual art choices, family filters and facing controls are omitted. Existing saved/imported object IDs and directions are preserved exactly in the document and JSON; new generic paint uses the representative `rock-wall-middle` / `decor-foreground-coral` IDs with South facing. **Pick** chooses the generic block type from the active layer.

**Pan** drags the map; wheel/trackpad scrolls, and Ctrl/Meta + wheel zooms. Zoom buttons and Fit view preserve the editing position. The up/down buttons move the viewport by exactly one displayed row per press at the current zoom, clamping at the map edges. On phones the palette sits below the map and can collapse. All visible controls retain 44px touch targets. The canvas uses viewport-sized rendering rather than allocating a full-length bitmap.

Undo/redo works per complete stroke, rectangle, import, new map and resize. Pointer cancellation restores the pre-stroke document. Resize crops only cells outside the new dimensions after its explicit action; Undo can restore them. Grid and layer visibility are editor settings and never delete tiles.

Shortcuts: **B** paint, **F** fill rectangle, **E** erase, **H** pan, **I** pick, **⌘/Ctrl Z** undo, **⌘/Ctrl Shift Z** or **Ctrl Y** redo, **⌘/Ctrl S** local save. With the canvas focused, arrows move the cell cursor; Space/Enter paints and Delete/Backspace erases. Escape cancels a stroke or closes a dialog. Inputs retain normal text editing behavior.

## Route chunks

Expedition runs are built from chunk maps (see `assets/expedition/route/README.md`). **New map → Route chunk · 11 × 16** starts one; **Import** opens an existing file from `godot/content/expedition/chunks/`. The palette's third block type, **Gold**, paints salvage pickups on open water. The **Route chunk** panel sets the kind (start, normal, rest, fork, finish) and an optional difficulty override, and validates live with the same rules as the game: passable at steering speed, no dead ends, reachable gold, computed difficulty. **Test in route preview** opens the expedition review with the chunk forced into a seeded run. Export the JSON over the chunk file to use it in the game; no build step is needed. The `chunk` block round-trips through import, export and local autosave.

## Local autosave and JSON

Storage key: `sushi-loop-underwater-map-designer-v1`. The current document and editor settings autosave after changes and flush at stroke completion and on page hide. Reload restores the map and zoom, then opens at the bottom edge. **Saved locally** is shown only after storage succeeds. If storage is unavailable/full, a persistent status says so while painting and JSON export remain usable. An unreadable prior payload is copied to the `-recovery` key when possible before loading the example. Storage is local to the browser and origin; there is no cloud persistence.

Use the stable Netlify draft alias **underwater-map-designer--game-prototypes-yiochen.netlify.app** for ongoing editing. Future review deployments should reuse this alias so the browser's saved map stays on the same origin. The configured site remains `game-prototypes-yiochen`, `a05448cf-3d0c-4100-9b1a-6d8a0d28c886`; production is not replaced.

**Export JSON** downloads a readable versioned map. **Import** reopens that format without a server upload, validates it before replacement, and preserves the previous document in Undo. Invalid imports leave the current map untouched. Dimensions are 3–32 columns and 8–256 rows. Displayed rows are counted from the bottom. For compatibility, saved and exported tile coordinates remain zero-based integer top-left cells: x increases right, y increases down. A displayed row number is `rows - y`; no block is moved or rewritten by the display change. One authoring row/cell is 128 logical world units; viewing zoom is not exported.

```json
{
  "format": "sushi-loop-underwater-map",
  "version": 1,
  "name": "My passage",
  "grid": {"columns": 7, "rows": 80, "cellSize": 128},
  "floor": "floor-underwater",
  "coordinates": {"origin": "top-left", "x": "right", "y": "down", "placement": "cell-top-left"},
  "layers": [{"id": "obstacles", "collidable": true}, {"id": "decor", "collidable": false}],
  "placements": [{"id": "obstacles:2:10", "layer": "obstacles", "object": "reef-middle", "x": 2, "y": 10, "direction": "S", "footprint": [1, 1]}]
}
```

IDs match the production library. Registered frame/root/footprint metadata stays in the asset catalog rather than baking pixels or sprite URLs into maps. Import rejects unknown objects, invalid directions/layers, duplicate same-layer cells and out-of-bounds/fractional coordinates. A runtime adapter can translate these authoring rows to expedition-forward coordinates; native gameplay import is not implemented by this authoring tool.

## Composition and compatibility

- `model.js` defines the two generic paint types and their colors, alongside the unchanged map schema and legacy tile validation.
- `art.js` draws only cell rectangles, grid lines, hover/fill previews, overlap markers and rulers. Its compact top margin has no raised-art padding. It does not load or draw sprites or floor textures.
- `assets/catalog.json` retains the registered catalog for compatible import/export and footprint validation. The previously extracted PNGs, provenance and `prepare-assets.py` remain as historical sources; they are not loaded by the schematic designer.
- Header, tools, passive palette, brush bar, dialogs and notices remain live HTML/CSS in the existing Nunito/maple/cream/navy family. The simplified map colors are the user's requested authoring representation and do not replace native game art.

This is authoring UI, so it uses a responsive editor workspace rather than constraining the entire tool to a portrait game screen. The stable deployment origin and local-storage key remain unchanged across this simplification.

## Verify

From the repository root:

```sh
node --test prototypes/sushi-loop/tests/underwater-map-designer.test.js
node prototypes/sushi-loop/design/underwater-map-designer/capture.mjs
npm test
npm run build
```

The browser check uses Vite on port 4177 by default; `TEST_URL` selects a built/deployed host. It verifies bottom-start views and numbering, upward keyboard painting without coordinate migration, and actual mouse/touch paint, layer separation, stroke undo/redo, rectangle fill, block picking, right-click erase, scrolled coordinates, pan/zoom, JSON download/import, invalid-import recovery, local reload, resize/undo, touch cancellation and storage-failure export. It verifies 390×844, 320×720, 844×390 and 1440×1000 layouts. Captures, a real exported JSON file and verification records are in `review/21/map-designer/`.
