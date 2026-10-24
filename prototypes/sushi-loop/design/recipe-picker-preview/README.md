# Issue 15 — wood recipe picker HTML review

Open the existing wireframe site:

- Clean interactive phone: `/prototypes/sushi-loop/?recipe-ui=1`
- Studio with review-state controls and Comments: `/prototypes/sushi-loop/#recipe-wood-review`
- Clean state examples: add `&state=eligible`, `current`, `new`, `unavailable`, `unknown` or `idle` to the clean phone URL.

The current game's **continuous maple wood board** governs this design. It reuses the exact inventory dock's grain, wave texture and Nunito font, with cream recipe cards and rounded wood depth. The noren composition does not govern this revision.

## Composition and interactions

`wireframe/recipe-maple.jsx` and `recipe-maple.css` own the shared panel and tile presentation. Existing picker stories and the recipe-tile gallery reuse it; the recipe award also reuses the dish compositor. The studio's new wood-review page provides all six review fixtures. Clean mode uses the same components with mock state isolated from the older studio fixtures.

**Plate and sushi are separate HTML layers.** `raw/plates.png` contains empty White/Yellow/Red/Blue/Black plates. `raw/food.png` contains sushi only plus an unidentified silhouette. Each is an unchanged 3×2 sheet with square cells. CSS selects one cell per layer and places the uniformly sized sushi over its plate. No precombined dish image is rendered. The earlier `raw/dishes.png` experiment is superseded and retained as source history.

The catalog scrolls independently of fixed details/Prepare. The details surface spans the popup’s full inner width with rounded top-left/right corners; content and Prepare retain 20px side padding. Cookable recipes sort by descending tier, followed by discovered ineligible recipes, then unknown recipes. A walnut inner outline marks current production; a brighter cream background marks inspection; both cues can appear on the same tile. NEW clears on inspection, including when ineligible. Unknown dishes have no price. Ineligible recipes show a dash for time and disabled Prepare; the current eligible recipe shows noninteractive Preparing.

Prepare commits an eligible choice in the mock preview, closes the panel and updates the preview blackboard. Close or Escape preserves current production. Reopening returns to the current recipe. Outside taps do not dismiss or activate the restaurant. Keyboard focus is contained while open; actions retain at least 44px targets. Reduced motion removes the short panel entrance. Review controls are outside the game surface.

This is a design prototype for review, not native Godot integration or an economy/save simulation. Fixture prices/timings are illustrative and do not change balance. State persists during this mounted preview; reloading resets the fixture. The chef portrait and restaurant sprites are existing project art.

## Source and checks

The complete screen brief and surface/state inventory are in `brief.md`. Full ImageGen originals, exact prompts, reference hashes and generation provenance are preserved in `generation.json` and `raw/`. Built-in ImageGen was used; no API/CLI fallback.

The Vite build passes. Browser checks cover 390×844, 320×720 and 1280×720: layout containment, catalog scrolling, independent plate/food DOM layers, NEW clearing while ineligible, disabled/unknown states, prepare→close→reopen, idle chef and Escape. Native implementation and final design approval remain pending under #15.

## Current headshot and popup refinement

The current profile family is generated with ImageGen in the supplied concept-art style. It is shared across inventory/roster, applications and profile UI. In the recipe header, the chest begins at the separator and the headshot extends above the popup's upper border; a separate rounded interior frame clips the catalog and footer. Full-width details retain rounded top-left and top-right corners. Inspection lights the tile background while current production retains its walnut marker.

The gallery at `#chef-ui-portraits` compares all eight headshots and dialog crops. [Current artwork and generation records](../../assets/ui/chef-headshots/v1/README.md). Earlier Blender front captures remain identity/source history; in-scene sprites keep their native presentation.
