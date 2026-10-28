# Revision 5 · slower purchase flight

The user found the purchase flight too fast. Increase travel from 680ms to 1100ms while keeping the existing arc, independent item layers and 240ms bag arrival pulse. Store the adjustable flight duration in the existing timing configuration. Payment remains immediate; bag tap and close stay available throughout travel. Reduced motion still omits travel. This changes only pacing and reuses the exact existing composition/assets.

# Revision 4 · shopping bag returns to inventory

The floating bag is now an accessible button labeled Back to inventory, with the existing cream surface and 54–62px target retained. Tap, click or Enter closes Shop through the same close path as the shared X, restores the mounted Edit inventory tray and its tab/scroll, and returns focus to the Shop opener. This also works during an item flight without undoing or repeating payment. The bag remains the destination for purchase animation. No new surface or raster artwork is needed; the maple popup and beige rounded scroll view remain unchanged.

# Revision 3 · maple popup and recipe catalog interior

The user requested the same wood grain popup as the game's other popups, with the recipe picker's beige rounded scroll area. Reuse `.wr-panel` and `.wr-catalog` directly from `wireframe/recipe-maple.css`, including the exact approved grain, fine maple rim, depth shadow, beige fill and inset shadow. Compose one portrait-contained maple shell, fixed coin/title header and existing shared X, independently scrolling beige catalog with rounded clipping on all four corners, and a quiet wood footer with the floating bag. Item flights remain a separate unclipped overlay layer, so they can travel from the beige list into the bag. Keep Edit-only tray entry, hidden/restored tray, purchases, stock, disabled costs, focus/Back, independent flights and reduced motion exactly as revision 2.

The full surface/state inventory remains normal, pressed, disabled, sold-out, flight/arrival, interrupted purchase, gallery, Edit tray/Live absence and viewport containment. Reuse approved existing raster grain and wave artwork without regeneration. The generated paper is retained only as history. The same popup/catalog CSS now supplies the Shop and recipe-picker presentation. This supersedes the paper surface described in older briefs below.

# Revision 2 · user-directed composition

Shop entry exists only on the Edit inventory tray. The left HUD Shop action is removed; Live has no Shop entry. Opening Shop hides the entire inventory dock while keeping it mounted for scroll/focus restoration. Shopping keeps Edit paused. The full paper leaf now has four ordinary rounded corners and the identical 44px cream round X shared with Applicants and the chef popup. There is no curled-return control. A passive 62px floating shopping bag sits 25px from the lower-right paper boundary; the catalog has enough bottom scroll padding to clear it. Purchased item thumbnails fly from their own row to this bag and give it a short arrival pulse; purchase text/receipts are removed. Payment and inventory commit before motion. Overlapping flights, closing/reopening, cancellation and reduced motion cannot change the purchase. Reduced motion skips travel and only gives the bag a short pulse.

Assets: existing ImageGen paper and approved maple/cream surfaces are reused unchanged. The approved close component is shared directly with both neighboring prototypes. The bag uses the existing monochrome SVG icon vocabulary, with live item artwork as independent animation layers. No raster surface generation is needed for this revision. Normal/pressed/disabled/sold-out, purchase-in-flight, bag-arrival, Edit-only entry, hidden/restored tray, focus/system Back, reduced-motion and interrupted motion are the revision state inventory. This user instruction supersedes the original Live entry and curled-return requirements below; those describe the historical first draft.

# Issue 18 · complete composition and asset map

The approved continuous maple dock and fixed coin/Editing/Live pills remain the neighboring family. The Shop is one nearly full-height warm paper leaf over the mounted restaurant, with a generous upper-right diagonal opening and curled underside. This exposes the actual same restaurant DOM, including its exact camera offset. A fixed header contains the live coin balance and Shop title; one independently scrolling list contains essentials and limited goods with no section headings. Each row has separate artwork, name, useful description, stock, and a cost-only action. Purchases stay on the leaf. A quiet inline Added to inventory receipt updates without moving rows. No confirmation dialog, extra return action or stock refresh.

Reference sections: restaurant catalog 5 (press/disabled), 8 (paper surfaces), 10 (seating), 11 (conveyor), 15 (decor); 3 (coins) and 14 (feedback) support the family. Current #shop, #shop-unaffordable, #component-paper-page and #component-restaurant-hud govern behavior; current wood-dock prototype governs neighboring composition. Accepted B and restaurant world concept were inspected, with later wood-dock amendments taking precedence.

| Piece | Source / layer | Bounds and behavior |
| --- | --- | --- |
| Whole page | New ImageGen warm blank paper, based on complete composition and approved paper | Nine-slice fixed corners; clipped diagonal upper right. Plain center can resize. Safe content 18px each side. |
| Curled underside | Code geometry with same paper material | Separate 76px square, no baked text; same diagonal as page cutout; target at least 76px. Reveals real mounted room. |
| Goods | Existing editor Blender thumbnails | Preserve complete image aspect; bottom-center in 76px art bounds. Same asset used for inventory. |
| Placed goods | Existing registered production world art | Crop first idle frame with source scale/root registration; bottom-centered on square grid. |
| Actions/coins | Existing approved maple/cream HTML family | Dynamic labels/counts, normal/pressed/disabled; 44px minimum hit bounds. |
| Inventory | Existing continuous maple board, tabs, waves and quantity circles | Horizontal scroll, direction-owned upward placement; tap selects then tap a valid cell. |
| Receipt | Live inline text on the paper | Fixed reserved line; no additional surface. |

State inventory: affordable and unaffordable cost actions, limited quantities and sold-out rows, purchased receipt, normal/pressed/lifted curl, Live/Edit origins, all three dock categories, selected inventory, valid/invalid placement, stored object, gallery. No NEW/MAX mechanics apply to these offers. Prototype state is isolated in its own browser key; prices are review fixtures, separated from rules. No native game/save changes before deployed approval.
