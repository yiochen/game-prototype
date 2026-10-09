// Review inventory. These fixtures describe intended UI behavior, not gameplay rules.
const element = (name, behavior, motion) => ({ name, behavior, motion });
const returnDoor = () => element(
  'Sushi Bar doorway',
  'Return to the restaurant. Workshop and expedition returns recenter on cleared floor; Shop preserves the prior view and Live/Edit mode.',
  'Press feedback: 0.97 scale for 70 ms. Scene crossfade: 200 ms; consume the opening touch to avoid a second action.'
);
const closePopup = () => element(
  'Close / system Back',
  'Close the active popup and restore its parent view without applying an unconfirmed choice. Outside taps neither close the popup nor activate the scene underneath.',
  'Popup exits with a 160 ms opacity fade and 8 px downward movement. Return focus to the opener; reduced motion uses a fade only.'
);
const popupEntrance = 'Light scrim fades in over 160 ms; popup rises 12 px over 220 ms. Keep the scene visible. Reduced motion removes travel.';
const motionNote = 'Animation values are proposed review targets. State changes happen on the action, never after an animation finishes.';
const mockNote = 'All values and interaction outcomes are fixtures for review; this story does not run economy, service, physics, clocks, or save logic.';

export const storyGroups = [
  { id: 'layout', title: 'Floor plan' },
  { id: 'components', title: 'Shared components' },
  { id: 'restaurant', title: 'Restaurant' },
  { id: 'recipes', title: 'Recipe picker' },
  { id: 'staff', title: 'Staff & applicants' },
  { id: 'shop', title: 'Shop' },
  { id: 'workshop', title: 'Workshop' },
  { id: 'expedition', title: 'Expedition' },
  { id: 'rewards', title: 'Catch & rewards' },
];

export const stories = [
  {
    id: 'floor-plan', group: 'layout', title: 'Full restaurant floor plan', scene: 'floor-plan', variant: 'overview',
    description: 'Three portrait-width panels form one continuous restaurant. Only the first is usable initially; future floor is blocked by garbage. The middle panel reserves the submarine and a compact Workshop hut.',
    elements: [
      element('Panel guides', 'Reference widths for the camera, not partition walls. Pan across the full plan; retain a finished left wall.', 'A viewport change glides for 300 ms at a fixed scale. No pinch zoom.'),
      element('Floating Shop button', 'Shop belongs to the fixed HUD below the upper-left coin count and uses no restaurant floor cells. This overview offers the same navigation above the plan.', 'Press feedback for 70 ms; scene crossfade takes 200 ms. The button remains fixed while the floor pans.'),
      element('Entry openings', 'Customer entrances sit along the top of each panel. Later access activation is a proposal for review.', 'If route activation is accepted, the entrance changes from muted to active over 180 ms.'),
      element('Garbage patch', 'Tap an adjacent patch to inspect its footprint and open the expansion card. Clear purchases a permanent floor extension in the intended game.', 'Center the selected patch over 300 ms; its outline appears in 160 ms. Clearing uses a local 350 ms debris fade.'),
      element('Submarine and Workshop hut', 'Separate navigation targets close together in panel two. The reserved footprint is kept distinct from workable restaurant cells.', 'Submarine ready light gently pulses over 1.6 s; hut has press feedback only. Neither target has a constant bouncing marker.'),
    ],
    notes: ['The sketch supersedes the earlier two-panel image layout. Exact tile counts, patch shapes, prices, and dock approach remain open.', 'Activating later entries or the dock when a cleared route reaches them is a proposal, not an approved rule.', motionNote, mockNote],
  },
  {
    id: 'restaurant-live', group: 'restaurant', title: 'Live service · starter floor', scene: 'restaurant', variant: 'live',
    description: 'The initial operating restaurant with one chef, a short belt and reachable seats. Fixed HUD controls stay visible while scene landmarks move with the floor.',
    elements: [
      element('Coin count', 'Shows restaurant savings at the upper-left, above the floating Shop button. Styled numerals use no cream/yellow backing container. It stays fixed while panning; no income-rate counter.', 'A sale updates the number immediately; nearby icon pulses for 180 ms with repeated events coalesced.'),
      element('Chef and blackboard', 'Tap the chef/blackboard target to inspect and Prepare recipes without interrupting live service.', 'Chef tool motion loops over 320 ms; it stops when holding one blocked dish. An applied recipe updates the board immediately, then shakes by 2° for 260 ms.'),
      element('Customer preference', 'One first-dish preference per visit, with a countdown ring. A preferred dish changes the existing cue into a happy face.', 'Ring represents the actual remaining time. Cue crossfades for 100 ms, customer bobs 4 px over 300 ms, then cue holds 650 ms and fades for 200 ms.'),
      element('Belt and dishes', 'Dishes follow the belt, including local congestion. These wireframe plates remain illustrative; no service simulation runs.', 'Intended movement is linear at configured belt speed; blocked plates stop without decorative drift.'),
      element('Edit control', 'Enter the editing view; intended service pauses immediately.', 'Press feedback for 70 ms; edit chrome appears over 200 ms.'),
      element('Staff control', 'Open the roster and job-applicant navigation.', 'Open panel over 220 ms with a 160 ms light scrim. Service remains live.'),
      element('Floating Shop and future floor', 'The upper-left Shop button opens its scene from any camera panel in Live or Edit. Returning preserves that view and panel. Garbage remains on the floor and opens a selected patch card; swipe empty floor to pan.', 'Shop has 70 ms press feedback and a 200 ms scene crossfade. It never travels with the camera; selected garbage centers over 300 ms.'),
    ],
    notes: ['Characters have distinct silhouettes, occupations and backgrounds; identity is not a gameplay statistic.', 'HUD controls use clear transparent target outlines for this wireframe. Their touch area is larger than the visible icon.', motionNote, mockNote],
  },
  {
    id: 'restaurant-expanded', group: 'restaurant', title: 'Live service · dock unlocked', scene: 'restaurant', variant: 'expanded',
    description: 'An illustrative cleared middle panel makes the submarine and adjacent compact Workshop hut available, while farther patches remain blocked.',
    elements: [
      element('Scene panning', 'Swipe empty floor or use the wireframe panel controls. HUD remains viewport anchored; chef bubbles, dock and entrances move with the floor.', 'Smooth fixed-scale camera movement; proposed programmatic pan duration is 300 ms.'),
      element('Ready submarine', 'Tap to open expedition preparation. This does not launch or consume readiness; Start does.', 'Full battery stays full while the headlight gently pulses over 1.6 s. Destination enters with a 200 ms crossfade.'),
      element('Workshop hut', 'Tap the compact hut/sign beside the submarine to inspect upgrades.', 'Press for 70 ms; 200 ms scene crossfade. Preserve the mode used to leave the restaurant.'),
      element('Remaining garbage', 'Inspect a neighboring expansion patch without showing all prices on the floor.', 'Selection outline fades in for 160 ms and its bottom-half card rises 12 px over 220 ms.'),
    ],
    notes: ['The cleared layout is an example for navigation review. Unlock requirements and progression timing remain unresolved.', motionNote, mockNote],
  },
  {
    id: 'restaurant-edit', group: 'restaurant', title: 'Edit · layout tools', scene: 'restaurant', variant: 'edit',
    description: 'Editing pauses restaurant characters and belts. Icon-only People, Layout and Floor layers control what the player can select; there is no Save or Cancel step.',
    elements: [
      element('Layer icons', 'Choose People, Layout or Floor. The UI uses icons with accessible names rather than visible layer labels in the intended game.', 'Active-layer outline moves or crossfades over 140 ms; tray content changes over 160 ms.'),
      element('Inventory tray', 'Paginated items can be dragged into valid cells. An invalid drop returns the item; purchases return to inventory when removed from the floor.', 'Picked item lifts 4 px over 100 ms; valid cells outline immediately. Invalid placement settles back over 180 ms with a brief reason.'),
      element('Object selection', 'Tap to select, then drag to move. Selection stays after the drop. A swipe outside the selected object clears selection and pans in that same gesture.', 'Outline appears in 100 ms. Drag follows the finger without easing; release settles to a cell over 120 ms.'),
      element('Belt path controls', 'Neighbors are available for extension; existing neighboring tiles can be reused. Latest-tile Rotate, Remove and X remain available; reaching zero inventory does not close path mode.', 'Available neighbors blink slowly over 1.4 s. Rotation turns 90° over 160 ms; reduced motion changes orientation immediately.'),
      element('Live control', 'Return to live view and resume service. Edit choices are already applied; no confirmation screen.', 'Edit chrome fades over 160 ms and intended scene motion resumes immediately with the mode change.'),
    ],
    notes: ['The wireframe demonstrates tools and selected targets without implementing cell validation, belt connectivity, inventory consumption or persistence.', motionNote],
  },
  {
    id: 'restaurant-floor', group: 'restaurant', title: 'Edit · floor palette', scene: 'restaurant', variant: 'floor',
    description: 'Choose an owned style and paint individual cells or drag a stroke. Painting is cosmetic and can extend beneath furniture.',
    elements: [
      element('Style swatches', 'No brush is selected on entry. Tap a swatch to activate its brush; newest purchases appear first and the free original style last.', 'Selection outline appears over 100 ms. Palette remains in place while painting.'),
      element('Paintable cells', 'Tap paints one cell; dragging paints each crossed cell. Selected style remains active after each stroke.', 'A newly painted cell crossfades its surface over 120 ms. Same-style floor may share a subtle slow ambient flare across multiple cells.'),
      element('Edge pan carets', 'Tap moves four cells; hold continues panning. Keep the brush ready and hide directions that cannot reveal more floor.', 'Proposed four-cell glide is 300 ms. On release, resume paint targeting without clearing the style.'),
      element('Top X', 'Clear the active brush and remain in the Floor layer with the palette open.', 'Brush cue fades for 120 ms; palette does not close or jump.'),
    ],
    notes: ['The shared floor shader is a visual requirement for later art; this wireframe uses a neutral pattern preview.', motionNote, mockNote],
  },
  {
    id: 'restaurant-selected', group: 'restaurant', title: 'Edit · selected object', scene: 'restaurant', variant: 'selected',
    description: 'A selected chair demonstrates local controls, persistent selection, movement and return-to-inventory behavior.',
    elements: [
      element('Selected chair', 'Drag after selecting. Moving an occupied seat carries its customer in the intended game.', 'Chair and occupant track the same drag transform. Selected outline remains after 120 ms cell settling.'),
      element('Rotate target', 'Change the chair’s facing connection to an adjacent belt.', 'Rotate 90° over 160 ms; update the connection immediately on action.'),
      element('Remove target', 'Return a purchased chair to inventory without coin refund. Its customer would retain meal progress and search after service resumes.', 'Object shrinks to 0.9 scale and fades for 160 ms; inventory count changes immediately.'),
      element('Empty-floor swipe', 'Clear selection and pan in one gesture.', 'Selection fades for 100 ms; camera follows the swipe immediately.'),
    ],
    notes: ['Customers and plates affected by edits are documented intent; this review view does not simulate their reactions.', motionNote],
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
    description: 'The saved restaurant scene returns with earnings already credited. A brief amount-only notice appears beside the coin balance; there is no collection popup.',
    elements: [
      element('Coin balance and notice', 'Automatically show the updated savings and earned amount. Suppress this notice when earnings are zero; it does not pause service.', 'Notice fades in over 120 ms, holds for 2.2 s and fades out for 200 ms. No claim action or blocking animation.'),
      element('Restored customers and plates', 'Intended reopen preserves saved transient scene state after aggregate offline credit, then resumes service.', 'Restore directly at saved positions; do not animate a backlog of missed sales or customer visits.'),
      element('Floating Shop sparkle', 'A cue attached to the upper-left HUD button signals refreshed goods until entering Shop. Opening Shop clears it.', 'A quiet sparkle loop over 1.8 s; fade it out for 150 ms on entry. The cue stays attached when panning.'),
    ],
    notes: ['Offline accounting, saving and real-time recharge are out of scope for this prototype. Closing while in edit mode remains an open product decision.', motionNote],
  },
  {
    id: 'recipe-picker', group: 'recipes', title: 'Picker · eligible recipe', scene: 'restaurant', variant: 'eligible', overlay: 'recipes',
    description: 'A large portrait dialog overlays the visible restaurant. Its two-column catalog scrolls above a fixed details panel.',
    elements: [
      element('Catalog tiles', 'Tap a discovered dish to inspect it; inspection leaves the chef’s current recipe intact. Current and inspected recipes have distinguishable outlines.', 'Tile press for 70 ms; selected outline appears for 100 ms. Lower details crossfade over 140 ms without moving the catalog.'),
      element('Fixed recipe details', 'Show dish, fixed selling price, chef-adjusted preparation time and required tier. Exclude base time and belt-loading waits.', 'Details stay anchored while catalog scrolls. Fact changes use a short crossfade, not a number-counting animation.'),
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
      element('Muted discovered tile', 'Tap to view price and tier requirement. Inspection still clears NEW, even when the chef cannot cook it.', 'Artwork is muted rather than hidden. Selection outline remains readable; details crossfade for 140 ms.'),
      element('Preparation time', 'Show an em dash while the chef is ineligible; do not imply a usable adjusted duration.', 'Static value; no timer or progress ring.'),
      element('Disabled Prepare', 'Retain the unavailable action and visible required tier; tapping performs no purchase or shortage popup.', 'Muted outline and text with no press bounce; accessible disabled state.'),
      closePopup(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'recipe-undiscovered', group: 'recipes', title: 'Picker · undiscovered silhouette', scene: 'restaurant', variant: 'undiscovered', overlay: 'recipes',
    description: 'Undiscovered recipes remain engraved silhouettes on tier-material boards and do not reveal dish identity or facts.',
    elements: [
      element('Undiscovered tile', 'A silhouette explains collection space without revealing the upcoming expedition reward. It has no Prepare action.', 'Static engraved silhouette; no teaser pulse or fake NEW badge.'),
      element('Tier board', 'Different materials communicate Wood, Steel, Copper, Silver and Gold; include text so tier is not color dependent.', 'No transition until discovery; later artwork can reveal with a 180 ms crossfade.'),
      closePopup(),
    ],
    notes: ['The neutral wireframe represents material differences with labels and patterns; dish catalog and illustrations are placeholders.', motionNote],
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
    description: 'A compact roster lists portrait, level and assigned status. Job applications open a separate popup; the panel has no tabs.',
    elements: [
      element('Staff capacity', 'Show current and maximum staff in both roster and applicant views. Assigned and unassigned chefs both count.', 'Update directly after hire/fire/expansion; briefly emphasize changed count for 180 ms.'),
      element('Chef row', 'Tap to open a separate detail popup for this chef.', 'Row press 70 ms; detail popup uses the standard 220 ms entrance.'),
      element('Job applicants', 'Open the separate three-candidate popup without replacing the roster with a tab.', popupEntrance),
      returnDoor(),
    ],
    notes: ['Portrait backgrounds describe occupations and histories, while gameplay comparisons use explicit growth, capability and cost attributes.', motionNote, mockNote],
  },
  {
    id: 'staff-applicants', group: 'staff', title: 'Applicants · available capacity', scene: 'staff', variant: 'applicants', overlay: 'applicants',
    description: 'Three deliberately varied candidates expose strengths, growth, maximum level, reachable tier and hiring cost.',
    elements: [
      element('Candidate cards', 'Compare noticeably different tradeoffs; applicants remain until hired or refreshed. A hired slot is left empty rather than replaced.', 'On hire, card fades for 160 ms; remaining cards stay in their positions.'),
      element('Hire', 'Mock one immediate hire into unassigned roster, keeping the applicant popup open. Intended game deducts the visible cost with no confirmation.', 'Press 70 ms; capacity and roster change immediately; local Hired cue fades over 180 ms.'),
      element('Refresh', 'Replace all three candidates and begin a free real-time cooldown. No confirmation and no pinned candidate.', 'Candidate set crossfades over 180 ms. Cooldown stops press feedback until available again.'),
      closePopup(),
    ],
    notes: ['Refresh countdown visibility remains deferred (UI interview Q206). This prototype can show an unavailable Refresh state without running a timer.', motionNote, mockNote],
  },
  {
    id: 'staff-full', group: 'staff', title: 'Applicants · roster full', scene: 'staff', variant: 'full', overlay: 'applicants',
    description: 'The full-capacity state keeps candidate information visible and prevents hiring.',
    elements: [
      element('Capacity status', 'Show current/max and a full-roster explanation; player can expand or fire a chef.', 'Static readable status; no alert shake.'),
      element('Disabled Hire', 'All candidate Hire actions are unavailable at the limit. Do not automatically replace a chef or open a firing flow.', 'No click animation or shortage popup. Preserve cost legibility and disabled semantics.'),
      element('Refresh', 'Refresh is independent from capacity and may remain available when its cooldown permits.', 'Candidate set crossfades for 180 ms if refreshed.'),
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
    description: 'Name the chef and explain permanent removal with no refund before offering the destructive action.',
    elements: [
      element('Named confirmation', 'Identify exactly which chef is removed. It is a UI confirmation, not a second purchase.', popupEntrance),
      element('Cancel', 'Return to the chef detail popup without changing assignment or progression.', 'Confirmation exits for 160 ms; restore focus to Fire.'),
      element('Confirm Fire', 'Mock removal from roster and return to the roster. Intended removal is permanent and frees capacity without refund.', 'Roster row fades over 180 ms; count updates immediately; no celebratory effect.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'shop', group: 'shop', title: 'Shop · available goods', scene: 'shop', variant: 'normal',
    description: 'Stable belt/chair essentials sit beside limited rotating goods and an optional floor-style offer. Purchases stay in Shop.',
    elements: [
      element('Stable essentials', 'Buy an unlimited belt tile or ordinary chair for inventory. Intended purchases spend the shown restaurant-coin price.', 'Press 70 ms; fixture inventory count changes immediately and a compact Added cue fades for 180 ms.'),
      element('Rotating goods', 'Show remaining quantity; purchase reduces that offer count. Refresh happens on expedition return, not from a Shop refresh button.', 'Count crossfades for 140 ms; sold-out/disabled state changes in place.'),
      element('Floor style offer', 'Show name, a large repeated-tile pattern and price. Buy once to unlock unlimited floor use; no rarity badge or tile quantity.', 'Immediate purchase; text-only style-unlocked toast appears beside coin balance for about 2.2 s, then fades 200 ms.'),
      element('Restaurant coin count', 'Restaurant purchases use coins, never expedition salvage. Clear the floating HUD button’s stock sparkle on Shop entry.', 'Balance updates directly; the floating Shop sparkle fades over 150 ms.'),
      returnDoor(),
    ],
    notes: ['At most one floor style appears per refresh and none is guaranteed. Furniture functions and all prices remain open.', motionNote, mockNote],
  },
  {
    id: 'shop-owned', group: 'shop', title: 'Shop · style owned', scene: 'shop', variant: 'owned',
    description: 'A purchased floor-style offer remains in its slot until the next rotation.',
    elements: [
      element('Owned floor-style card', 'Keep the pattern and name; replace both price and Buy with Owned. Exclude this style from future shop selections.', 'Owned crossfades in over 160 ms; card neither disappears nor collapses.'),
      element('Owned status', 'Noninteractive. Apply the style later in the restaurant Floor layer; buying it did not move the player there.', 'No press animation or repeated unlock toast.'),
      returnDoor(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'shop-unaffordable', group: 'shop', title: 'Shop · insufficient coins', scene: 'shop', variant: 'unaffordable',
    description: 'Unaffordable offers retain their preview and price so the player can plan purchases.',
    elements: [
      element('Disabled Buy', 'Cannot purchase; no shortage dialog appears on tap. Other affordable offers may remain active.', 'Muted target has no press bounce. Enable in place over 140 ms when affordability changes in the intended game.'),
      element('Offer details', 'Pattern, quantity and price remain legible even when unavailable.', 'Static presentation; no flashing warning.'),
      returnDoor(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'workshop', group: 'workshop', title: 'Workshop · three upgrade tracks', scene: 'workshop', variant: 'normal',
    description: 'Hull, Harpoon and Collector cards appear together, with current level, next benefit and salvage cost.',
    elements: [
      element('Upgrade cards', 'Compare maximum hull, reeling strength and pickup reach. Upgrade buys one level immediately with salvage; no confirmation.', 'Press 70 ms; level/stat/next cost crossfade for 140 ms while card positions remain stable.'),
      element('Salvage balance', 'Shows banked upgrade currency, separate from restaurant coins and expedition result totals.', 'Update directly; optional 180 ms numeral emphasis without counting through intermediate values.'),
      element('Submarine preview', 'Selected equipment milestones may change hull panels/harpoon/collector art while retaining silhouette and footprint.', 'New part crossfades over 220 ms; avoid changing scale or implying a bigger hitbox.'),
      returnDoor(),
    ],
    notes: ['Live service and passive charging continue in intended gameplay; entering from Edit preserves paused restaurant state.', motionNote, mockNote],
  },
  {
    id: 'workshop-max', group: 'workshop', title: 'Workshop · completed track', scene: 'workshop', variant: 'max',
    description: 'A maximum upgrade track retains its full card, final level and final stat.',
    elements: [
      element('MAX card', 'Replace Upgrade and salvage cost with noninteractive MAX; remove the next-stat arrow. Other tracks remain independent.', 'Crossfade purchase area to MAX over 160 ms; keep full-card geometry.'),
      element('Submarine preview', 'Retain any visible purchased equipment changes across restaurant dock, Workshop and expedition.', 'No repeated unlock celebration on scene entry.'),
      returnDoor(),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'workshop-unaffordable', group: 'workshop', title: 'Workshop · insufficient salvage', scene: 'workshop', variant: 'unaffordable',
    description: 'The next level remains inspectable with its stat preview and cost, while Upgrade is disabled.',
    elements: [
      element('Disabled Upgrade', 'No purchase and no shortage popup on tap. Keep cost legible.', 'No press animation; availability can crossfade over 140 ms when banked salvage changes.'),
      element('Current → next stat', 'Retain comparison for planning; the disabled state does not hide the upgrade benefit.', 'Static values and arrow; no tempting pulse on a disabled control.'),
      returnDoor(),
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
    description: 'A centered card overlays the frozen saved expedition, with Resume and a separate Return early action.',
    elements: [
      element('Paused card', 'Outside taps leave the card open and world frozen. Reopening an unfinished expedition restores this same card.', popupEntrance),
      element('Resume', 'Close the card and start a visible countdown; do not resume immediately or consume the menu tap as steering.', 'Card fades out for 160 ms; countdown appears in place with an opacity transition.'),
      element('Return early', 'Open confirmation explaining retained salvage and missing completion bonus; include unfinished-catch consequence during pursuit.', 'Confirmation content replaces the card with a 180 ms crossfade.'),
    ],
    notes: ['In intended gameplay, restaurant service proceeds independently while expedition is paused. The prototype holds a static visual fixture.', motionNote],
  },
  {
    id: 'expedition-return', group: 'expedition', title: 'Return early confirmation', scene: 'expedition', variant: 'return', overlay: 'early-return',
    description: 'Confirmation keeps already earned rewards while explaining that completion bonus and an unfinished recipe catch are not earned.',
    elements: [
      element('Cancel', 'Return to Paused without resuming the world.', 'Confirmation exits and pause card returns over 160 ms; restore focus to Return early.'),
      element('Return early', 'End the mock journey and open Returned early results. Intended gameplay retains earned salvage and begins recharge.', 'Scene transitions over 220 ms; no reward subtraction or lost-cargo animation.'),
      element('Retained-reward explanation', 'Name the consequences before the second Return early action. Outside taps keep confirmation open.', 'Static readable text; no timed dismissal.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'expedition-resume', group: 'expedition', title: 'Resume countdown', scene: 'expedition', variant: 'resume',
    description: 'A short visible countdown holds the whole expedition frozen before continuing. This review state can be advanced explicitly.',
    elements: [
      element('Countdown', 'Intended automatic completion restarts saved timers and play without extra protection or capture progress.', 'Each numeral changes via a 100 ms crossfade with no zoom. Exact countdown duration remains open.'),
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
      element('Recipe artwork and name', 'Show the earned recipe; it remains retained if the presentation is interrupted.', 'Card rises 12 px over 220 ms, artwork reveals with a 180 ms fade. Reduced motion removes travel.'),
      element('Recipe facts', 'Show fixed dish price, base preparation time and required chef quality. Base time here is distinct from the chef-adjusted picker time.', 'Facts appear together after a short 120 ms fade, without a staggered mandatory wait.'),
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
    description: 'A highlighted garbage footprint opens a bottom-half price card. Purchases are permanent and available from live or edit mode.',
    elements: [
      element('Patch footprint', 'Center the selected patch. Unselected patches have no prices; outside taps leave the card open.', 'Camera glide 300 ms; footprint outline 160 ms. No extra full-screen zoom.'),
      element('Clear', 'Mock a permanent clear and reveal usable floor. Intended game spends the shown cost immediately, with no refund.', 'Garbage fades locally over 350 ms; card leaves over 160 ms. Logic does not wait for the debris animation.'),
      element('Cancel', 'Close the card without clearing or paying; preserve Live/Edit mode.', 'Card lowers 8 px and fades over 160 ms; remove selected outline over 100 ms.'),
      element('Capacity benefit', 'New cleared floor expands staff capacity and customer arrivals in intended gameplay; exact thresholds remain balance decisions.', 'Changed capacity can emphasize for 180 ms after the clear.'),
    ],
    notes: ['The prototype clearance is a navigation fixture and may reveal the dock for review. It does not implement patch adjacency, currency deduction or progression.', motionNote],
  },
  {
    id: 'expansion-unaffordable', group: 'layout', title: 'Expansion · insufficient coins', scene: 'restaurant', variant: 'expanded', overlay: 'expansion',
    description: 'The selected patch and permanent-clear cost remain visible while Clear is disabled.',
    elements: [
      element('Disabled Clear', 'No purchase and no shortage dialog on tap; retain cost and patch highlight.', 'Muted target has no press animation.'),
      element('Cancel', 'Close the card and preserve the underlying restaurant mode.', 'Card exit 160 ms; footprint outline fades 100 ms.'),
      element('Highlighted garbage', 'Continue to show exactly which footprint the offer concerns.', 'Static highlighted boundary; avoid looping alarm animation.'),
    ],
    notes: [motionNote, mockNote],
  },
  {
    id: 'inventory-empty', group: 'restaurant', title: 'Inventory · no belt tiles', scene: 'restaurant', variant: 'edit', overlay: 'inventory-empty',
    description: 'Path placement remains open at zero belt inventory, with available reuse and latest-tile controls.',
    elements: [
      element('Zero count / blocked extensions', 'Disable extensions into empty cells while keeping existing-neighbor reuse available. Zero does not automatically close path mode.', 'Unavailable neighbor outlines stop blinking; remaining valid reuse targets retain the slow 1.4 s pulse.'),
      element('Rotate / Remove / X', 'Latest-tile actions stay usable. X ends path placement and restores the inventory tray.', 'Rotation 160 ms; removal fade 160 ms; panel content crossfades over 160 ms.'),
      element('Shop link', 'Wireframe shortcut demonstrates where inventory can be replenished, preserving edit mode on return.', '70 ms press, 200 ms scene crossfade.'),
    ],
    notes: ['The accepted game state is an inline path-placement state. The standalone review overlay isolates it for discussion; its final presentation remains open.', motionNote, mockNote],
  },
  {
    id: 'component-restaurant-hud', group: 'components', title: 'Restaurant HUD · floating Shop', scene: 'component', variant: 'restaurant-hud', component: 'restaurant-hud',
    description: 'The shared restaurant HUD follows the reference placement: savings at the upper-left and a floating Shop directly below. It is rendered independently here and in every restaurant state.',
    elements: [
      element('Fixed savings', 'Styled coin count stays in the upper-left as the restaurant pans. Earnings appear beside it without adding a background panel.', 'Amounts update immediately; earned text fades in for 120 ms, holds for about 2.2 s and fades out for 200 ms. Camera movement never moves the HUD.'),
      element('Floating Shop', 'Open Shop from Live or Edit on any panel. Returning restores the same view and camera panel. The button has no doorway or floor footprint.', 'Press feedback: 0.97 scale for 70 ms. Scene crossfade takes 200 ms; no camera movement or constant button bounce.'),
      element('Stock cue', 'A small sparkle belongs to the floating Shop button and clears when Shop opens.', 'Proposed subtle sparkle loop: 1.8 s; on entry fade out for 150 ms. Reduced motion keeps the cue static.'),
    ],
    notes: ['The user chose the reference layout with existing Sushi Loop controls only. Workshop remains a compact physical hut beside the submarine; the reference’s level meter, Settings, Tasks and extra Workshop shortcut are outside this wireframe.', motionNote, mockNote],
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
    description: 'The same character renderer used for restaurant guests, chef roster rows, applications and detail popups is shown here. Shared portrait revisions update each context.',
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
      element('Submarine target', 'Ready tap opens expedition preparation; charging tap keeps the restaurant visible and gives local status. Future-access preview must be labeled as review navigation.', 'Target press 70 ms; ready headlight gently pulses over 1.6 s. Charging has no ready pulse.'),
      element('Local battery', 'Charge is visible at the dock only. Omit a persistent top-HUD battery and separate Ready badge.', 'Intended charge fill is linear; the component fixture remains static until a review state changes.'),
      element('Charging message', 'Show Charging with remaining time near the dock after a tap; do not open an unavailable start screen.', '120 ms entrance fade, about 2.2 s hold and 180 ms exit. Repeated taps replace one cue rather than stacking notices.'),
      element('Workshop hut target', 'Separate target adjacent to the submarine. It opens Workshop and preserves the originating Live/Edit mode.', '70 ms press followed by a 200 ms scene crossfade. Consume the opener touch.'),
    ],
    notes: ['Dock footprint, connected access route and exact middle-panel location remain floor-plan decisions. This component does not clear garbage or run recharge.', motionNote],
  },
  {
    id: 'component-recipe-tile', group: 'components', title: 'Recipe catalog tile', scene: 'component', variant: 'recipe-tile', component: 'recipe-tile',
    description: 'The same recipe-tile renderer used inside every chef recipe picker is shown here with current, inspected, NEW, above-tier and undiscovered treatments. Revisions carry through to all picker stories.',
    elements: [
      element('Tier board and dish', 'Discovered tiles show artwork, name and tier. Undiscovered tiles show unidentified engraved silhouettes. Material color and texture supplement a readable tier label.', 'Artwork may crossfade on discovery over 180 ms; no pulsing mystery teaser.'),
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
