# Selected art direction: doodle

Status: accepted by the user. Applies to both the sushi restaurant and submarine expedition.

## Visual reference

![Selected doodle direction: restaurant on the left, expedition on the right](../design/art-directions/01-doodle.png)

The paired image is the primary reference for visual style. Gameplay and controls documents govern behavior and cell occupancy; the image is a static art study rather than a production sprite sheet.

## Style guide

- Confident, slightly irregular ink outlines with rounded, readable silhouettes.
- Simple expressive faces and modular character shapes suited to 2D animation. Customer reactions should read at phone size.
- Flat color fills with restrained paper grain and sparse hatching. Keep textures quieter than characters, sushi, pickups, and hazards.
- Restaurant: warm ivory floor, coral accents, mustard highlights, and mint details.
- Expedition: deep navy and teal water, warm yellow submarine and headlight, and bright accents for interactive objects.
- Both modes share the same line treatment, shape language, and hand-drawn sticker-like icons. Cream HUD surfaces and dark numerals provide clear contrast.
- Commercial finish comes from consistent outlines, deliberate spacing, polished icons, and clear visual hierarchy.

## Gameplay presentation

Use locked portrait orientation throughout the game, including the sushi bar, expedition, Workshop, and related screens. Rotating the device does not reflow the game into landscape. Exact phone insets and sizes remain to be designed.

The restaurant retains its square grid, with each chef, seat, and belt tile fitting its own cell. Recipe blackboards belong within the chef's footprint. NPC reactions and belt dishes remain easy to distinguish from floor decoration.

Use a full-screen portrait recipe picker for the selected chef, with a scrolling two-column grid of recipe tiles in the upper area and a fixed recipe details panel below. On opening, the panel shows this chef's current recipe. Order the groups as cookable recipes from highest to lowest tier, discovered recipes above this chef's tier from highest to lowest in muted color, then undiscovered recipes as silhouettes engraved on their tier-material boards. The named tiers are Wood, Steel, Copper, Silver, and Gold. Render each recipe tile as a board made from its tier's material, using distinct color and texture rather than relying on a text label. Show discovered dishes as full-color illustrations against their board; keep undiscovered dishes as engraved silhouettes. Mark newly unlocked recipes with a small NEW badge until inspected in the restaurant. Outline the current-recipe tile and give the tile selected for inspection a different outline; keep both outlines distinguishable if they apply to the same tile. Keep these outlines visually distinct from NEW. Tapping a discovered tile updates the lower panel with its artwork, price, preparation time, and required chef tier. When it shows the chef's current recipe, display a noninteractive Preparing status in place of Prepare; selecting a different eligible recipe restores Prepare. Include both an icon-only header close control and support the phone's system back gesture; either closes the picker without changing the chef's current recipe or cooking state. The panel stays in place while tiles scroll. Choosing a different recipe closes the picker to show live service; briefly shake the updated chef blackboard to signal the recipe change. Keep this motion local to the blackboard within the chef's cell. For cookable recipes, show only the preparation duration adjusted for this chef's current speed, omitting base time. Discovered recipes above the selected chef's tier stay inspectable with their requirement displayed; disable Prepare and show a dash (—) for preparation time while the chef is ineligible. Keep the NEW marker legible alongside tile artwork; tier thresholds and material details, card/panel dimensions and artwork/insets, and blackboard-shake timing/amplitude remain to be designed.

At the restaurant dock, show charge through a scene-local battery indicator. When the battery is full, keep it visibly full and gently pulse the submarine's headlight to signal readiness. Keep this cue within the dock scene, without a ready badge. Tapping the charging submarine shows a brief local message with Charging and the time remaining until full. Keep time remaining on demand rather than in a persistent HUD timer. Exact headlight colors, animation timing, and charging-message wording/duration remain to be designed.

Inside the Workshop, use a visible doorway with the sushi curtain and Sushi Bar sign as the return entrance to the restaurant. It follows the expedition preparation screen's scene-entrance convention. Leaving the Workshop centers the restaurant view on the cleared floor at the accepted fixed scale, showing its current live customer and dish activity. The expedition preparation screen's Sushi Bar doorway and the results' Restaurant action use the same restaurant-floor framing on return. Exact doorway placement and tap area remain to be designed.

The expedition shows an overhead submarine traveling up the screen along a descending ocean-bed canyon. The scene fills the screen, with drag steering and a compact top HUD overlay. Its status row places the hull meter upper-left, collected expedition salvage as an icon and amount in the center, and pause upper-right. The creature's name and boss-style resistance bar occupy a separate wide row below while ship status stays in place. The bar appears full when the shooting window opens, stays full during aiming, and drains toward capture after hooking while following within range. A contextual harpoon button overlays the lower-right corner during the shooting window. During cooldown, mute its icon and fill a circular recharge ring around the button, restoring its active appearance when ready; keep the feedback within the button without a numeric timer. Pursuit shows a faint narrow vertical following strip tracking the creature's horizontal position, without visible top or bottom boundaries. Upcoming encounters occupy the visible space above the submarine. Coins belong to the restaurant economy; salvage belongs to the expedition economy.

Before an unhooked creature's shooting window expires, show a clearly restless animation, such as quicker fin movements and extra bubbles, then let it swim away at expiry. The warning does not change its movement path or hit area. Convey the approaching escape through the creature's behavior, without a shooting-window HUD countdown. Exact warning duration and species-specific animation remain to be designed.

Confine the low-hull warning to the existing upper-left hull meter, using a warning color and gentle pulse while hull is low. Add no screen-edge tint. Exact threshold, colors, pulse timing, and intensity remain to be designed.

Celebrate a successful catch with a full-screen portrait cutscene in the selected 2D doodle style. Keep it very quick, lasting only a few seconds, and play it automatically without a Skip button. Open the award dialog automatically afterward. Active gameplay and hazards have ended during this presentation. The composition, animation, and exact timing within the short-duration target remain to be designed.

Expedition results present a salvage receipt with pickups, a repeat-catch bonus when earned, and a completion bonus, followed by a prominent total earned. Show a zero completion bonus with a short explanation on failure or early return. Keep the single Restaurant continuation. The dedicated first-catch recipe award dialog shows the recipe and its accepted facts; the following results omit a recipe recap. Use the outcome titles Expedition complete, Returned early, and Hull depleted, each with a different image-generated background in the selected 2D doodle style. Keep the receipt and action visually consistent across outcomes. Backgrounds are presentation rather than additional repair, rescue, permanent-damage, or lost-reward mechanics. Exact receipt/background styling remains to be designed.

Generated background studies within result-screen mockups: [bright completed-route water](../design/ui/41a-results-complete.png), [quiet return corridor](../design/ui/41b-results-returned-early.png), and [damaged submarine in a rocky alcove](../design/ui/41c-results-hull-depleted.png). These illustrate the accepted distinct-background approach; their exact composition and example amounts remain proposals. [Exact prompts and output record](../design/ui/41-results-background-prompts.md) document the built-in generation. Each is a static portrait mockup with baked-in UI rather than an isolated background or animated cutscene.

At a few selected equipment levels, show visible hull-panel, harpoon, or collector improvements on the submarine. The same equipment appearance persists in the Workshop, dock, and expedition. Preserve the recognizable yellow silhouette, existing ship footprint, and collision size. These changes reflect the accepted equipment stats without adding mechanics. Exact thresholds and part artwork remain to be designed; existing references do not depict every equipment level.

## Source and alternatives

The reference was generated with the built-in image generation tool. Exact prompts are recorded in [the generation record](../design/art-directions/prompts.md).

The retro atomic and bright storybook studies remain saved as alternatives. Doodle is the selected direction for future work.
