# HTML UI fidelity review

Reference: `../inventory-tray-concepts/v5-connected-tabs/full-screen.png`, with the
later user refinements for compact controls, clipped inventory and a short
fading safe-area footer.

The latest request replaces all pre-rendered UI surface assembly with HTML/CSS.
Only wood-grain and wave textures remain as UI image backgrounds. The original
surface sheet and previous screenshots remain available as history.

| Element | Current construction |
| --- | --- |
| Maple board and active cap | CSS radii and inset highlight, shared uniformly scaled grain coordinates, two-unit overlap at the join |
| Inactive categories | CSS rounded faces with shallow lower shadows, detached from the board |
| Shop action | CSS walnut capsule and wood-grain tint, independent of the tablist |
| Stock badge | CSS circle, ivory border and live number |
| Coin counter | HTML number, CSS cream capsule and gold coin, SVG star |
| Editing and Live | HTML mode controls, CSS cream/vermilion capsules, SVG pencil/play |
| Icons | Monochrome inline SVG |
| Footer | Complete wave repeat, uniformly scaled and faded within the safe area |
| Restaurant and goods | Separate illustration/content images, with no baked HUD faces |

Retain 78-unit category caps, a 60-unit Shop surface, minimum 44px input targets,
16-unit inventory clipping insets and the 42-unit footer plus real safe-inset
handling. The native merchandise artwork is reused rather than replacing it
with pixels from the generated concept.

Check all six states on 390×844, 320×720, 1280×720 and 984×1224. Verify the exact
two-texture UI background contract, category and Shop recovery, horizontal and
upward gesture ownership, keyboard reveal, complete status labels, and Live to
Editing presentation recovery. Live is a visual preview, not a simulation.
