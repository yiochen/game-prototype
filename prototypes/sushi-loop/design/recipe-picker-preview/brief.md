# Issue 15 — recipe picker HTML review

Scope: ImageGen composition and interactive HTML/React review in the existing wireframe studio. Native Godot integration remains pending review.

## Visual direction

Extend the approved continuous maple inventory dock: pale warm maple, quiet grain and carved waves, cream faces, dark walnut depth, rounded Nunito labels, vermilion primary action. Keep the restaurant visible around a large portrait dialog. Catalog sections 5 (states), 8 (panels), 13 (dish identity) guide this slice. Earlier B/indigo composition is family history; the maple amendment is current.

## Complete composition and surface/state inventory

- Maple dialog frame, maple header with chef portrait/name and level, round cream close target.
- Scrollable two-column catalog in a cream inset; recipe artwork on White/Yellow/Red/Blue/Black plates with distinct rims.
- Cream recipe cards: normal, pressed, current (walnut inner outline), inspected (brighter cream background), both, NEW, muted ineligible, unknown food silhouette without name/price.
- Full-width fixed lower details area, flush to both inner popup edges with padded content: plated dish, name, fixed price, effective prep time and required level. Empty, eligible, ineligible, current and unknown states.
- Vermilion Prepare action, noninteractive Preparing status and subdued disabled Prepare. Quiet wave engraving at the bottom.
- Return to the originating restaurant preview on Prepare/close; reopening retains the current recipe and inspection-cleared NEW state in this browser. No save/economy simulation is claimed.
- Desktop and landscape retain a portrait composition. All actions have 44px targets; keyboard focus, Escape, outside-tap shielding and reduced motion are supported.

Generate the complete screen first, then coordinated transparent empty-plate and sushi-only families. Keep dynamic labels and counts in HTML. Preserve full originals, prompts and reference hashes. Compose plate and sushi as independent HTML layers; the earlier combined dish sheet is superseded and retained as history. Use existing wood/wave textures and code geometry as in the approved inventory bar; do not stretch a generated full-screen bitmap into the UI.

Fixture values are design examples, not balance changes. Chef-level thresholds remain 1/3/5/8/12; recipe prices remain fixed within strictly ordered bands. Unknown recipes stay after discovered recipes, with cookable recipes descending before ineligible discovered recipes.
