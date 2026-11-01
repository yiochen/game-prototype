# Issue 20 · Floor painting UI review

Interactive HTML/CSS review of the current maple inventory dock with cosmetic floor painting. This is the approved standalone design reference; its preview data remains separate from Godot saves. The native implementation is recorded in `review/20/native/`. The review storage key is `sushi-loop-floor-ui-review-v1`.

## Composition and states

Reuse the existing full-width square room, registered ground-root sprites, cream coin/Editing pills, vermilion Live action, continuous maple category dock, walnut Shop and carved-wave footer. Floor has a horizontally clipped row of caption-free 2×2 pattern thumbnails; four complete choices and a hint of the next are visible on a normal portrait phone. A walnut inset and small dot mark the selected brush. No item quantities apply to unlimited patterns.

Centered scene copy reads exactly **select a tile pattern** before selecting a brush, then **paint the floor**. Palette touches and scrolling keep the instruction visible. Touch/pointer down outside the palette hides it until release/cancellation. Bare cream scene-edge carets have independent 44px targets; press-and-hold pans without painting. Disabled directions stay muted. The round cream X above the dock clears only the brush. Active Floor toggles palette collapse and retains the brush. Escape closes Shop, clears the brush, then collapses the palette.

Brush mode fades furniture/characters/covered landmark to 28% opacity; trash remains identifiable at 65%. Taps and interpolated strokes paint eligible square cells, including beneath furniture; trash footprint cells are skipped. A blocked trash stroke provides a short cream notice. Clearing trash belongs to issue 19 and is not performed by the brush. Camera, painted floor, owned patterns and coins persist in isolated preview storage. Scene-edge panning reaches the floor initially obscured by the dock.

The Shop uses the approved maple shell, beige inset catalog, shared round X and floating bag return. It demonstrates one optional Blue Wave offer, a 2×2 pattern preview, 600-coin purchase, brief named toast, persistent Owned state and disabled insufficient-coins action. A purchase stays in Shop, debits once and prepends the unlimited style to the palette. Adjacent supplies are passive context from the existing Shop; stock rotation, balance and game integration remain outside this design review.

Review toolbar fixtures: choose pattern, painting, painted floor, Shop offer, Owned, insufficient coins, Shared components. Reset only resets this preview. The gallery reuses the same PatternSample, pattern button, caret and SharedClose components; normal, pressed, selected and disabled states remain inspectable.

## Asset and layer map

| Piece | Source | Bounds, anchor and resizing |
| --- | --- | --- |
| Room sprites and trash | `../expansion-preview/assets/` with its `world-registration.json` | Original measured frame, ground root, 128 units/cell and depth order. Uniform scaling only; pointer-transparent. |
| Restaurant backdrop | `wireframe/restaurant-backdrop.jsx` | Existing SVG at 21×3 square-cell extent. |
| Maple grain / waves / Nunito | `../editor-dock-preview/assets/` and `shared.css` | Existing approved dock. Repeated grain, clipped wave footer, native text and CSS corners; no stretched composite. |
| HUD, tabs, Shop shell, round X | Existing dock, Shop and `SharedClose` CSS/React | Code geometry; labels and state remain live, fixed corner radii and 44px hit targets. |
| Cream, Blue Wave, Harbor Check | Existing production floor sprites, URLs in `patterns.js` | Square repeat at one cell, 2×2 repeat in previews, no image distortion. |
| Jade Check, Terracotta, Plum Petal, Linen Stripe | Deterministic CSS in `style.css` | Quiet geometric review variants. Same pattern component and cell extent in palette and world. No new raster artwork or ImageGen output required. |
| Instruction / selection / disabled / toast | Live HTML/CSS | Pointer-transparent scene copy, unclipped dynamic text, CSS state styling and existing cream notice family. |

The current dock amendment supersedes the historical B curtain/pagination layout. Inspected references: current native issue 19 Edit capture, accepted B composition, restaurant world concept and unchanged restaurant item catalog, especially sections **1–2** (square grid), **5** (states) and **15** (quiet environment patterns), plus **3–4, 8, 14** for reused HUD, Shop and notice surfaces. Older `restaurant-floor` and `component-editor-controls` wireframes supply feature context; issue 20's updated scroll/caret/instruction rules take precedence over their historical pagination and no-instruction copy.

## Verification

Run `node prototypes/sushi-loop/design/floor-paint-preview/capture.mjs` against Vite on port 4177, or set `TEST_URL`. It asserts observable touch/wheel/focus selection, instruction hiding, sparse stroke continuity, painting under furniture, trash exclusion, scene panning with brush retention, collapse, brush exit/opacity restoration, reload persistence, Shop purchase/Owned/disabled and return focus/scroll. Captures and measurements: `review/20/floor-prototype/` at 320×720, 390×844, 844×390 and 1440×1000.

The user approved this deployed composition and explicitly requested Godot integration on 2026-10-31, including the amendment that instructions stay visible while scrolling the palette. Native code uses `floor_book.gd`, `floor_pattern.gd` and `floor_presentation.gd`, with integration in the shared editor, Shop and restaurant renderer.
