# Organic 80 · generated from the user's painted opening

Open `https://underwater-map-designer--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/underwater-map-designer/?preset=organic-80`, then Create map. The existing draft remains intact until that explicit action and is retained in Undo. The same file is available from the preset dialog's Download JSON link and through ordinary Import.

The generated map is `design/underwater-map-designer/maps/turquoise-passage-organic-80.json`. It preserves every obstacle and decor placement in progress rows 1–25 of the provided `Turquoise-passage.json`; stored top-left y values remain compatible. The original is copied unchanged under `maps/sources/` with its hash in `generation.json`.

Rows 1–8 are only 18% obstacle cells; the new tight sections are around 60–62%. Rows 26–34 meander into a narrow throat, 35–40 provide an island fork and recovery, 41–50 use staggered shelves, 51–68 follow a long irregular cliff, 69–77 finish with a slalom, and 78–80 open into extraction water. Tight sections have no single straight-through open column. Wider shoulders separate narrow stretches so direction changes have space.

Decor uses irregular colonies on obstacle faces and short fringes beside them. Every new obstacle is decorated or immediately next to decor, and every new decor cell accompanies an obstacle. Kelp/coral variants and facings vary in the data while the designer keeps its single green decor representation.

`overview.svg` is the editable four-panel overview; `overview.png` is its browser-rendered 2× capture. Read each panel bottom-to-top, then move to the next. Source rows 1–25 are unchanged. `generation.json` records stage counts and hashes, and `clearance-verification.json` records independent passage checks.

Validation:

- All 4 new map checks pass; all 8 existing designer model checks pass.
- A continuous route exists for the preview collider. The extension also passes with a 0.8×1.6 footprint and a lateral-change bound of 3 cells per progress row. These are geometric checks, not a native gameplay/balance playtest.
- Browser checks verify exact file import/export, restoring the old map with Undo, preset Cancel preserving the draft, exact preset download, preset loading, bottom-start orientation, local autosave/reload, New map dropdown access and viewport containment on desktop, phone, narrow phone and landscape. `browser-verification.json` records the checked host.
- Build passes. Full repository tests: 231 passed, 2 fail because of the previously missing historical refinement fixtures in `refinement-rollout.test.js`; no new failure is introduced.

The preset URL query is consumed on Create/Cancel so reload resumes the map rather than reopening the dialog. `deploy.json` records the draft on the configured game-prototypes site; production and native Android gameplay are unchanged.
