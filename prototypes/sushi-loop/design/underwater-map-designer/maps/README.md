# Turquoise passage · Organic 80

`turquoise-passage-organic-80.json` is a version 1 map accepted by the designer's existing Import action. The website also offers it under **New map → Starting point → Organic passage · 80 rows**. A `?preset=organic-80` link opens that existing creation dialog without replacing the current local draft; Cancel keeps the draft, Create map loads the preset with Undo available. Download JSON in the dialog returns the exact file.

The user's reference is retained unchanged in `sources/turquoise-passage-user-reference.json`. Its first 25 progress rows (stored y 55–79) are preserved exactly, including both layers, object IDs, directions and footprints. Rows 26–80 replace the old straight-wall/template continuation.

The opening remains deliberately light: rows 1–8 contain only 10 obstacles across 56 cells. The extension uses moving two-/three-cell passages with wider shoulders at turns, an island fork at rows 36–38, wider recovery pockets, a long connected cliff with changing edge depth, a late slalom and an open finish. Tight sections require lateral steering; no single column remains open through each such section.

Decor grows in irregular clusters on and immediately beside obstacle masses, rather than at a fixed every-other-row cadence. Every new obstacle has decor on itself or within one neighboring cell; every new decor cell accompanies an obstacle. Kelp and two coral families vary in patches and facings in the data; the designer continues to show all decor using the same green code, as requested.

Regenerate deterministically from the source and authored profiles:

```sh
node prototypes/sushi-loop/design/underwater-map-designer/maps/generate-organic-80.mjs
```

Verification:

```sh
node --test prototypes/sushi-loop/tests/organic-passage-map.test.js
node prototypes/sushi-loop/design/underwater-map-designer/maps/verify-organic-80.mjs
```

`TEST_URL` selects the deployed host. Browser checks cover real file import, exact export roundtrip, preserving/restoring the previous draft through Cancel and Undo, preset download, preset selection, local save/reload and four viewports. The link query is removed after Create/Cancel so reopening the saved map does not replay the preset dialog.

Independent geometric checks in `analyze-passage.mjs` find a continuous route for the current preview's 0.64×0.88 collider. The new extension also passes with a larger 0.8×1.6 footprint and a lateral-change bound of three cells per forward row. These are clearance checks, not a native gameplay/balance playtest.

`review/21/organic-80/` holds the four-panel SVG/PNG overview, stage counts, input hash, actual website captures and browser verification. Read each overview panel bottom-to-top, then continue to the next panel. Display row 1 is at the bottom; JSON retains the designer's compatible top-left coordinates.
