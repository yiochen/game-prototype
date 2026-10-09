# Sushi Loop: gameplay and controls

Checkpoint: the user accepted this core restaurant gameplay and control model. The later expedition interview defines recipe acquisition and the day/night recharge loop; its [consolidated checkpoint](./expedition-gameplay-and-controls.md) is being reviewed. This is a design document, not an implemented game. Exact balance values and unresolved interactions are listed at the end. Vocabulary lives in [CONTEXT.md](../CONTEXT.md); the restaurant decision record is [design-interview.md](./design-interview.md).

The UI interview subsequently accepted locked portrait orientation throughout the game, including the sushi bar, expedition, Workshop, and related screens. Rotating the device does not switch to a landscape layout. Exact device insets and sizes remain open; see [Question 31 in the UI interview](./ui-design-interview.md#question-31-game-screen-orientation).

## Player activity

Watch an automatic sushi restaurant, identify a problem, change the layout or chef assignments, and observe the result. Repeated manual cooking, serving, or clearing is not the main activity. Customers, plates, and chef animations provide feedback. Show the cash balance, but no earning-rate metric. Restaurant coins earned during an expedition stay pending and are credited when the player returns. After any outcome with earnings, briefly show the credited total beside the updated cash balance; suppress the notice when the total is zero. The text fades out automatically and requires no dismissal.

When the player enters another scene through an in-world entrance, the current simulation keeps running. Non-full-screen popups also leave the current simulation running. If the player enters a scene from edit mode, the restaurant stays paused and resumes from the same edit state on return. Explicit Pause stops the expedition itself; restaurant simulation continues independently in the background during an expedition. Edit mode pauses restaurant NPCs and belts, including when visiting another scene from edit mode.

## Restaurant and growth

- Start with a small rectangular workable area and an operating starter bar: a short open belt, one chef, and a few seats.
- Surrounding garbage blocks expansion. Cash clears predefined patches, with a choice among neighboring patches.
- Cleared space permanently expands the workable area. It is not refundable.
- Cleared area increases customer arrivals and staff capacity. Capacity uses total cleared area, not remaining empty cells.
- The restaurant persists and grows; the core progression does not reset across separate locations.
- The camera stays at a fixed scale. Swipe to pan; no pinch zoom.
- Returning from the Workshop, expedition preparation, or expedition results recenters the view on the cleared restaurant floor at the fixed camera scale. Normal swipe panning remains available afterward.

## Grid and belt

- A belt tile, seat, or assigned chef occupies one cell. Objects occupy distinct cells.
- Each seat and chef faces one adjacent belt tile. Rotation changes that connection.
- Belt tiles connect through center points, and the connected line determines belt direction. Paths can turn by changing the connection line through a tile.
- During path placement, tapping an existing neighboring belt can take that segment into the new path and reorient it, potentially breaking the previous path. Repeated tapping can replace its route, such as changing a left-to-down turn into left-to-right only.
- Belts support open paths and closed loops. Separate belts can coexist. Each tile has at most one incoming and one outgoing belt connection; no splits or merges.
- Each tile holds one dish, including the endpoint of an open path. No collection tray, endpoint stack, or manual Clear tray action.
- An open endpoint retains its uneaten dish. Plates queue behind it; blockage remains local.
- Customers can take dishes from stopped tiles. Removing a dish allows upstream motion.
- Full loops circulate all plates together. A tile may advance into an occupied tile when its plate advances simultaneously.
- Disconnected chefs and seats are allowed. Their inactivity is conveyed through animation, without error badges or inactive labels.

## Customers

- Customers walk through empty floor cells to reachable seats. They consider nearby dishes and chef blackboards when choosing among free seats.
- Customers pass or yield automatically; pedestrian collisions do not create permanent blockages.
- A customer's first-dish preference appears in a thought bubble with a circular countdown. Receiving that dish briefly transforms the bubble into a happy face and triggers a short happy customer animation, then the bubble fades away.
- When the countdown expires, the customer accepts the next available dish at their facing tile.
- This preference cycle runs once per visit. After the first plate, customers accept whatever arrives.
- Appetite and meal completion vary internally by customer. No fullness bar, remaining-plate counter, or default three-dish meal.
- Eating duration is broadly similar across recipes. Recipes differ principally in preparation time, fixed price, quality tier, and preferences.
- Customers who receive no food for too long become restless and leave. No fine or lasting reputation penalty.
- Income comes from dishes sold. Each consumed dish triggers a small coin-icon pop near the customer or dish and updates the cash balance; the pop has no amount label. Splitting the same sales across more customers does not create an extra turnover reward.

## Chefs and recipes

- Chefs are hired people, not refundable construction objects. Their assigned working position is an ordinary floor cell, not a separately built station.
- Each chef's one-cell footprint includes their blackboard, showing the current recipe. It moves and rotates with the chef.
- Each chef makes one assigned recipe at a time. Manage recipes and upgrades in live preview while service continues.
- A chef may prepare and hold one dish while waiting for loading space. After placing it, they begin the next dish. No hidden stockpile.
- Changing recipe immediately resets unfinished preparation and replaces any held dish. The blackboard updates immediately and briefly shakes when the recipe picker closes back to the restaurant. Plates already on the belt remain unchanged.
- Unlock recipes once for the restaurant. Recipes use named quality tiers in this order: Wood, Steel, Copper, Silver, Gold. Each recipe tile is a board made from its tier's material, with distinct color and texture so the tier reads without relying on a text label. All chefs share these starting unlock thresholds: Wood at Level 1, Steel at Level 3, Copper at Level 5, Silver at Level 8, and Gold at Level 12. A chef can make any unlocked recipe at or below their highest unlocked tier; a capability ceiling below a threshold prevents reaching that tier. These thresholds remain open to balance tuning, as does the exact material treatment.
- Newly unlocked recipes have a small NEW badge in the chef's recipe picker until inspected in the restaurant. Inspection clears the marker without requiring assignment or cooking; the expedition award dialog does not clear it. Returning with a discovery leaves existing chef recipes intact.
- The chef's recipe picker is a large portrait dialog over the restaurant, with a light scrim that dims but keeps the live scene visible. It contains a scrolling two-column catalog of recipe tiles above a fixed lower recipe details panel containing artwork, facts, and the Prepare area. For an existing chef, the panel initially shows that chef's current recipe when the picker opens. A newly placed chef's picker opens with no recipe selected; Prepare remains unavailable until the player chooses a cookable recipe. Group the catalog in this order: recipes the chef can cook, sorted from highest to lowest tier; discovered recipes above the chef's tier, sorted from highest to lowest and shown in muted color; then undiscovered recipes shown as silhouettes engraved on their tier-material boards. Each tile is a board made from its tier's material and shows the discovered dish's artwork, name, tier, and a NEW marker where applicable. Outline the current recipe tile; give the tile selected for inspection a different outline. When both states apply to one tile, keep both outlines distinguishable. Tapping a discovered recipe updates the panel; scrolling leaves it in place. An icon-only header control and the phone's system back gesture both close the picker without changing the chef's current recipe or cooking state. Taps outside the dialog do not dismiss it or trigger underlying restaurant actions. Opening the picker leaves the chef's recipe intact, and restaurant service continues while browsing. Exact material treatment, card/panel dimensions, and insets remain under review.
- Tapping a discovered recipe tile updates the fixed lower details panel with its full-color dish illustration, fixed price, preparation time, and required chef quality tier. For recipes the selected chef can cook, show only effective preparation time adjusted for that chef's current speed, omitting base time. This duration excludes waiting to load onto a blocked belt. For recipes above the chef's tier, show a dash (—) for preparation time while retaining price and required tier, and disable Prepare. When the selected recipe is already the chef's current recipe, show a noninteractive Preparing status in place of Prepare. Selecting a different eligible recipe restores Prepare. Choosing a different recipe closes the picker and returns to live service with the updated blackboard briefly shaking. Prepare chooses the chef's ongoing recipe rather than requiring a tap for each dish. Inspection leaves their current preparation and held dish intact; an actual recipe change has the accepted reset/replacement effects. Restaurant service continues throughout.
- Discovered recipes above the selected chef's tier remain visible with their tier requirement and can still be inspected. Prepare is disabled while the chef is ineligible. Inspection still clears their NEW marker; seeing a recipe does not grant permission to cook it. Undiscovered recipes remain unidentified silhouettes until caught.
- Each recipe has a fixed selling price; chef quality tier does not multiply it. Every higher recipe tier has a higher fixed-price band than every lower tier. Preparation time varies independently of tier and price, so higher-tier recipes can be quick, lower-tier recipes can be slow, and long preparation does not guarantee a higher price within one tier.
- The chef detail popup shows the current-to-next cooking-speed change and notes any recipe-tier unlock. Tapping an affordable Level Up action immediately pays the visible cost and improves cooking speed according to predefined growth attributes. When coins are insufficient, keep the next-level preview and cost visible and disable Level Up. Quality capability advances when a chef reaches a designated level threshold, unlocking a whole recipe tier. At their capability ceiling, retain final level and stats and replace Level Up and its cost with a noninteractive MAX status. No separate speed/quality purchase tracks or cooking-experience system.
- Applications expose strengths, growth per level, maximum chef level, highest recipe tier reachable at that level, and hiring cost. The maximum level limits further development.
- Recruit from a changing set of three chef applications. Offers remain until manually refreshed. Refresh is free; its cooldown runs in real time while the app is closed.
- Assigned and unassigned chefs both count toward staff capacity. Unassigning frees the floor cell and preserves the chef's progress. Firing permanently removes the chef without refund.

## Editing and controls

Preview is the actual live restaurant, not a sandbox simulation. Entering edit mode pauses NPCs and belt movement.

Use three icon-only edit layers, without visible text labels:

| Layer in the model | Selectable content |
| --- | --- |
| People | Customers and placed chefs; unassigned chef portraits appear in the layer tray for placement |
| Layout | Seats, belts, and applicable placed objects |
| Floor | Floor tiles and their appearance |

- Tap an existing object to select it and reveal local rotation controls. After selection, drag it to move; it remains selected after release so the player can rotate or move it again. A swipe starting outside the selected object clears selection and pans in that same gesture.
- Without an object selected, dragging pans rather than moving an object.
- Place an unassigned chef by dragging their portrait from the People layer onto an empty floor cell next to a belt. This works in live or edit mode. Placement immediately opens that chef's dish picker; closing it leaves the chef idle.
- A shop entrance is part of the restaurant scene and can be entered in live or edit mode. The shop scene shows a restaurant doorway for returning. Returning from the shop preserves the current restaurant and edit state. The shop offers stable essentials such as belt tiles and normal chairs, plus changing random goods such as fancier chairs and other objects. Stable essentials remain available in unlimited quantities between expeditions; rotating goods refresh after each expedition and have displayed limited quantities that decrement on purchase. Most furniture is appearance-only, while a smaller subset has functional benefits. Furniture benefits do not change customer patience or preferences; the exact effects remain future design work. Unaffordable items remain visible with their prices, but their purchase controls are disabled. Purchased goods go into the player's inventory.
- In edit mode, the paginated bottom inventory panel lets the player drag an item into the scene. Starting a belt path places one inventory tile; its four surrounding cells then light and blink slowly. Each newly placed tile consumes one belt tile from inventory, with the remaining count shown. Tapping a neighboring cell places or connects the next tile and continues the path. Tapping an existing neighboring belt reuses and reorients that segment rather than placing a new tile. If the tapped belt is the starting tile of the active path, it closes the loop and ends path placement, returning the bottom panel to inventory. Releasing a dragged inventory item in an invalid location returns it to its original position and briefly indicates why placement was rejected.
- During belt path placement, the bottom panel shows rotate and delete controls for the latest tile, plus an X to return to inventory and end path placement. If belt inventory reaches zero, keep path mode open, show zero, and disable extensions into empty cells; the player can still reuse an existing neighboring belt or use the latest tile controls. Tapping outside the highlighted neighbor cells ends the current path and returns the bottom panel to inventory.
- Edit-mode changes take effect and persist immediately; there is no Save, Done, or Cancel step. NPCs and the belt stay paused until the player taps the explicit Live control in the edit toolbar to return to live view. Removing a purchased object returns it to inventory without refunding coins.
- Floor appearance is cosmetic: alternate styles are premium collectibles that cost restaurant coins and appear as rotating shop goods, at most one per rotation and with none guaranteed, with a large multi-cell pattern preview, pattern name, and price; owned styles are excluded from later selections. Any unowned style is eligible from the beginning. Unpurchased styles may return on the next rotation, with no recent-offer protection. Prices use three levels—low, middle, and high—and higher-priced styles appear less often; exact values and appearance odds remain balance work. They do not change earnings, patience, preferences, or walking access. Tapping Buy immediately spends the shown price and unlocks a style for unlimited floor tiles; applying it consumes no tile items. A brief text-only toast beside the coin balance names the unlocked style and confirms it was added to the Floor palette. The player remains in the shop after purchase and can apply the style later from the Floor layer. The Floor layer opens with no style selected. In the visible, paginated bottom swatch grid, tap an owned style to activate it, then tap a cell to paint one tile or drag across floor cells to paint multiple tiles, including cells beneath placed objects. Matching painted tiles may use subtle visual variants and share shader effects spanning across cells, such as a slow ambient flare over multiple tiles of the same type. Purchased styles are ordered newest first; the original floor style appears last. The selected brush stays active after each stroke. Directional carets at the screen edges pan the scene while preserving the selected style; a tap smoothly moves four grid tiles, holding continues panning, and releasing resumes painting. Hide carets for directions where the scene cannot move farther. Exact motion duration remains tuning work. A top X clears the brush and keeps the player in the Floor layer with the palette open. The original floor appearance is a free palette option.
- Purchase expansion patches in either mode. Tapping a garbage patch pans the scene to center its highlighted footprint and opens a price card in the bottom half of the screen with Clear and Cancel actions; unselected patches show no prices, and outside taps leave the card open. Confirming spends the visible cost and permanently clears the patch, including during edit mode. Cleared floor cannot be refunded. If the player cannot afford it, the cost remains visible and Clear is disabled.

## People affected by edits

- Moving an occupied seat carries its customer. Moving an occupied belt tile carries its plate.
- Removing a seat leaves its customer at the former seat position with their meal progress intact. They look puzzled, search for another reachable seat, and move after finding one.
- Removing a belt tile removes its plate without earning money.
- If a new seat or similar sit-on object occupies a standing customer's cell, seat them on it immediately. Otherwise, push them to the nearest valid empty cell with a pushed animation. If no empty cell is available, block placement so the object cannot overlap the customer.
- A customer with no route to an exit or a seat panics and wanders slowly. Such layouts are allowed; the customer remains in this behavior until the player edits the layout or drags them to safety.
- Customers can be selected and dragged directly in the People layer during editing, including to rescue them from enclosed spaces; dragging preserves their visit, preference, and eating progress. They can be dropped onto any empty floor cell or free seat, including cells they could not reach by walking; dropping them on a free seat resumes their visit there.
- Customer reactions occur when live play resumes; edit mode remains paused.

## Economy and idle progress

- No wages, ingredient charges, or recurring operating costs.
- Restaurant coins fund construction, hiring, level-ups, cosmetic purchases where applicable, and permanent expansion. Recipes are unlocked by expedition catches rather than purchased with coins; expedition salvage funds submarine upgrades.
- Congestion and failed service reduce potential income without draining savings.
- Offline income reflects the committed restaurant's layout and service performance, rather than a generic allowance based only on upgrades.
- Offline income accumulates for the entire absence, without a time cap or required collection visits.

## Open details for the next design pass

These are unresolved, not extra rules inferred from mockups:

- Balance tables: prices, preparation times, chef profiles, growth, maximum levels, upgrade costs, appetite variation, eating intervals, preference and departure timers, arrivals, patch geometry, and staff-capacity thresholds.
- Recipe acquisition and the day/night loop are defined in [expedition gameplay and controls](./expedition-gameplay-and-controls.md): night service recharges one expedition, while catching new species unlocks recipes. Recharge time is independent of sales; coins and salvage have separate spending purposes.
- Exact thought-bubble cue animation and coin-pop timing/design.
- Detailed chef applicant, hiring, assignment, and firing screen flows.
- Exact odds between tier-roll misses, the tier-unlock notice content, exact material treatment, card/details-panel dimensions and artwork/device insets, disabled-action styling, and blackboard-shake timing/amplitude; see the active interview. Exact effective-time calculation and values remain balance work.
- Application refresh cooldown duration and whether the disabled Refresh button shows a countdown (deferred UI choice; see Question 206 in [ui-design-interview.md](./ui-design-interview.md)).
- Exact functional furniture effects, connecting to existing belts in complex overlaps, and closing a loop against existing tiles.
- Treatment of a customer dragged directly off an occupied seat.
- When the shop's new-goods badge clears.
- Exact balance values for offline throughput and customer preference demand.

The principal balance risk is a dominant high-priced recipe once chefs become fast enough. Test recipe preparation curves, fixed prices, capability ceilings, demand, and layout throughput together.
