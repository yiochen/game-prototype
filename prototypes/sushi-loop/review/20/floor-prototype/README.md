# Issue 20 · Interactive floor prototype evidence

Review URL: https://6ae6197257c775abb7d6fbc0--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/floor-paint-preview/

This is a draft deployment to the existing `game-prototypes-yiochen` site (`a05448cf-3d0c-4100-9b1a-6d8a0d28c886`). This deployment leaves the production web site unchanged. The user approved the prototype and requested Godot implementation on 2026-10-31; native implementation/evidence is in `review/20/native/`.

Source, composition, asset map and reproducible capture command: `design/floor-paint-preview/README.md`.

Revision: instruction text stays visible throughout palette touches and horizontal scrolling, whether a brush is selected or not. Touches outside the palette still hide it until release. The `14-palette-scroll-instruction-*` captures show an active touch-scroll in both states.

Screenshots cover 320×720, 390×844, 844×390 and 1440×1000: unselected/scrolled palette, selected brush, touch-down instruction hiding, floor painted beneath furniture, blocked trash, collapsed palette, brush exit, Shop offer/Owned/insufficient coins, new style and normal/pressed/selected/disabled shared components. `results.json` records the tested host, error collection and measured 44px touch targets.

Visual comparison used the current native #19 Edit composition, approved continuous maple dock and restaurant item catalog sections 1–2, 5, 15, with existing HUD/Shop/notice references from sections 3–4, 8, 14. The captures preserve square cells, registered sprite scale, cream HUD pills, warm wood grain, carved waves and the separate walnut Shop. Selected brush fades furniture, people and the covered landmark; trash remains legible. The phone palette shows four complete thumbnail previews and part of the next. Landscape keeps the portrait scene contained and starts with a panned floor view rather than spending its limited playfield on the entrance wall.

Validation:

- Vite production build passes; existing large-chunk advisory remains.
- All 24 existing `editor-dock-preview.spec.js` / `shop-preview.spec.js` checks pass.
- Floor-specific hosted browser/touch checks and capture measurements are in `results.json`.
- Repository engine/model suite: 216/218 pass. Two unrelated refinement provenance checks cannot open historical files: `assets/refinement/objects/belt-straight-n/candidates/round-09/consumer/.godot/.gdignore` and `assets/refinement/objects/coin-pop/final/original-catalog-object.json`. No refinement assets or existing game rules were modified by this prototype.

The review prototype uses its own localStorage key and mock collection, prices and balance. It demonstrates a single optional pattern offer, unlimited painting and the updated #20 interactions; the native implementation now adds rotation, real save migration and the approved Godot interactions separately.
