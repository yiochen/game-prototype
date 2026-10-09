// Review inventory. These fixtures describe intended UI behavior, not gameplay rules.
const element = (name, behavior, motion) => ({ name, behavior, motion });
const paperReturn = () => element(
  'Top-right curled paper corner',
  'Shop and Workshop share a paper page over the originating restaurant. Its curled upper-right corner reveals that actual floor plan and is the Return to Restaurant target. Returning preserves Live/Edit mode, tray state and exact camera position; omit a doorway or full-width return button. Supply an accessible return name.',
  'The curl grows from 48 px to 72 px on hover or press over 160 ms. A 200 ms paper exit fade is proposed; current wireframe return restores the restaurant directly without moving the floor. Reduced motion also restores directly; consume the opener touch.'
);
const closePopup = () => element(
  'Close / system Back',
  'Close the active popup and restore its parent view without applying an unconfirmed choice. Outside taps neither close the popup nor activate the scene underneath.',
  'Popup exits with a 160 ms opacity fade and 8 px downward movement. Return focus to the opener; reduced motion uses a fade only.'
);
const popupEntrance = 'Light scrim fades in over 160 ms; popup rises 12 px over 220 ms. Keep the scene visible. Reduced motion removes travel.';
const motionNote = 'Animation values are proposed review targets. State changes happen on the action, never after an animation finishes.';
const mockNote = 'All values and interaction outcomes are fixtures for review; this story does not run economy, service, physics, clocks, or save logic.';
const floorOnlyNote = 'This review pass draws the restaurant floor, entries, expansion patches and dock without belt, chef or customer decoration. One neutral footprint remains in the selected-object example for its tools. The accepted future gameplay and simulation rules remain unchanged.';

export const storyGroups = [
  { id: 'layout', title: 'Floor plan' },
  { id: 'concept', title: 'Concept & art' },
  { id: 'components', title: 'Shared components' },
  { id: 'restaurant', title: 'Restaurant' },
  { id: 'recipes', title: 'Recipe picker' },
  { id: 'staff', title: 'Staff & applicants' },
  { id: 'shop', title: 'Shop' },
  { id: 'workshop', title: 'Workshop' },
  { id: 'expedition', title: 'Expedition' },
  { id: 'rewards', title: 'Catch & rewards' },
];

const expeditionComponents = [
  ['expedition-surroundings', 'Ocean · canyon & scenery', 'Reusable canyon edges, seabed, plants and current-direction marks establish the ocean without covering the ship, hazards or HUD. Scenery is distinct from collidable obstacles.', 'World dressing scrolls with the route in the intended game; this review fixture stays still.'],
  ['expedition-obstacle', 'Obstacles · long tunnel barriers', 'Long rock shelves, reef ridges and wreck sections run along forward travel like train-length barriers. Some take half the playfield width and extend beyond one screen in length. Canyon walls and staggered barriers form a continuous tunnel passage with room to steer; exact collision shapes and spacing remain balance work.', 'Obstacles travel with the route. Contact feedback belongs to the future simulation; no artificial obstacle movement or damage is added by this gallery.'],
  ['expedition-pickup', 'Salvage · collectible pickup', 'Salvage fragments are separate world items, visibly smaller than obstacles. Collected salvage belongs to this expedition; the top HUD shows the run total rather than the banked Workshop balance.', 'Future collection draws a fragment toward the ship and updates the run total immediately. The gallery shows static collectible states.'],
  ['expedition-submarine', 'Submarine · ship states', 'Use the same ship silhouette in preparation, travel, pursuit and catch scenes. Its visual footprint remains much smaller than half-width obstacles, with lateral room to steer.', 'Direct relative steering follows a fresh playfield drag; release stops lateral movement. The wireframe does not implement steering or collision simulation.'],
  ['expedition-creature', 'Creature · encounter & catch', 'The same creature renderer supports aiming, hooked pursuit, approaching escape and caught presentation. The escape warning changes expression or movement tone, not the creature hit area or path.', 'Restless motion warns before shooting-window expiry; caught artwork stays recognizable. Motion is proposed and respects reduced motion.'],
  ['expedition-hud', 'Expedition HUD · hull, salvage & pause', 'Reuse the stable top row: continuous hull meter left, current-run salvage in the center and Pause at right. Low hull changes only the hull meter; keep normal travel space clear.', 'Numbers update on events. A proposed gentle low-hull pulse stays inside the meter; no screen-edge warning tint.'],
  ['expedition-resistance', 'Creature resistance · aiming & reeling', 'The separate creature-name row appears below the ship HUD. Resistance stays full while aiming and drops toward capture during valid following; it is not an escape countdown.', 'Update fill with intended catch progress, without jumping the HUD or delaying logic for animation.'],
  ['expedition-following-range', 'Following range · strip & cable', 'A faint full-height vertical strip tracks the creature horizontally, with no top or bottom border. The shared cable communicates hooked, taut and frayed states without becoming a second HUD.', 'Strip follows the creature. Cable feedback reflects actual following/grace state in the future simulation.'],
  ['expedition-attack-warning', 'Attack warning · hazard column', 'A local column shows an incoming creature attack in the world. Preserve readable boundaries and a clear steering route; the warning does not cover the persistent HUD.', 'Future warning leads the attack with a brief local cue. The gallery is static and introduces no new attack timer.'],
  ['expedition-harpoon', 'Harpoon · ready, cooldown & shot', 'The contextual lower-right control shows ready, muted cooldown with a circular fill, and disabled states. A shared projectile travels straight upward from the ship. A fresh press fires once; holding does not repeat.', 'Press feedback takes 70 ms. Future cooldown fills the ring and restores readiness without numeric countdown text.'],
  ['expedition-resume-countdown', 'Resume · countdown', 'Show only the count and Returning to ship... over the preserved expedition. Ship, creature, hazards and timers stay frozen during countdown; opener input cannot steer.', 'Future countdown updates the numeral; the fixture displays a still count. Return to the preserved scene without accumulated movement.'],
  ['expedition-preparation', 'Departure · airlock & Start', 'Reuse the Sushi Bar airlock, ready ship/battery and explicit Start action. Opening preparation or returning through the airlock consumes no charge; Start consumes readiness.', 'Consume the opener touch and use the shared press response. No automatic launch or repeated Start action.'],
  ['expedition-catch-reward', 'Catch celebration · first & repeat', 'Use the shared caught-creature presentation for a short first-discovery celebration and a familiar catch with earned repeat salvage. First catch proceeds to its recipe award; repeat catch proceeds to results.', 'The intended celebration lasts only a few seconds and advances automatically. This fixture previews the states without a simulated timer.'],
  ['expedition-route-feature', 'Route features · currents, boosts & portals', 'Distinct current arrows, boost and portal cues are ordinary-travel world elements. Currents allow steering; boosts and portal passages end before aiming or pursuit. These visual examples do not implement the future route mechanics.', 'Future cues scroll with the world. Keep direction and entrances legible, with no mandatory control footer or extra steering button.'],
];
const worldComponentStories = [
  {
    id: 'component-garbage-cluster', group: 'components', title: 'Garbage clusters · paid clearance', scene: 'component', component: 'garbage-cluster', variant: 'garbage-cluster',
    description: 'Each garbage cluster is one distinctive broken object: a sofa, wrecked car or collapsed shelving with varied supporting rubbish. Configurable footprints set occupied floor cells independently of its artwork. Each cluster is inspected and paid for separately.',
    elements: [
      element('Variable footprint', 'Show a whole broken sofa, wrecked car and collapsed shelving as distinct compositions across compact, broad and tall footprints. Do not repeat the same rubbish tile over the cells; the grid describes occupancy only. Sizes and prices are illustrative. Unselected clusters show no price.', 'World clusters stay fixed to their floor cells while the camera pans. Proposed clearance fades only the selected debris over 350 ms.'),
      element('Inspect and pay', 'Tap any uncleared cluster to open the same minimal confirmation with its exact footprint and cost on Clear. Cancel preserves it; insufficient coins disable Clear. A confirmed preview deducts that fixture cost once and clears only the chosen cluster.', popupEntrance),
      element('Shared scene use', 'Use this same renderer for adjacent restaurant expansion patches and the confirmation silhouette. A cleared example remains cleared until Reset; wireframe fixture state is not saved game progress.', 'State updates immediately on Clear. Reset restores the original examples and mock balance without an animation delay.'),
    ], notes: [motionNote, mockNote],
  },
  ...expeditionComponents.map(([component, title, behavior, motion]) => ({
    id: `component-${component}`, group: 'components', title, scene: 'component', component, variant: component,
    description: behavior,
    elements: [element('Shared presentation and states', behavior, motion), element('Scene integration', 'The complete expedition scenes render this same component. Review its isolated states here and its spacing with other elements in the full scene.', 'Shared presentation changes apply in both contexts. Existing gameplay, input and reward contracts remain unchanged.')],
    notes: [motionNote, mockNote],
  })),
  ...[
    ['pause-dialog', 'Pause card · expedition', 'pause', 'pause'],
    ['early-return-dialog', 'Return confirmation · expedition', 'early-return', 'return'],
    ['recipe-award', 'Recipe award · first discovery', 'recipe-award', 'award'],
  ].map(([component, title, overlay, variant]) => ({
    id: `component-${component}`, group: 'components', title, scene: 'component', component, overlay, variant,
    description: 'The exact shared dialog from the expedition flow is shown over a neutral review stage. Its actions and focus behavior match the complete scene.',
    elements: [element('Shared dialog', 'Use the same dialog, copy and actions in this isolated page and the full flow. Pause offers side-by-side Resume and Return early; early return retains earned rewards; the recipe award uses its material board and Continue.', popupEntrance)],
    notes: [motionNote, mockNote],
  })),
  {
    id: 'component-expedition-results', group: 'components', title: 'Expedition results · three outcomes', scene: 'component', component: 'expedition-results', variant: 'complete',
    description: 'Complete, early return and hull depletion reuse the same outcome presentation and salvage receipt as the complete results scenes.',
    elements: [element('Outcome background, receipt and action', 'Keep a distinct backdrop/title per outcome, earned salvage and one Restaurant action. Incomplete routes have no completion bonus. The first-discovery award already covered the recipe; omit its recap.', 'Proposed 220 ms scene crossfade. Receipt values appear together without delayed counting or extra required interaction.')],
    notes: [motionNote, mockNote],
  },
];

export const stories = [
  ...worldComponentStories,
  {
    id: 'floor-plan', group: 'layout', title: 'Full restaurant floor plan', scene: 'floor-plan', variant: 'overview',
    description: 'Three portrait-width panels form one continuous restaurant. Only the first is usable initially; future floor is blocked by garbage. The middle panel reserves the submarine and a compact Workshop hut.',
    elements: [
      element('Panel guides', 'Reference widths for the camera, not partition walls. Pan across the full plan; retain a finished left wall.', 'The floor follows a swipe or finger drag at a fixed scale. Keep the released camera position; no numbered shortcuts, panel snapping or pinch zoom.'),
      element('Floating Shop button', 'Shop belongs to the fixed HUD below the upper-left coin count and uses no restaurant floor cells. This overview offers the same navigation above the plan.', 'Press feedback for 70 ms; scene crossfade takes 200 ms. The button remains fixed while the floor pans.'),
      element('Entry openings', 'Customer entrances sit along the top of each panel. Later access activation is a proposal for review.', 'If route activation is accepted, the entrance changes from muted to active over 180 ms.'),
      element('Garbage patch', 'Tap an adjacent patch to inspect its footprint and open the expansion card. Clear purchases a permanent floor extension in the intended game.', 'Center the selected patch over 300 ms; its outline appears in 160 ms. Clearing uses a local 350 ms debris fade.'),
      element('Submarine and Workshop hut', 'Share one 3 × 3 floor-cell footprint in panel two, with Workshop to the submarine’s right. Keep their targets separate and leave room above the hut for taller artwork without covering the submarine.', 'Submarine ready light gently pulses over 1.6 s; hut has press feedback only. Neither target has a constant bouncing marker.'),
      element('Covered future dock', 'When access is locked, patchwork rags cover both landmarks with small openings that reveal parts of their silhouettes. Both targets are unavailable; show no Future access instructions.', 'Cloth stays still while locked. Proposed unlocking fades the covering locally over 240 ms; reduced motion uses an immediate reveal.'),
    ],
    notes: [floorOnlyNote, 'The sketch supersedes the earlier two-panel image layout. The combined dock footprint is 3 × 3 cells; overall grid dimensions, patch shapes, prices and dock approach remain open.', 'Activating later entries or the dock when a cleared route reaches them is a proposal, not an approved rule.', motionNote, mockNote],
  },
  {
    id: 'concept-doodle-catalog', group: 'concept', title: 'Doodle UI & art catalog', scene: 'concept', variant: 'catalog',
    description: 'The supplied doodle catalog is displayed unchanged as a visual reference for materials, shapes, icons, sprites and scene artwork. Screen composition and controls continue to follow the wireframes.',
    elements: [
      element('Full supplied catalog', 'Show the complete original 1024 × 1536 image in a scrollable viewport. Keep its aspect ratio and artwork unchanged. The catalog’s illustrative branding, Map, Settings, level HUD and junction-belt examples do not add controls or gameplay to Sushi Loop.', 'The reference image stays still. Native scrolling follows the user directly; do not animate or reconstruct the catalog artwork.'),
      element('Zoom / Fit catalog', 'Zoom displays the original image at its natural width inside the contained scroll area so its annotations can be read on a phone. Fit restores the full-width overview. Both controls preserve the surrounding explorer and its comment context.', 'Change the image size immediately; no animated zoom or delayed interaction. Keyboard focus remains on the same control.'),
      element('Open full-size catalog', 'Open the same original image in a separate tab for browser zoom or sharing. Supply an accessible link and retain this concept page as the source of review comments.', 'Use normal link navigation without a popup entrance or custom transition.'),
    ],
    notes: ['This is a concept reference page, not another shared component or an approved screen. The catalog informs the doodle art vocabulary; accepted Sushi Loop behavior and controls remain in the wireframes.', motionNote],
  },
  {
    id: 'restaurant-live', group: 'restaurant', title: 'Live service · starter floor', scene: 'restaurant', variant: 'live',
    description: 'A floor-plan-only starter restaurant keeps fixed navigation visible while the continuous room pans freely. Service characters and furniture are omitted for this layout review.',
    elements: [
      element('Coin count', 'Shows restaurant savings at the upper-left, above the floating Shop button. Reserve the credited-earnings line even when absent so +420 while away can appear without moving Shop. Styled numerals use no cream/yellow backing container; no income-rate counter.', 'A sale updates the number immediately in the intended game; a nearby icon can pulse for 180 ms with repeated events coalesced.'),
      element('Edit control', 'The bottom-left Edit target opens editing. Intended restaurant service pauses immediately; the wireframe does not display Service paused text.', 'Press feedback for 70 ms; edit chrome appears over 200 ms without changing the camera position.'),
      element('Staff control', 'The bottom-left Staff target opens a paginated bottom tray of three compact draggable chef profiles per row, with previous/next carets at the row edges and no visible page number, while keeping the restaurant visible. Tap a profile to inspect its stats in a popup; Job applicants opens resume browsing.', 'Tray enters over 200 ms. Intended service remains live; the tray does not add a full-scene scrim.'),
      element('Floating Shop', 'The upper-left Shop button opens its scene from any camera position in Live or Edit. Returning restores that mode and exact camera position.', 'Shop has 70 ms press feedback and a 200 ms scene crossfade. It never travels with the camera.'),
      element('Finger panning', 'Drag or swipe the floor to pan at a fixed scale. There are no numbered panel buttons, directional shortcuts or snapping between panels.', 'The floor follows the finger directly; release retains the resulting camera position. Fixed HUD controls remain still.'),
      element('Future floor', 'Garbage remains on the floor and opens a selected patch card. The finished left wall marks the room boundary.', 'A selected garbage patch centers over 300 ms; its outline fades in for 160 ms.'),
    ],
    notes: [floorOnlyNote, 'HUD controls use clear transparent target outlines for this wireframe. Their touch area is larger than the visible icon.', motionNote, mockNote],
  },
  {
    id: 'restaurant-expanded', group: 'restaurant', title: 'Live service · dock unlocked', scene: 'restaurant', variant: 'expanded',
    description: 'A floor-plan-only cleared middle panel makes the submarine and adjacent compact Workshop hut available, while farther patches remain blocked.',
    elements: [
      element('Scene panning', 'Swipe or drag the floor freely. HUD remains viewport anchored; dock, entrances and expansion patches move with the floor. No numeric shortcuts or panel snapping.', 'Follow the finger directly. Retain the exact camera position through Shop and Live/Edit transitions; selected patches may recenter smoothly over 300 ms.'),
      element('Ready submarine', 'Tap to open expedition preparation. This does not launch or consume readiness; Start does.', 'Full battery stays full while the headlight gently pulses over 1.6 s. Destination enters with a 200 ms crossfade.'),
      element('Workshop hut', 'Tap the compact hut/sign to the submarine’s right to inspect upgrades. Together they occupy 3 × 3 floor cells, with room above the hut for taller artwork.', 'Press for 70 ms; 200 ms scene crossfade. Preserve the mode used to leave the restaurant.'),
      element('Remaining garbage', 'Inspect a neighboring expansion patch without showing all prices on the floor.', 'Selection outline fades in for 160 ms and its bottom-half card rises 12 px over 220 ms.'),
    ],
    notes: [floorOnlyNote, 'The cleared layout is an example for navigation review. Unlock requirements and progression timing remain unresolved.', motionNote, mockNote],
  },
  {
    id: 'restaurant-edit', group: 'restaurant', title: 'Edit · layout tools', scene: 'restaurant', variant: 'edit',
    description: 'Floor-plan-only editing uses a top-right Live control and a separate vertical stack of People, Layout and Floor controls on the right. Only the selected layer shows its name beside the icon; the bottom tray can be opened or collapsed.',
    elements: [
      element('Live control', 'The top-right target returns to live view. Intended service resumes immediately; edit choices already apply and need no confirmation. Omit Service paused text.', 'Press 70 ms; edit chrome fades over 160 ms. Keep the exact camera position.'),
      element('Right-side layer icons', 'People, Layout and Floor buttons stay vertically stacked at the right, outside the bottom tray. Show the selected layer’s name beside its icon, including while its tray is collapsed; other layers remain icon-only. All have accessible names.', 'An active-layer outline and adjacent title crossfade over 140 ms. Controls remain fixed while the floor pans; reduced motion updates the title immediately.'),
      element('Selected-layer toggle', 'Tap the active layer to collapse its tray; tap it again to reopen the same content. The chosen layer remains selected while collapsed.', 'Tray height changes over 200 ms with ease-out. The layer stack follows its top edge over the same duration, staying outside the tray. Reduced motion applies both positions immediately.'),
      element('Different-layer selection', 'Tap another layer to select it and open its content, including when the prior tray was collapsed.', 'Active outline and content update immediately. Tray height and the layer stack position ease to the new content height over 200 ms.'),
      element('People roster tray', 'Reuse the shared roster component with three compact profiles per row, same-row edge carets and no visible page number. Tap inspects stats; drag previews placement while preserving the layer’s tray toggle.', 'Use the shared roster’s 70 ms tap response, direct drag ghost and 160 ms page-content crossfade.'),
      element('Bottom inventory tray', 'People uses the shared compact roster tray rather than a separate Omar inventory card. Layout and Floor use paginated two-item rows with previous/next carets at the left and right edges, without visible page numbers. The tray stays separate from the right-side controls. Full-game drag placement and validation are future implementation.', 'Inventory selection reacts on press. Future drag follows the finger directly, with an invalid item settling back over 180 ms.'),
      element('Finger panning', 'Drag or swipe the floor freely; there are no numbered or directional pan controls and no panel snapping.', 'Camera follows the finger directly at a fixed scale and retains its position when a tray changes.'),
    ],
    notes: [floorOnlyNote, 'Editing still pauses restaurant characters and belts in the intended game; removing the paused label does not change that rule.', motionNote, mockNote],
  },
  {
    id: 'restaurant-floor', group: 'restaurant', title: 'Edit · floor palette', scene: 'restaurant', variant: 'floor',
    description: 'The Floor layer shows thumbnail-only style choices in the bottom tray, with the Floor name beside its selected icon in the separate right-side stack.',
    elements: [
      element('Style thumbnails', 'Show pattern thumbnails in a two-item paginated row with same-row carets at both edges, without visible page numbers, style names, Owned captions or instructional text. Each target retains an accessible style name and selected state. Newest purchases appear first and the free original style last.', 'Selection outline appears over 100 ms. The palette stays in place while a fixture style changes.'),
      element('Floor-layer toggle', 'Tap the active Floor icon to collapse the palette and tap again to reopen it. Its adjacent Floor name remains visible when collapsed; choosing another layer moves the visible name to that layer and opens its content.', 'Palette height changes over 200 ms; the right-side layer stack follows its top edge and stays outside it. Selected name crossfades over 140 ms; reduced motion applies both positions immediately.'),
      element('Paintable floor', 'Full-game painting is cosmetic: tap paints one cell and a stroke paints crossed cells, including beneath furniture. This wireframe previews a style without implementing paint-cell rules.', 'A changed floor surface crossfades over 120 ms. The full-game shared floor shader may use a subtle slow ambient flare.'),
      element('Finger panning', 'Pan by dragging or swiping the floor; no numbered panel shortcuts or edge carets. Keep the chosen style while panning or collapsing the tray.', 'Follow the finger directly at a fixed scale. Do not snap to a panel or clear the selection on release.'),
      element('Live control', 'The top-right Live target returns to live mode without a save or confirmation step.', 'Edit chrome fades over 160 ms; retain the exact camera position.'),
    ],
    notes: [floorOnlyNote, 'Pattern illustrations and the shared floor shader remain future art work. Thumbnail names remain available to assistive technology.', motionNote, mockNote],
  },
  {
    id: 'restaurant-selected', group: 'restaurant', title: 'Edit · selected object', scene: 'restaurant', variant: 'selected',
    description: 'One neutral selection footprint illustrates local Rotate and Remove targets on the floor-only edit view. It contains no customer, chef or belt decoration.',
    elements: [
      element('Selected footprint', 'Represent one selected layout object without adding restaurant furniture artwork. Full-game selection and dragging remain documented intended behavior.', 'Outline appears in 100 ms. In the intended game, the object follows the finger directly and keeps selection after 120 ms cell settling.'),
      element('Rotate target', 'Preview the selected object orientation. Full-game chair rotation changes its facing connection to an adjacent belt.', 'Rotate 90° over 160 ms; reduced motion applies the orientation immediately.'),
      element('Remove target', 'Preview returning a purchased object to inventory without a coin refund. Customer reactions belong to the future service implementation.', 'Footprint fades over 160 ms; fixture inventory state updates immediately.'),
      element('Empty-floor swipe', 'Clear selection and pan in one gesture. Panning is free, without numbered shortcuts or panel snapping.', 'Selection fades for 100 ms; camera follows the swipe immediately.'),
      element('Editor controls', 'The top-right Live control and separate right-side layer stack share their renderer and tray-toggle behavior with the other edit views.', 'Tray height and the right-side stack position ease together over 200 ms. Live remains fixed at the top-right.'),
    ],
    notes: [floorOnlyNote, 'Moving an occupied seat or belt still carries its customer or plate in the intended game; this review footprint does not simulate those reactions.', motionNote, mockNote],
  },
  {
    id: 'restaurant-charging', group: 'restaurant', title: 'Dock · charging feedback', scene: 'restaurant', variant: 'charging',
    description: 'The charging submarine remains in the restaurant and gives local status when tapped.',
    elements: [
      element('Charging dock', 'Tap to show Charging and time remaining locally. Do not navigate to a disabled expedition start screen.', 'Local text enters with a 120 ms fade, holds about 2.2 s and leaves over 180 ms; a repeat tap refreshes the same cue.'),
      element('Battery indicator', 'Shows charge only at the dock. There is no persistent top-HUD battery badge or separate Ready badge.', 'The indicator reflects actual charge linearly in the intended game; fixture charge is static here.'),
      element('Workshop hut', 'Workshop remains accessible while charging.', 'Standard 70 ms press and 200 ms scene crossfade.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'restaurant-offline', group: 'restaurant', title: 'Reopen · earnings notice', scene: 'restaurant', variant: 'offline',
    description: 'The floor-plan-only restaurant shows an illustrative credited-earnings notice beside the coin balance, with no collection popup.',
    elements: [
      element('Coin balance and notice', 'Automatically show updated savings and earned amount in an always-reserved line so Shop remains stationary. Suppress the notice when earnings are zero without removing its layout space; it does not pause service.', 'Notice fades in over 120 ms, holds for 2.2 s and fades out for 200 ms. No claim action or blocking animation.'),
      element('Restored scene', 'Draw the floor and navigation for this review. The intended game still restores saved customers and plates after offline credit; those props are omitted here.', 'Restore the intended saved positions directly; do not animate a backlog of missed sales or customer visits.'),
      element('Floating Shop sparkle', 'A cue attached to the upper-left HUD button signals refreshed goods until entering Shop. Opening Shop clears it.', 'A quiet sparkle loop over 1.8 s; fade it out for 150 ms on entry. The cue stays attached when panning.'),
    ],
    notes: [floorOnlyNote, 'Offline accounting, saving and real-time recharge are out of scope for this prototype. Closing while in edit mode remains an open product decision.', motionNote, mockNote],
  },
  {
    id: 'recipe-picker', group: 'recipes', title: 'Picker · eligible recipe', scene: 'restaurant', variant: 'eligible', overlay: 'recipes',
    description: 'A large portrait dialog overlays the visible restaurant. Its two-column catalog scrolls above a fixed details panel.',
    elements: [
      element('Catalog tiles', 'Discovered tiles show each dish’s fixed coin selling price beside its artwork and name. Tap to inspect without changing the chef’s current recipe; current and inspected outlines remain distinct. Undiscovered tiles do not reveal a price.', 'Tile press for 70 ms; selected outline appears for 100 ms. Lower details crossfade over 140 ms without moving the catalog.'),
      element('Recipe header and catalog', 'Show the chef’s level without a Wood chef or other tier suffix. Preserve catalog ordering without visible group headings; use material textures and muted/outline states to distinguish recipes.', 'The catalog scrolls directly with input. Header stays stable; no title transition accompanies recipe inspection.'),
      element('Fixed recipe details', 'Show dish, fixed selling price and chef-adjusted preparation time on a board made from the recipe tier’s material. Material texture conveys required tier without a visible tier label; retain tier information in accessible descriptions. Exclude base time and belt-loading waits.', 'Details stay anchored while catalog scrolls. Content and board material crossfade together over 140 ms, without counting through intermediate facts.'),
      element('Prepare', 'Choose the inspected eligible recipe, close the picker and update the blackboard. If it is already current, show noninteractive Preparing instead.', 'Apply on tap; close over 160 ms. Blackboard updates immediately and shakes 2° over 260 ms.'),
      closePopup(),
    ],
    notes: ['Order: cookable highest tier first, discovered above-tier next, then undiscovered silhouettes. Service continues while browsing.', 'A newly placed idle chef opens this picker with no selection; Prepare remains unavailable until a cookable recipe is selected.', motionNote, mockNote],
  },
  {
    id: 'recipe-idle', group: 'recipes', title: 'Picker · newly placed idle chef', scene: 'restaurant', variant: 'idle', overlay: 'recipes',
    description: 'Placing an unassigned chef beside a belt opens dish selection without an automatically chosen recipe.',
    elements: [
      element('Empty details panel', 'No recipe is current or inspected yet. Ask for a recipe selection; do not choose the highest-tier recipe for the player.', 'Popup uses the standard 220 ms entrance. Empty panel remains fixed beneath the catalog.'),
      element('Recipe tile', 'Inspect a discovered dish to populate the details. An eligible dish enables Prepare; an above-tier dish remains unavailable.', 'Selected outline appears for 100 ms and details crossfade for 140 ms.'),
      element('Prepare', 'Unavailable until the player explicitly chooses a cookable recipe. Confirming begins that chef’s assigned production in intended gameplay.', 'Disabled action has no press cue; enabled action closes the picker over 160 ms and emphasizes the blackboard.'),
      closePopup(),
    ],
    notes: ['Closing without a recipe leaves the newly placed chef idle. Placing chefs is allowed from the People tray in either live or edit mode.', motionNote, mockNote],
  },
  {
    id: 'recipe-unavailable', group: 'recipes', title: 'Picker · chef tier too low', scene: 'restaurant', variant: 'unavailable', overlay: 'recipes',
    description: 'Discovered recipes above this chef’s quality can be inspected, but cannot be prepared.',
    elements: [
      element('Muted discovered tile', 'Tap to view price and the required tier’s material board without a visible tier name. An accessible description retains the requirement. Inspection still clears NEW, even when the chef cannot cook it.', 'Artwork is muted rather than hidden. Selection outline remains readable; details and board material crossfade for 140 ms.'),
      element('Preparation time', 'Show an em dash while the chef is ineligible; do not imply a usable adjusted duration.', 'Static value; no timer or progress ring.'),
      element('Disabled Prepare', 'Retain the unavailable action and required tier’s board texture; tapping performs no purchase or shortage popup. Expose eligibility and tier to assistive technology.', 'Muted outline and text with no press bounce; accessible disabled state.'),
      closePopup(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'recipe-undiscovered', group: 'recipes', title: 'Picker · undiscovered silhouette', scene: 'restaurant', variant: 'undiscovered', overlay: 'recipes',
    description: 'Undiscovered recipes remain engraved silhouettes on tier-material boards and do not reveal dish identity or facts.',
    elements: [
      element('Undiscovered tile', 'A silhouette explains collection space without revealing the upcoming expedition reward. It has no Prepare action.', 'Static engraved silhouette; no teaser pulse or fake NEW badge.'),
      element('Tier board', 'Distinct wood grain and metal textures communicate Wood, Steel, Copper, Silver and Gold without visible tier labels. Keep tier information in accessible descriptions; texture must remain distinguishable beyond color.', 'No transition until discovery; later artwork can reveal with a 180 ms crossfade.'),
      closePopup(),
    ],
    notes: ['The wireframe uses distinguishable material patterns without visible tier names; dish illustrations remain placeholders.', motionNote],
  },
  {
    id: 'recipe-new', group: 'recipes', title: 'Picker · newly discovered recipe', scene: 'restaurant', variant: 'new', overlay: 'recipes',
    description: 'A NEW marker persists after the expedition award and clears when the recipe is inspected here.',
    elements: [
      element('NEW marker', 'Mark newly discovered recipes until an actual inspection. Opening the picker alone does not clear every marker.', 'Marker disappears over 140 ms after inspection. Do not loop attention animation on every tile.'),
      element('Inspect recipe', 'Update the fixed details without changing current service or requiring Prepare.', 'Outline transition 100 ms; details crossfade 140 ms.'),
      element('Prepare', 'Apply only when the chef is eligible. Discovery never silently replaces existing chef assignments.', 'Close popup over 160 ms and shake updated board over 260 ms.'),
      closePopup(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'staff-roster', group: 'staff', title: 'Roster', scene: 'staff', variant: 'roster',
    description: 'A bottom tray over the visible restaurant pages through three compact draggable chef profiles per row, with edge carets on the same row and no visible page number. Tapping a profile opens its stats popup; applicants remain a separate view.',
    elements: [
      element('Staff capacity', 'Show current and maximum staff in both roster and applicant views. Assigned and unassigned chefs both count.', 'Update directly after hire/fire/expansion; briefly emphasize changed count for 180 ms.'),
      element('Chef profiles', 'Show portrait, name and assignment state on three compact draggable targets per row. A tap opens that chef’s level and stats in a popup; it does not place or unassign them. A valid drop on the visible cleared starter floor previews a neutral footprint and updates assignment presentation while keeping the tray open.', 'Tap press 70 ms; stats popup uses the standard 220 ms entrance. Drag activates after 8 px, source fades over 120 ms and a portrait ghost follows directly. Valid-target outline appears immediately; invalid or cancelled preview removes the ghost immediately. A 160 ms snap-back remains a proposed full-game effect.'),
      element('Roster pagination', 'Left and right carets sit at the two edges of the profile row and page the tray without replacing the restaurant. Show no page number; announce the current page accessibly. Controls have accessible names and at least 44 × 44 px targets; unavailable directions are disabled.', 'Profile page settles with a 160 ms content crossfade; the tray stays in place. Reduced motion updates the page immediately.'),
      element('Job applicants', 'Open separate paper-resume browsing while retaining the roster as the return context. No roster tabs.', popupEntrance),
      element('Tray close / Back', 'Close the roster tray and restore the same restaurant mode and camera position. The tray is not a fullscreen scene and adds no scene-wide scrim.', 'Tray exits over 160 ms. Restore focus to Staff; reduced motion uses a fade.'),
    ],
    notes: ['Drag placement updates presentation fixtures only. Valid drops are limited to the visible cleared starter panel; full-game floor adjacency, occupancy and belt-connection validation remain future behavior. Portrait backgrounds describe occupations and histories, while gameplay comparisons use explicit growth, capability and cost attributes.', motionNote, mockNote],
  },
  {
    id: 'staff-applicants', group: 'staff', title: 'Applicants · available capacity', scene: 'staff', variant: 'applicants', overlay: 'applicants',
    description: 'Browse one paper resume at a time with left/right swipes. Three varied applicants expose strengths, growth, maximum level, reachable tier and hiring cost; explicit Hire confirms the selected candidate.',
    elements: [
      element('Paper resume', 'Present one applicant’s portrait, background, strengths and stats on a paper resume. Left/right swipes browse remaining applicants; swiping alone neither hires nor rejects a candidate.', 'Resume enters over 180 ms, follows a horizontal drag with a small tilt and settles to the selected page over 200 ms. There is no discard fling; reduced motion changes pages immediately.'),
      element('Previous / Next applicant', 'Accessible 44 × 44 px controls provide the same browsing as swipes. Show the current position and number of remaining applications; disable unavailable directions.', 'Use the same 200 ms horizontal settle as swipe navigation. Do not delay action availability until animation completes.'),
      element('Hire', 'Mock one immediate hire into unassigned roster, keeping resume browsing open. Intended game deducts the visible cost with no confirmation. Hired offers leave the remaining pool without automatic replacement.', 'Press 70 ms; capacity and roster change immediately. Resume content changes over 160 ms and a local Hired cue fades over 180 ms.'),
      element('Refresh', 'Replace the applicant set and begin a free real-time cooldown. No confirmation and no pinned candidate; reset browsing to the first new resume.', 'Resume set crossfades over 180 ms. Cooldown stops press feedback until available again.'),
      element('Header X', 'Close resume browsing and restore its originating roster/editor view. Omit the redundant Back to staff footer button; system Back has the same dismissal behavior.', 'Popup fades out over 160 ms and restores focus to the opener; reduced motion uses a fade without travel.'),
      closePopup(),
    ],
    notes: ['Refresh countdown visibility remains deferred (UI interview Q206). This prototype can show an unavailable Refresh state without running a timer.', motionNote, mockNote],
  },
  {
    id: 'staff-full', group: 'staff', title: 'Applicants · roster full', scene: 'staff', variant: 'full', overlay: 'applicants',
    description: 'The full-capacity state keeps the same swipeable paper resumes and browsing controls while preventing hiring.',
    elements: [
      element('Capacity status', 'Show current/max and a full-roster explanation; player can expand or fire a chef.', 'Static readable status; no alert shake.'),
      element('Disabled Hire', 'The current resume’s Hire action is unavailable at the limit. Browsing remains available; do not automatically replace a chef or open a firing flow.', 'No click animation or shortage popup. Preserve cost legibility and disabled semantics.'),
      element('Refresh', 'Refresh is independent from capacity and may remain available when its cooldown permits.', 'Candidate set crossfades for 180 ms if refreshed.'),
      element('Header X', 'Close resume browsing and restore its originating roster/editor view. Omit the redundant Back to staff footer button; system Back has the same dismissal behavior.', 'Popup fades out over 160 ms and restores focus to the opener; reduced motion uses a fade without travel.'),
      closePopup(),
    ],
    notes: ['Insufficient coins also disable only the affected Hire action while retaining its price.', motionNote, mockNote],
  },
  {
    id: 'staff-detail', group: 'staff', title: 'Chef detail · next level', scene: 'staff', variant: 'detail', overlay: 'chef-detail',
    description: 'One chef’s level, growth, current recipe and management actions appear together with a current-to-next speed preview.',
    elements: [
      element('Chef profile', 'Show assigned/unassigned status, level, maximum level, growth and capability ceiling. Background biography is flavor.', 'Profile remains stable during updates; avoid replacing the whole popup.'),
      element('Level Up', 'One affordable tap buys one level in the intended game, updates speed and indicates a newly reached quality tier. No confirmation.', 'Level/stat text crossfades for 140 ms; newly unlocked tier emphasizes for 200 ms. Cost and state update immediately.'),
      element('Recipe action', 'Inspect recipe choice separately from leveling. Unassigned chef placement remains a People-tray interaction.', popupEntrance),
      element('Unassign', 'Release the working cell while preserving chef progression and roster membership.', 'Assigned state crossfades for 140 ms; no money/refund animation.'),
      element('Fire', 'Open a separate named confirmation before permanent removal.', 'Confirmation replaces detail content over 180 ms while the parent roster stays visible.'),
      closePopup(),
    ],
    notes: ['When coins are insufficient, keep next-level preview and cost visible and disable Level Up; no shortage popup. This state is recorded here for later dedicated coverage.', motionNote, mockNote],
  },
  {
    id: 'staff-unaffordable', group: 'staff', title: 'Chef detail · insufficient coins', scene: 'staff', variant: 'unaffordable', overlay: 'chef-detail',
    description: 'A chef’s next-level benefit and cost remain visible when restaurant savings cannot fund the upgrade.',
    elements: [
      element('Next-level preview', 'Retain current-to-next speed and any quality-tier unlock so the player can plan.', 'Static legible preview; do not pulse an unavailable upgrade.'),
      element('Disabled Level Up', 'No purchase and no shortage popup on tap. Keep the cost visible.', 'No press bounce. Intended affordability change enables the action in place over 140 ms.'),
      element('Recipe / Unassign / Fire', 'Other management actions remain available according to assignment; firing still opens confirmation.', 'Standard 70 ms press and 180–220 ms popup transition.'),
      closePopup(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'staff-max', group: 'staff', title: 'Chef detail · maximum level', scene: 'staff', variant: 'max', overlay: 'chef-detail',
    description: 'A chef at their capability ceiling retains final level and stats, with a noninteractive MAX status.',
    elements: [
      element('Final attributes', 'Retain level, speed, reachable tier and ceiling; there is no extra experience track or separate quality purchase.', 'Stable text; no animated upgrade arrow.'),
      element('MAX status', 'Replace Level Up and its cost with MAX. Do not remove the full management area.', 'On reaching max, crossfade action to status over 160 ms; MAX has no hover/press cue.'),
      element('Fire / Unassign', 'Management actions remain available even though leveling is finished.', 'Standard 70 ms press; Fire opens confirmation.'),
      closePopup(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'staff-fire', group: 'staff', title: 'Fire confirmation', scene: 'staff', variant: 'fire', overlay: 'fire',
    description: 'Name the chef and explain permanent removal before offering the destructive action, without a separate refund sentence.',
    elements: [
      element('Named confirmation', 'Identify exactly which chef is removed. It is a UI confirmation, not a second purchase.', popupEntrance),
      element('Cancel', 'Return to the chef detail popup without changing assignment or progression.', 'Confirmation exits for 160 ms; restore focus to Fire.'),
      element('Confirm Fire', 'Mock removal from roster and return to the bottom tray. Intended removal is permanent and frees capacity without refund.', 'Profile fades over 180 ms; count and pagination update immediately; no celebratory effect.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'shop', group: 'shop', title: 'Shop · available goods', scene: 'shop', variant: 'normal',
    description: 'A single catalog combines unlimited essentials, limited rotating goods and an optional floor-style offer on a paper page over the restaurant. Price-only purchase targets retain accessible item-specific Buy names; purchases stay in Shop.',
    elements: [
      element('Stable essentials', 'Buy an unlimited belt tile or ordinary chair for inventory through a coin-price-only target, with no visible Buy label. Retain an accessible Buy plus item name. Intended purchases spend the shown restaurant-coin price; omit catalog section headings and implementation notes.', 'Press 70 ms; fixture inventory count changes immediately and a compact Added cue fades for 180 ms.'),
      element('Rotating goods', 'Show remaining quantity; purchase reduces that offer count. Refresh happens on expedition return, not from a Shop refresh button.', 'Count crossfades for 140 ms; sold-out/disabled state changes in place.'),
      element('Floor style offer', 'Show name, a large repeated-tile pattern and price. Buy once to unlock unlimited floor use; no rarity badge or tile quantity.', 'Immediate purchase; text-only style-unlocked toast appears beside coin balance for about 2.2 s, then fades 200 ms.'),
      element('Restaurant coin count', 'Restaurant purchases use coins, never expedition salvage. Clear the floating HUD button’s stock sparkle on Shop entry.', 'Balance updates directly; the floating Shop sparkle fades over 150 ms.'),
      paperReturn(),
    ],
    notes: ['At most one floor style appears per refresh and none is guaranteed. Furniture functions and all prices remain open.', motionNote, mockNote],
  },
  {
    id: 'shop-owned', group: 'shop', title: 'Shop · style owned', scene: 'shop', variant: 'owned',
    description: 'A purchased floor-style offer remains in its slot until the next rotation.',
    elements: [
      element('Owned floor-style card', 'Keep the pattern and name; replace the price-only purchase target with Owned. Exclude this style from future shop selections.', 'Owned crossfades in over 160 ms; card neither disappears nor collapses.'),
      element('Owned status', 'Noninteractive. Apply the style later in the restaurant Floor layer; buying it did not move the player there.', 'No press animation or repeated unlock toast.'),
      paperReturn(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'shop-unaffordable', group: 'shop', title: 'Shop · insufficient coins', scene: 'shop', variant: 'unaffordable',
    description: 'Unaffordable offers retain their preview and price so the player can plan purchases.',
    elements: [
      element('Disabled purchase price', 'Cannot purchase; no shortage dialog appears on tap. Other affordable offers may remain active.', 'Muted target has no press bounce. Enable in place over 140 ms when affordability changes in the intended game.'),
      element('Offer details', 'Pattern, quantity and price remain legible even when unavailable.', 'Static presentation; no flashing warning.'),
      paperReturn(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'workshop', group: 'workshop', title: 'Workshop · three upgrade tracks', scene: 'workshop', variant: 'normal',
    description: 'Hull, Harpoon and Collector cards appear together on the shared paper page over the restaurant, with current level, next benefit and salvage cost. The upper-right curled corner returns to the originating restaurant.',
    elements: [
      element('Upgrade cards', 'Compare maximum hull, reeling strength and pickup reach. Upgrade buys one level immediately with salvage; no confirmation.', 'Press 70 ms; level/stat/next cost crossfade for 140 ms while card positions remain stable.'),
      element('Salvage balance', 'Shows banked upgrade currency, separate from restaurant coins and expedition result totals.', 'Update directly; optional 180 ms numeral emphasis without counting through intermediate values.'),
      element('Submarine preview', 'Selected equipment milestones may change hull panels/harpoon/collector art while retaining silhouette and footprint.', 'New part crossfades over 220 ms; avoid changing scale or implying a bigger hitbox.'),
      paperReturn(),
    ],
    notes: ['Live service and passive charging continue in intended gameplay; entering from Edit preserves paused restaurant state.', motionNote, mockNote],
  },
  {
    id: 'workshop-max', group: 'workshop', title: 'Workshop · completed track', scene: 'workshop', variant: 'max',
    description: 'A maximum upgrade track retains its full card, final level and final stat.',
    elements: [
      element('MAX card', 'Replace Upgrade and salvage cost with noninteractive MAX; remove the next-stat arrow. Other tracks remain independent.', 'Crossfade purchase area to MAX over 160 ms; keep full-card geometry.'),
      element('Submarine preview', 'Retain any visible purchased equipment changes across restaurant dock, Workshop and expedition.', 'No repeated unlock celebration on scene entry.'),
      paperReturn(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'workshop-unaffordable', group: 'workshop', title: 'Workshop · insufficient salvage', scene: 'workshop', variant: 'unaffordable',
    description: 'The next level remains inspectable with its stat preview and cost, while Upgrade is disabled.',
    elements: [
      element('Disabled Upgrade', 'No purchase and no shortage popup on tap. Keep cost legible.', 'No press animation; availability can crossfade over 140 ms when banked salvage changes.'),
      element('Current → next stat', 'Retain comparison for planning; the disabled state does not hide the upgrade benefit.', 'Static values and arrow; no tempting pulse on a disabled control.'),
      paperReturn(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expedition-start', group: 'expedition', title: 'Preparation · Start', scene: 'expedition-start', variant: 'ready',
    description: 'The submarine waits on the ocean bed with Start and a Sushi Bar airlock. Equipment and future reward previews are omitted.',
    elements: [
      element('Start', 'Begin the journey and consume readiness in intended gameplay. Opening preparation alone did not spend it.', '70 ms press, then preparation overlay fades over 180 ms; travel controls appear after the opener touch is consumed.'),
      element('Sushi Bar airlock', 'Return to restaurant, preserving readiness and recentering on cleared floor.', 'Scene crossfade for 200 ms; curtain gives a small 120 ms press response.'),
      element('Submarine', 'Illustrative starting ship; no steering is active before Start.', 'Quiet 2 px vertical idle over 2 s. Reduced motion keeps it stationary.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expedition-travel', group: 'expedition', title: 'Travel · status HUD', scene: 'expedition', variant: 'travel',
    description: 'A continuous portrait playfield with hull upper-left, run salvage centered and pause upper-right. The wireframe advances using explicit demo controls.',
    elements: [
      element('Playfield steering', 'Intended steering is a relative drag; ship does not snap to touch. Two independent touches allow steering and firing.', 'Ship follows lateral input directly; scenery scrolls at intended travel speed. No smoothing that delays a dodge.'),
      element('Hull meter', 'Continuous durability proportion with submarine icon; no current/max numeric readout.', 'Damage changes fill over 120 ms with a brief ship hit flash. Low hull pulse stays confined to the meter.'),
      element('Run salvage', 'Shows pickups from this expedition, not banked balance or income rate.', 'Pickup attraction follows intended range; numeral updates directly with a 160 ms icon cue.'),
      element('Pause', 'Open the centered Paused card and freeze expedition play.', 'Freeze immediately; pause card enters over 220 ms with a 160 ms scrim.'),
    ],
    notes: ['Demo controls advance review states explicitly. No continuous steering physics, pickups, hull damage, hazards or elapsed travel run here.', motionNote],
  },
  {
    id: 'expedition-encounter', group: 'expedition', title: 'Encounter · harpoon ready', scene: 'expedition', variant: 'encounter',
    description: 'An unhooked creature shows a full name/resistance bar and a lower-right harpoon target.',
    elements: [
      element('Creature bar', 'Appears when the shooting window opens and stays full while aiming. It is resistance, not time until escape.', 'Name/bar fade in over 160 ms; keep the row below the top status HUD.'),
      element('Harpoon', 'One fresh press fires upward from the ship; holding does not repeat. The target remains anchored lower-right.', 'Pressed icon compresses for 70 ms; cooldown mutes it and fills a ring, with no numeric timer or extra HUD.'),
      element('Creature warning', 'Near shooting-window expiry, creature becomes restless before swimming away; no countdown is shown.', 'Fins and bubbles quicken locally. Departure follows a readable upward swim, with no camera shake.'),
      element('Demo Hook transition', 'A wireframe-only control opens pursuit; it does not test aiming or hits.', 'Short 180 ms crossfade to the selected pursuit fixture.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expedition-pursuit', group: 'expedition', title: 'Pursuit · following range', scene: 'expedition', variant: 'pursuit',
    description: 'A hooked creature and ship share forward speed. A narrow vertical following strip tracks lateral position.',
    elements: [
      element('Following strip', 'About two ship widths as an initial target, with no top/bottom boundary or forward-distance test.', 'Strip follows the creature horizontally without lag; low-opacity patterned treatment stays quieter than attacks.'),
      element('Resistance bar', 'Drain only while following in range. Shots themselves did not lower it.', 'Fill responds linearly to intended reeling progress; no decorative spring or delayed catch.'),
      element('Cable', 'Leaving range pauses reeling and begins a grace period. Tautness, color and fraying are the only recovery cues; no return arrow or grace countdown.', 'Cable tightens immediately, with increasing fray as grace runs out; recovery returns it over 120 ms.'),
      element('Pause', 'Freeze expedition, including encounter timers and progress.', popupEntrance),
    ],
    notes: ['Standard attacks must leave a usable safe position inside the strip. No pursuit calculation or timer runs in this fixture.', motionNote],
  },
  {
    id: 'expedition-danger', group: 'expedition', title: 'Pursuit · attack / low hull', scene: 'expedition', variant: 'danger',
    description: 'Attack hatching, strained cable and a low-hull meter demonstrate distinct warning channels.',
    elements: [
      element('Attack strip', 'Amber diagonal hatching and lightning identify the affected vertical band. Warning does not track the submarine.', 'A 160 ms fade reveals the warning; intended windup holds it before discharge. No full-screen flashing.'),
      element('Low-hull meter', 'Warning color and gentle pulse stay at the hull meter; omit a screen-edge tint.', 'Opacity emphasis cycles over 1.2 s; reduced motion uses a steady warning icon/color.'),
      element('Strained cable', 'Out-of-range grace can expire and break the cable. A missed pursuit earns no recipe and cannot be rehooked.', 'Increasing local fray precedes a brief 180 ms cable snap/fade; no return arrow.'),
      element('Impact feedback', 'Intended hits reduce hull and set pursuit progress back slightly, with no forced sideways knockback.', 'Ship flashes locally for 120 ms with a brief protective cue; steering remains responsive.'),
    ],
    notes: ['Danger combinations here are visual examples, not tuned hazard scheduling. Use labeled patterns so warnings remain distinct without color.', motionNote],
  },
  {
    id: 'expedition-pause', group: 'expedition', title: 'Pause card', scene: 'expedition', variant: 'pause', overlay: 'pause',
    description: 'A minimal centered Paused card overlays the frozen saved expedition. Resume and Return early sit side by side without an eyebrow or explanatory paragraph.',
    elements: [
      element('Paused card', 'Show only the Paused title and side-by-side Resume and Return early actions. Omit Expedition preserved and the explanatory sentence. Outside taps leave the card open and world frozen; reopening an unfinished expedition restores this same card.', popupEntrance),
      element('Resume', 'Close the card and start a visible countdown; do not resume immediately or consume the menu tap as steering.', 'Card fades out for 160 ms; countdown appears in place with an opacity transition.'),
      element('Return early', 'Open a concise confirmation stating the retained-reward and no-completion-bonus outcome in one sentence. Intended unfinished catches still earn no recipe.', 'Confirmation content replaces the card with a 180 ms crossfade.'),
    ],
    notes: ['In intended gameplay, restaurant service proceeds independently while expedition is paused. The prototype holds a static visual fixture.', motionNote],
  },
  {
    id: 'expedition-return', group: 'expedition', title: 'Return early confirmation', scene: 'expedition', variant: 'return', overlay: 'early-return',
    description: 'A short confirmation uses one sentence about keeping earned rewards without a completion bonus, followed by Stay paused and Return early.',
    elements: [
      element('Stay paused', 'Return to Paused without resuming the world.', 'Confirmation exits and pause card returns over 160 ms; restore focus to Return early.'),
      element('Return early', 'End the mock journey and open Returned early results. Intended gameplay retains earned salvage and begins recharge.', 'Scene transitions over 220 ms; no reward subtraction or lost-cargo animation.'),
      element('Retained-reward explanation', 'Use one short outcome sentence, without separate paragraphs about unfinished catches or recharge. Intended rules still retain earned rewards, omit completion bonus and unfinished-catch recipes, and begin recharge. Outside taps keep confirmation open.', 'Static readable text; no timed dismissal.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expedition-resume', group: 'expedition', title: 'Resume countdown', scene: 'expedition', variant: 'resume',
    description: 'A numeral and Returning to ship… form the whole resume cue. The expedition stays frozen until completion without extra Frozen scene or Paused · no steering text. Review playback can be advanced explicitly.',
    elements: [
      element('Countdown', 'Show only the numeral and Returning to ship… in the countdown. Omit Resuming expedition, Scene remains frozen during countdown, Frozen scene and Paused · no steering copy. Intended completion restarts saved timers and play without extra protection or capture progress.', 'Each numeral changes via a 100 ms crossfade with no zoom. Exact countdown duration remains open.'),
      element('Prepared touch', 'A fresh playfield touch may wait during countdown. On completion, anchor to its current position and move only from subsequent drag.', 'No ship movement, snapping or accumulated drag while countdown remains visible.'),
      element('Continue demo', 'Wireframe-only advance returns to a pursuit fixture; it is not an accepted game button.', 'Countdown fades for 120 ms; selected fixture becomes visible without a physics step.'),
    ],
    notes: ['Wireframe playback is explicit to keep review deterministic. Real background/reopen persistence is out of scope.', motionNote],
  },
  {
    id: 'catch-first', group: 'rewards', title: 'Catch cutscene · first discovery', scene: 'catch', variant: 'first',
    description: 'A brief full-screen catch celebration precedes the dedicated recipe award. Rewards are already earned before the presentation.',
    elements: [
      element('Catch illustration', 'Intended cutscene plays for only a few seconds with no Skip button. No hazards continue behind it.', 'Submarine/creature settle into a short 300 ms arrival; restrained bubbles rise then fade over 600 ms.'),
      element('Flow to award', 'After the short cutscene, open the first-discovery recipe card automatically. The review prototype exposes explicit advance to inspect both states.', 'Crossfade to recipe dialog over 200 ms; do not gate retained reward on animation completion.'),
    ],
    notes: ['Cutscene composition and exact duration remain art decisions. Demo Advance is review chrome, not gameplay UI.', motionNote],
  },
  {
    id: 'catch-repeat', group: 'rewards', title: 'Catch cutscene · repeat', scene: 'catch', variant: 'repeat',
    description: 'A repeat catch gets a brief catch presentation, then receipt-only results with its extra salvage bonus.',
    elements: [
      element('Repeat catch', 'Do not open a new-recipe award or NEW marker for an already discovered dish.', 'Reuse the short catch motion without the recipe reveal flourish.'),
      element('Flow to results', 'Go directly from catch cutscene to Expedition complete receipt; include repeat-catch salvage when earned.', '200 ms scene crossfade; no intermediate discovery popup.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'recipe-award', group: 'rewards', title: 'First-catch recipe award', scene: 'catch', variant: 'first', overlay: 'recipe-award',
    description: 'A dedicated discovery card shows the new dish and recipe-wide facts after the brief first catch cutscene.',
    elements: [
      element('Recipe artwork and name', 'Show the earned recipe on a board/roll made from its required material; the Eel fixture uses a copper texture. Material conveys required chef tier without a visible Chef requirement row. Keep tier information accessible and retain the recipe if presentation is interrupted.', 'Card rises 12 px over 220 ms, artwork reveals with a 180 ms fade. Reduced motion removes travel.'),
      element('Recipe facts', 'Show fixed dish price and base preparation time. Required chef quality is conveyed by the roll’s material and an accessible description rather than a visible Chef requirement row. Base time here is distinct from the chef-adjusted picker time.', 'Facts appear together after a short 120 ms fade, without a staggered mandatory wait.'),
      element('Continue', 'Open receipt-only results. This action does not earn the recipe and does not clear its NEW marker in the restaurant picker.', '70 ms press then 200 ms scene crossfade; consume the touch.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'results-complete', group: 'rewards', title: 'Results · expedition complete', scene: 'results', variant: 'complete',
    description: 'Completion uses its own background with a salvage receipt and one Restaurant continuation.',
    elements: [
      element('Salvage receipt', 'Show pickups, repeat-catch bonus only when earned, completion bonus and total earned this run; not the banked balance.', 'Rows fade in together over 160 ms. Total is final immediately; avoid count-up delaying continuation.'),
      element('Tier notice', 'When a tier opens, show its name and material icon with a brief future-expedition explanation. No new-species preview or separate reveal.', 'Inline notice fades in over 160 ms; no extra Continue step.'),
      element('Restaurant', 'Return to recentered cleared floor, with recharge and rewards retained in intended gameplay. No Workshop shortcut on results.', '70 ms press and 220 ms crossfade; restaurant earnings notice can appear beside cash balance afterward.'),
    ],
    notes: ['Results omit a recipe recap. The neutral completion background is a wireframe placeholder for future art.', motionNote, mockNote],
  },
  {
    id: 'results-early', group: 'rewards', title: 'Results · returned early', scene: 'results', variant: 'early',
    description: 'Returned early has a distinct background and keeps already earned salvage in the same receipt structure.',
    elements: [
      element('Outcome title', 'Clearly identify voluntary early return.', 'Title fades in with the receipt over 160 ms; no failure alarm.'),
      element('Completion bonus', 'Show zero with a short explanation that the route was unfinished. Do not subtract already earned salvage.', 'Static zero and explanatory text; no loss animation.'),
      element('Restaurant', 'Return to recentered restaurant and begin the intended recharge cycle.', '70 ms press, 220 ms crossfade.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'results-hull', group: 'rewards', title: 'Results · hull depleted', scene: 'results', variant: 'hull',
    description: 'Hull depleted uses a distinct background, keeps earned rewards and shows no completion bonus.',
    elements: [
      element('Outcome title and receipt', 'Explain hull depletion and retain pickups/earned bonuses. Do not imply repair charge, lost rewards or permanent hull damage.', '160 ms entrance fade; omit prolonged camera shake or flashing warning.'),
      element('Completion bonus', 'Show zero with the unfinished-route explanation.', 'Static receipt row matching other outcomes.'),
      element('Restaurant', 'Return to restaurant. A future expedition starts with full upgraded hull after charging.', '70 ms press, 220 ms scene crossfade.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expansion', group: 'layout', title: 'Expansion · selected patch', scene: 'restaurant', variant: 'expanded', overlay: 'expansion',
    description: 'A highlighted garbage patch opens a compact confirmation with only a title, Cancel and a Clear button carrying the coin cost. Clearing remains available from live or edit mode.',
    elements: [
      element('Patch footprint', 'Center the selected patch. Unselected patches have no prices; outside taps leave the card open.', 'Camera glide 300 ms; footprint outline 160 ms. No extra full-screen zoom.'),
      element('Confirmation title', 'Ask whether to clear the highlighted patch. Omit expansion number, panel number, dimensions, separate cost row, explanatory copy and permanence notice.', 'Title enters with the card over 220 ms. Keep the confirmation immediately readable without a stagger.'),
      element('Clear with cost', 'Show the coin cost once, inside Clear. Mock a permanent clear and reveal usable floor; the intended game spends that cost immediately with no refund.', 'Garbage fades locally over 350 ms; card leaves over 160 ms. Logic does not wait for the debris animation.'),
      element('Cancel', 'Close the card without clearing or paying and preserve Live/Edit mode. Cancel is the sole visible dismissal control; omit the redundant header X. System Back still cancels.', 'Card lowers 8 px and fades over 160 ms; remove selected outline over 100 ms and restore focus to the selected patch.'),
    ],
    notes: ['The prototype clearance is a navigation fixture and may reveal the dock for review. It does not implement patch adjacency, currency deduction or progression. The accepted capacity/customer-arrival benefits and permanent-clear rule remain, without explanatory copy in this card.', motionNote],
  },
  {
    id: 'expansion-unaffordable', group: 'layout', title: 'Expansion · insufficient coins', scene: 'restaurant', variant: 'expanded', overlay: 'expansion',
    description: 'Use the same minimal clearance confirmation, with Clear greyed out and its coin cost retained on the button. No shortage text or additional notice appears.',
    elements: [
      element('Disabled Clear', 'Grey out Clear when coins are insufficient. Keep the cost on that button and the selected patch highlighted; show no balance comparison, shortage reason or extra dialog.', 'Muted target has no press animation. Intended affordability changes update the enabled appearance over 140 ms in place.'),
      element('Cancel', 'Close the card and preserve the underlying restaurant mode. Omit a header X; system Back also cancels.', 'Card exit 160 ms; footprint outline fades 100 ms and focus returns to the patch.'),
      element('Highlighted garbage', 'Continue to show exactly which footprint the offer concerns.', 'Static highlighted boundary; avoid looping alarm animation.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'inventory-empty', group: 'restaurant', title: 'Inventory · no belt tiles', scene: 'restaurant', variant: 'edit',
    description: 'An open Layout tray shows zero belt inventory with a short, nonmodal message over the floor-only editor. There is no shortage dialog or forced navigation choice.',
    elements: [
      element('Inventory toast', 'Briefly explain that belt tiles are exhausted. Keep the floor, layer icons and inventory interactive; show no Shop or Keep editing action inside the message.', 'Fade in over 180 ms, hold for about 2.2 s and fade out over 180 ms. Repeated feedback replaces one cue. Reduced motion uses the same short fades without travel.'),
      element('Zero-count inventory item', 'Retain its identity and zero count. The intended game disables empty-cell extensions without closing path mode; existing-neighbor reuse and latest-tile tools remain available.', 'Disabled extensions have no press effect or shortage popup. Full-game available reuse targets retain the slow 1.4 s pulse.'),
      element('Layer and Live controls', 'Use the same right-side layer stack, tray toggle and top-right Live action as other edit views. The ordinary floating Shop remains available independently of the toast.', 'Layer change opens content over 160 ms; Live fades edit chrome over 160 ms. The toast does not take focus or delay either action.'),
    ],
    notes: [floorOnlyNote, 'The current fixture opens Layout with the tray visible. The intended game retains inline path-placement controls at zero inventory; the toast adds no modal decision or automatic exit.', motionNote, mockNote],
  },
  {
    id: 'component-restaurant-hud', group: 'components', title: 'Restaurant HUD · floating Shop', scene: 'component', variant: 'restaurant-hud', component: 'restaurant-hud',
    description: 'The shared restaurant HUD follows the reference placement: savings at the upper-left and a floating Shop directly below. It is rendered independently here and in every restaurant state.',
    elements: [
      element('Fixed savings', 'Styled coin count stays in the upper-left as the restaurant pans. An earnings line reserves space even when absent; +420 while away appears there without moving the Shop button. Earnings add no background panel.', 'Amounts update immediately; earned text fades in for 120 ms, holds for about 2.2 s and fades out for 200 ms. Camera movement never moves the HUD.'),
      element('Floating Shop', 'Open Shop from Live or Edit on any panel. Returning restores the same view and exact camera position. The button has no doorway or floor footprint.', 'Press feedback: 0.97 scale for 70 ms. Scene crossfade takes 200 ms; no camera movement or constant button bounce.'),
      element('Stock cue', 'A small sparkle belongs to the floating Shop button and clears when Shop opens.', 'Proposed subtle sparkle loop: 1.8 s; on entry fade out for 150 ms. Reduced motion keeps the cue static.'),
    ],
    notes: ['The user chose the reference layout with existing Sushi Loop controls only. Workshop remains a compact physical hut beside the submarine; the reference’s level meter, Settings, Tasks and extra Workshop shortcut are outside this wireframe.', motionNote, mockNote],
  },
  {
    id: 'component-editor-controls', group: 'components', title: 'Editor controls · layers & tray', scene: 'component', variant: 'editor-controls', component: 'editor-controls',
    description: 'The shared editor-controls renderer is isolated here and reused in every combined edit view. Review right-side layers, top-right Live and bottom-tray states together. People reuses the roster tray; Layout and Floor use the same edge-caret pagination pattern.',
    elements: [
      element('Top-right Live', 'Return to live mode with immediate edits retained and no confirmation. The editor omits Service paused text; intended NPC and belt pause semantics remain unchanged.', 'Press 70 ms; edit chrome fades over 160 ms. State changes on input rather than at the end of the fade.'),
      element('Vertical layer stack', 'People, Layout and Floor buttons remain at the right, outside the tray, with accessible names and selected state. Only the selected layer shows its adjacent name, including while its tray is collapsed.', 'The stack follows the tray top edge over 200 ms with ease-out. Selected title and outline crossfade over 140 ms; the stack remains fixed while the restaurant floor pans.'),
      element('Active-layer toggle', 'Tap the selected layer to collapse its tray; tap it again to reopen the same layer. Collapsing retains the selected layer and fixture selection.', 'Tray height and stack position change together over 200 ms. Reduced motion applies the collapsed or expanded positions immediately.'),
      element('Different-layer selection', 'Selecting a different layer opens its content, including from a collapsed tray.', 'Content changes immediately; tray height and stack position ease to the new content height over 200 ms.'),
      element('People roster tray', 'Render the same compact RosterTray as its isolated page and Staff scene, with three profiles per row and inline left/right carets. A profile tap opens stats and a drag exposes placement; no separate Omar inventory card.', 'The shared drag ghost follows input directly. Pagination crossfades content over 160 ms without shifting the layer controls.'),
      element('Layout pagination', 'Layout inventory uses two items per page with carets at the same row’s left and right edges. Omit a visible page counter; announce the current page accessibly and disable unavailable directions.', 'A page-content crossfade takes 160 ms; targets and tray geometry stay stable.'),
      element('Floor thumbnails', 'Floor content uses two thumbnail-only choices per page, with carets on the same row at the left and right edges and no visible page number, style names, Owned labels or instructions. Preserve accessible style names and selected semantics.', 'Selected thumbnail outline appears over 100 ms; pattern changes can crossfade over 120 ms.'),
    ],
    notes: ['The component demonstrates presentation fixtures only. Shared revisions must update this page and the combined restaurant edit, floor, selected-object and empty-inventory views.', motionNote, mockNote],
  },
  {
    id: 'component-roster-tray', group: 'components', title: 'Roster tray · paged profiles', scene: 'component', variant: 'roster-tray', component: 'roster-tray',
    description: 'The shared bottom roster tray is isolated here and reused over the restaurant. Inspect three compact profiles per row, tap-versus-drag behavior and edge-caret pagination without visible page numbers. The same tray also supplies the editor People layer.',
    elements: [
      element('Chef profile targets', 'Each profile shows portrait, name and assignment state. Tap opens the selected chef’s level and stats in a popup. Dragging uses the same affordance as the integrated roster; a valid starter-floor drop previews assignment and keeps the tray open. Full-game placement validation remains out of scope.', 'Tap press 70 ms. After 8 px of drag, source fades over 120 ms and a portrait ghost follows directly. Valid outline appears immediately; invalid or cancelled drag removes the ghost immediately. A future 160 ms snap-back is proposed, with direct restoration under reduced motion.'),
      element('Paged bottom tray', 'Display three compact profiles per row with current/max capacity. Place Previous and Next carets at the left and right edges on that same row. Hide visible page numbers while announcing page changes accessibly. Carets have at least 44 × 44 px targets; page changes keep the tray and restaurant visible.', 'Tray enters over 200 ms and exits over 160 ms. Profile content crossfades over 160 ms on pagination, without replacing the scene.'),
      element('Job applicants', 'Open the shared paper-resume view and preserve the roster as its return context.', popupEntrance),
      element('Tray close', 'Close the tray without changing chef assignments or the originating restaurant mode/camera. Do not add a fullscreen roster or scene-wide scrim.', 'Exit over 160 ms; return focus to Staff in the integrated view. Reduced motion uses a fade.'),
    ],
    notes: ['Changes to this shared tray must propagate to the isolated page, editor People layer and staff/restaurant compositions. Four fixture chefs show two pages, with three profiles on the first. The drag ghost and neutral footprint demonstrate presentation, with valid drops limited to visible cleared starter floor and no game assignment simulation.', motionNote, mockNote],
  },
  {
    id: 'component-applicant-resume', group: 'components', title: 'Applicant resume · swipe browsing', scene: 'component', variant: 'applicant-resume', component: 'applicant-resume',
    description: 'The shared paper resume and its browsing controls are isolated here and reused in applicant popups. Review one visible candidate at a time, diverse profiles and hiring states.',
    elements: [
      element('Paper resume', 'One applicant’s portrait, occupation, background, strengths, growth, maximum level and reachable quality are visible on a paper sheet. Left/right swipes browse; they do not commit a hire or rejection.', 'Resume enters over 180 ms. A horizontal drag follows the pointer directly; release settles the selected page over 200 ms. No flying-away paper or permanent dismissal; reduced motion changes content immediately.'),
      element('Accessible browsing', 'Previous and Next offer the same navigation with 44 × 44 px targets. Show position within the remaining applicant pool and disable unavailable directions.', 'Button press 70 ms followed by the same 200 ms horizontal settle. State updates on input.'),
      element('Explicit Hire', 'The visible cost and Hire action apply to this applicant. Hiring joins the unassigned roster, removes the offer without replacement, and preserves resume browsing. Full capacity or insufficient coins disables Hire.', 'Apply the fixture update immediately. Resume content crossfades over 160 ms; Hired cue fades over 180 ms. Disabled Hire has no press effect.'),
      element('Refresh', 'Replace the remaining set, reset to its first resume and enter the accepted free real-time cooldown. No pinned applicant or confirmation step.', 'Set crossfades over 180 ms. Refresh remains stable while unavailable; countdown visibility is still deferred.'),
    ],
    notes: ['The user confirmed swipes for browsing with explicit Hire. Hiring rules and cooldowns are fixtures; no economy or real timer runs. Shared changes must propagate to available/full-capacity applicant stories.', motionNote, mockNote],
  },
  {
    id: 'component-paper-page', group: 'components', title: 'Paper page · curled return corner', scene: 'component', variant: 'paper-page', component: 'paper-page',
    description: 'The shared paper-page treatment used in Shop and Workshop is isolated here over the actual restaurant floor plan. Its curled upper-right corner is the return target.',
    elements: [
      element('Paper surface', 'Present catalog or upgrade content on a paper sheet while retaining the originating restaurant behind it. Shop uses one combined catalog without section headings or implementation notes; Workshop shows its upgrade tracks on the same surface.', 'A 200 ms paper entrance fade is proposed; preserve underlying restaurant geometry and camera. Current wireframe entry is direct, and reduced motion also updates the view directly.'),
      paperReturn(),
      element('Return semantics', 'The curl replaces the old Restaurant bar and Sushi Bar doorway. Return to the same Live/Edit mode, open/collapsed layer state and exact camera position. Give the icon-only corner an accessible Return to Restaurant label and a target of at least 44 × 44 px.', 'Press affects the curl without moving nearby content. Current navigation is immediate and restores focus to the Shop or Workshop opener without scrolling the floor. A future 200 ms exit fade must not delay the state change.'),
    ],
    notes: ['The paper surface and corner are shared with Shop and Workshop rather than duplicated gallery artwork. Corner growth and opener focus restoration are implemented; paper entrance/exit fades remain proposed. They navigate review fixtures only; no gameplay currency, production or timer logic runs.', motionNote, mockNote],
  },
  {
    id: 'component-money', group: 'components', title: 'Currency display', scene: 'component', variant: 'money', component: 'money',
    description: 'The same currency renderer used in restaurant HUDs, Shop prices, Workshop salvage and reward receipts is shown here in isolation. Review a shared change once and it propagates to the full scenes.',
    elements: [
      element('Currency icon', 'Identify restaurant coins or expedition salvage without implying that the currencies can exchange. Supply the currency identity in the accessible label.', 'A relevant event can pulse the icon over 180 ms; coalesce overlapping events. Reduced motion keeps a stable icon.'),
      element('Styled amount', 'Use stable aligned numerals with no cream/yellow container. The surrounding scene decides whether the amount is savings, price or run reward.', 'Update immediately. Use a short 140 ms emphasis rather than counting through intermediate values.'),
      element('Earned/unlocked notice', 'Transient text belongs beside the associated balance; zero earnings should suppress an earnings notice. It never blocks the amount.', 'Fade in 120 ms, hold about 2.2 s and fade out 200 ms; no collection action.'),
    ],
    notes: ['Amount, currency and context are inputs to the shared renderer. This page is a visual fixture with illustrative values.', motionNote],
  },
  {
    id: 'component-character', group: 'components', title: 'Character portrait', scene: 'component', variant: 'character', component: 'character',
    description: 'The same character renderer used for draggable roster profiles, paper resumes and detail popups is shown here. Restaurant character art is omitted during the floor-plan-only review. Shared portrait revisions update each context.',
    elements: [
      element('Recognizable silhouette', 'Keep a person’s hair, face, skin tone and signature outfit consistent across small scene art and large portraits. Include varied ages, occupations and backgrounds.', 'Idle movement is restrained: 2 px over 2 s. Keep portrait panels still during inspection; reduced motion removes decorative motion.'),
      element('Identity and biography', 'Name the character where the player is inspecting a profile. Background is flavor and does not determine cooking statistics, patience, cost or capability.', 'Profile text appears with its parent row or popup; avoid separate staggered biography reveals.'),
      element('Reaction states', 'Preserve recognition in idle, waiting, eating, delighted and trapped states. A satisfied preference uses a short body bounce with the existing happy cue.', 'Delighted reaction bobs 4 px over 300 ms; restore the neutral pose without continuous bouncing.'),
    ],
    notes: ['The current monochrome art is a wireframe placeholder; the final cast and doodle illustrations remain subject to review.', motionNote],
  },
  {
    id: 'component-dock', group: 'components', title: 'Submarine dock & Workshop hut', scene: 'component', variant: 'dock', component: 'dock',
    description: 'The same dock-and-hut renderer used in the full floor plan and restaurant is shown here with access and charging states. Landmark changes propagate to both layouts.',
    elements: [
      element('Combined footprint', 'Submarine and Workshop share one 3 × 3 floor-cell footprint. Place the hut to the submarine’s right and keep targets separate; taller hut artwork can grow upward without covering the submarine.', 'The footprint stays stable between ready, charging and locked states; avoid scale changes or landmark overlap.'),
      element('Submarine target', 'Ready tap opens expedition preparation; charging tap keeps the restaurant visible and gives local status. Locked targets are unavailable.', 'Target press 70 ms; ready headlight gently pulses over 1.6 s. Charging and locked states have no ready pulse.'),
      element('Local battery', 'Charge is visible at the dock only. Omit a persistent top-HUD battery and separate Ready badge.', 'Intended charge fill is linear; the component fixture remains static until a review state changes.'),
      element('Charging message', 'Show Charging with remaining time near the dock after a tap; do not open an unavailable start screen.', '120 ms entrance fade, about 2.2 s hold and 180 ms exit. Repeated taps replace one cue rather than stacking notices.'),
      element('Workshop hut target', 'Separate target to the submarine’s right within the shared footprint. It opens Workshop and preserves the originating Live/Edit mode; locked coverage prevents navigation.', '70 ms press followed by a 200 ms scene crossfade. Consume the opener touch.'),
      element('Locked rag covering', 'Cover both landmarks with patchwork rags and small peek openings. Reveal recognizable fragments through the cloth instead of faded full landmarks or a Future access notice.', 'Static cloth while locked. Proposed unlock removes the covering in a local 240 ms fade; reduced motion reveals immediately.'),
    ],
    notes: ['The 3 × 3 footprint and right-side Workshop placement are current direction. Connected access requirements and precise middle-panel approach remain floor-plan decisions. This component does not clear garbage or run recharge.', motionNote],
  },
  {
    id: 'component-recipe-tile', group: 'components', title: 'Recipe catalog tile', scene: 'component', variant: 'recipe-tile', component: 'recipe-tile',
    description: 'The same recipe-tile renderer used inside every chef recipe picker is shown here with current, inspected, NEW, above-tier and undiscovered treatments. Revisions carry through to all picker stories.',
    elements: [
      element('Tier board and dish', 'Discovered tiles show artwork, name and fixed coin selling price on their tier’s material board, without visible Wood or other tier labels. Undiscovered tiles show unidentified engraved silhouettes without revealing or inventing a price. Distinct grain/metal patterns convey the tier beyond color; retain it in accessible descriptions.', 'Artwork may crossfade on discovery over 180 ms; no pulsing mystery teaser. Material stays consistent with the fixed details board.'),
      element('Current and inspected outlines', 'Keep current cooking assignment and inspection selection distinct, including when they are the same tile. Tap inspection does not Prepare.', 'Press 70 ms; selected outline changes over 100 ms. The fixed details panel crossfades separately over 140 ms.'),
      element('NEW marker', 'Present until inspected in the restaurant picker. Above-tier inspection also clears it; the expedition award does not.', 'Marker fades away over 140 ms after inspection, with no constant attention loop.'),
      element('Unavailable tile', 'A discovered above-tier tile remains inspectable with muted artwork; eligibility is handled by the picker’s Prepare area.', 'Retain target response and selection outline. Do not turn an inspectable tile into a disabled tap target.'),
    ],
    notes: ['This page reviews the tile itself; the recipe-picker pages review catalog order, scrolling and the fixed details/Prepare panel.', motionNote],
  },
  {
    id: 'component-hull-meter', group: 'components', title: 'Hull meter', scene: 'component', variant: 'hull-meter', component: 'hull-meter',
    description: 'The same compact hull renderer used in travel, encounter, pursuit and frozen expedition views is shown here at normal and low durability. Shared warning changes propagate to those scenes.',
    elements: [
      element('Hull identity and fill', 'Use a submarine icon and continuous durability proportion in the upper-left status row. Omit a visible current/max numeric readout.', 'Fill responds to intended damage over 120 ms; expose an accessible meter value even though visible text is compact.'),
      element('Low-hull warning', 'Keep warning color, symbol and gentle pulse confined to the meter. Do not tint the screen edges.', 'Proposed emphasis cycles over 1.2 s. Reduced motion uses a steady warning indication.'),
      element('Frozen state', 'Pause preserves the visible value and warning context; the component does not independently advance or restore hull.', 'Stop any decorative warning pulse during the paused fixture; do not reset the fill.'),
    ],
    notes: ['The low-hull threshold and damage values remain gameplay tuning. This gallery changes visual fixtures only.', motionNote],
  },
  {
    id: 'component-upgrade-card', group: 'components', title: 'Workshop upgrade card', scene: 'component', variant: 'upgrade-card', component: 'upgrade-card',
    description: 'The same upgrade-card renderer used for Hull, Harpoon and Collector in every Workshop state is shown here. Changing its structure, spacing or action treatment updates all tracks.',
    elements: [
      element('Track and current → next stat', 'Keep current level, benefit identity and next-level comparison together. The parent supplies hull, reeling strength or pickup reach and the salvage cost.', 'Updated level and benefit crossfade over 140 ms without collapsing or moving the card.'),
      element('Upgrade target', 'Affordable tap buys one level without a confirmation in the intended game. Unaffordable state keeps preview/cost and disables the action.', '70 ms press when active; disabled state has no bounce or shortage dialog.'),
      element('MAX state', 'Retain the full card, final level and final stat. Replace Upgrade/cost with noninteractive MAX and remove the next-value arrow.', 'Purchase area crossfades to MAX over 160 ms; no card removal or height change.'),
    ],
    notes: ['This component does not own balance, currency deduction or stat progression. Gallery interactions advance review fixtures.', motionNote],
  },
  {
    id: 'component-receipt', group: 'components', title: 'Salvage result receipt', scene: 'component', variant: 'receipt', component: 'receipt',
    description: 'The same salvage receipt renderer used in complete, early-return and hull-depleted result screens is shown here. Shared receipt changes update every outcome while their backgrounds and titles remain contextual.',
    elements: [
      element('Pickup and bonus rows', 'Show this run’s pickups, repeat bonus only when earned, and completion bonus. Early return/hull depletion show zero completion bonus and an explanation.', 'Rows appear together with a 160 ms fade; avoid mandatory staggered receipt playback.'),
      element('Total earned', 'Show the final run total, distinct from banked salvage or an earning rate. No recipe recap belongs inside this receipt.', 'Amount is final immediately; optional 180 ms emphasis does not gate Restaurant continuation.'),
      element('Outcome explanation', 'Clarify a zero completion bonus without suggesting lost salvage, repair charges or permanent hull damage.', 'Static readable text; no subtraction animation or failure flashing.'),
    ],
    notes: ['The parent results screen owns the title, background, optional tier notice and single Restaurant action.', motionNote],
  },
  {
    id: 'component-tap-target', group: 'components', title: 'Tap target & disabled control', scene: 'component', variant: 'tap-target', component: 'tap-target',
    description: 'The same target/button renderer used for scene navigation, HUD icons, catalog purchases and popup actions is shown here. Shared target changes improve every screen and isolated component.',
    elements: [
      element('Marked target', 'Blue dashed boundaries identify tappable controls in review. Keep transparent HUD targets separated from scene detail; supply accessible labels for icon-only actions.', 'Active press compresses to 0.97 for 70 ms and returns promptly. Minimum target is 44 × 44 CSS pixels.'),
      element('Focus and selected state', 'Keyboard focus stays visible; selected toggles expose their state. Hiding review outlines must not hide keyboard focus.', 'Focus appears immediately; selected outline can crossfade over 100 ms without moving the target.'),
      element('Disabled state', 'Muted actions retain their meaning and cost. Disabled controls do not navigate, purchase or open a shortage message.', 'No press transform, hover invitation or repeated warning on disabled targets.'),
      element('Navigation action', 'The parent provides destination/action. Opener input is consumed so scene change cannot trigger the destination twice.', 'Use the destination’s 160–220 ms popup or scene transition; reduced motion removes travel.'),
    ],
    notes: ['Review-target outlines and game art can evolve independently; shared semantics and touch area remain consistent. This gallery demonstrates presentation-only controls.', motionNote],
  },
];
