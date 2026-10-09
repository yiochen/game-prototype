# Sushi restaurant and submarine expeditions

The language of the proposed mobile game, combining a conveyor sushi restaurant with submarine expeditions that discover recipes.

## Language

**Cell**:
A square placement space in the restaurant grid. A chef, a customer seat, or a belt tile occupies one cell.
_Avoid_: Slot, plot

**Belt tile**:
A single-cell section of conveyor that carries dishes in a direction.
_Avoid_: Belt segment when referring to one tile

**Belt**:
A connected route of belt tiles along which dishes travel. A belt may be open rather than a complete loop.
_Avoid_: Loop when referring to an open route

**Chef**:
A hired restaurant worker who retains their level and upgrades while unassigned. When assigned, they occupy one cell beside the belt, prepare one assigned recipe, and load its dishes onto their facing tile.
_Avoid_: Loading point when referring to the worker

**Loading point**:
The belt tile where a chef places dishes.
_Avoid_: Kitchen, chef

**Customer seat**:
A single-cell seating position facing one adjacent belt tile, from which a seated customer can take dishes.
_Avoid_: Table when referring to an individual belt-side seat

**Dish**:
A prepared food item carried on a plate and available for a customer to take from the belt.
_Avoid_: Recipe when referring to an individual serving

**Recipe**:
A type of dish that a chef can prepare.
_Avoid_: Plate when referring to a food type

**Recipe tile**:
A recipe-picker entry rendered as a board made from its quality tier's material. An undiscovered dish appears as an engraved silhouette on its tier board.
_Avoid_: Grid cell, generic card

**Prepare**:
The instruction choosing which recipe a selected chef continually makes.
_Avoid_: Assign when naming the recipe-selection action, a one-dish cooking order

**Base preparation time**:
A recipe's preparation duration before a chef's cooking-speed improvements are applied.
_Avoid_: Chef-specific preparation time, earning rate

**Effective preparation time**:
A recipe's preparation duration after the selected chef's current cooking speed is applied, excluding time spent waiting to load the dish onto a blocked belt.
_Avoid_: Base preparation time, belt-loading delay, earning rate

**Backpressure**:
The buildup of uneaten dishes that prevents additional dishes from entering a full belt. Space freed by customers allows production to resume.
_Avoid_: Waste, breakdown

**Dish preference**:
A customer's favored recipe. A preference is not a requirement: the customer can accept other dishes.
_Avoid_: Required order, dietary restriction

**Fullness**:
A customer's internal meal-completion state. The appetite needed to finish a meal varies by customer and is not displayed to the player.
_Avoid_: Satisfaction, visible plate target

**Facing direction**:
The direction connecting a chef or customer seat to its one adjacent belt tile. Rotating the chef or seat changes which tile it faces.
_Avoid_: Belt direction when referring to a chef or seat

**Edit mode**:
The restaurant arrangement mode in which NPCs and belt movement are paused. Selecting an object exposes local controls and enables dragging that object to move it.
_Avoid_: Preview mode when referring to paused arrangement

**Preview mode**:
The live restaurant view in which customers, chefs, and dishes operate and normal gameplay progresses.
_Avoid_: Test simulation, sandbox preview

**Chef speed**:
A chef's rate of dish production.
_Avoid_: Belt speed

**Aisle**:
A connected route of empty floor cells through which customers can walk to reach seating.
_Avoid_: Decorative walkway

**Workable area**:
The restaurant floor available for building and customer movement. It begins as a small rectangle and expands as garbage is cleared.
_Avoid_: Entire restaurant footprint

**Garbage**:
An obstacle occupying floor space outside the initial workable area. Removing it costs cash and makes its floor space available.
_Avoid_: Uneaten dish, recurring restaurant waste

**Expansion patch**:
A predefined group of garbage-covered floor cells cleared together in one purchase.
_Avoid_: Individual clearance cell

**Chef blackboard**:
A small board integrated into a chef's one-cell footprint, identifying the dish that chef is currently making. It informs both the player and customers considering where to sit.
_Avoid_: General menu board

**Displacement**:
The movement of a customer into empty space when a newly placed object occupies their position. It is shown with a pushed animation.
_Avoid_: Return to entrance

**Trapped customer**:
A customer with no walking route to an exit or usable seat. Their panic and slow wandering convey the access problem.
_Avoid_: Belt congestion

**Edit layer**:
A category of restaurant content selectable in edit mode: People, Layout, or Floor. Layer controls are shown as icons without visible text labels.
_Avoid_: Separate gameplay mode

**People layer**:
The edit layer containing customers and chefs.
_Avoid_: Player layer

**Layout layer**:
The edit layer containing seats, belt tiles, and applicable placed furniture.
_Avoid_: Floor layer

**Floor layer**:
The edit layer containing floor tiles and their appearance.
_Avoid_: Layout layer

**Chef level**:
A chef's development rank advanced through upgrade investment. Reaching designated levels unlocks a whole recipe quality tier for that chef.
_Avoid_: Chef speed, dish quality

**Quality tier**:
A named recipe-quality band in the order Wood, Steel, Copper, Silver, Gold. Each tier has a distinct board material color and texture; shared starting unlock thresholds are Wood 1, Steel 3, Copper 5, Silver 8, and Gold 12.
_Avoid_: Fine-grained grade number

**Recipe tier**:
The minimum chef quality tier required to prepare a discovered recipe. A chef can prepare recipes at or below the highest tier they have unlocked.
_Avoid_: Individual recipe level, dish quality number

**Chef assignment**:
The placement of a hired chef in one ordinary restaurant floor cell. No separately built chef station is required.
_Avoid_: Hiring

**Unassignment**:
Removing a chef from their working spot while retaining them as hired staff for reassignment.
_Avoid_: Firing, selling

**Firing**:
Permanent dismissal of a hired chef, who disappears from the restaurant's staff without a cash refund.
_Avoid_: Unassignment, object removal

**Job application**:
A prospective chef's profile, exposing their predefined strengths, growth speed, capability ceiling, highest reachable recipe tier, and hiring cost before recruitment.
_Avoid_: Hired staff profile

**Capability ceiling**:
The maximum chef level established by a chef's predefined attributes. A chef cannot unlock a quality tier whose shared level threshold is above this ceiling.
_Avoid_: Current chef level

**Staff capacity**:
The maximum number of hired chefs, assigned or unassigned, that the restaurant can retain. Capacity grows with cleared workable floor space.
_Avoid_: Number of chef spots, currently empty floor cells

**Preference timer**:
A customer's willingness to wait for their preferred dish, shown as a circular countdown around its thought bubble. After expiry, the customer accepts the next available dish.
_Avoid_: Fullness meter, departure timer

**Satisfaction cue**:
The positive visual reaction replacing a preference bubble when the customer receives their preferred dish.
_Avoid_: Fullness progress bar

**Chef quality tier**:
A chef's highest cooking-capability tier, unlocked when they reach its designated level threshold.
_Avoid_: Fine-grained quality grade

**Growth**:
The cooking-speed improvement a chef gains per level-up, as determined by predefined attributes; designated chef levels unlock higher recipe quality tiers.
_Avoid_: Cooking experience rate, training duration, upgrade discount

**Expedition**:
A submarine journey along the ocean bed to gather salvage and catch creatures that unlock recipes.
_Avoid_: Restaurant service session

**Expedition entrance**:
The restaurant-scene destination through which the player accesses submarine departures.
_Avoid_: Underwater portal, restaurant customer entrance

**Dock**:
The restaurant-side mooring where the visible submarine serves as the expedition entrance.
_Avoid_: Workshop, underwater portal

**Departure**:
The beginning of active expedition travel, when readiness is consumed. Opening the expedition start screen is preparation rather than departure.
_Avoid_: Dock tap, resuming a paused expedition

**Sushi-bar entrance**:
The warm airlock doorway on the expedition preparation screen through which the player returns to the restaurant before departure.
_Avoid_: Back-arrow button, travel portal, restaurant customer entrance, early return

**Coins**:
The restaurant's currency, earned from dish sales and spent on restaurant development.
_Avoid_: Salvage, shared cash

**Salvage**:
The expedition's currency, recovered underwater and spent on submarine improvements.
_Avoid_: Restaurant coins, shared cash

**Workshop**:
The submarine improvement area, where salvage funds permanent equipment upgrades.
_Avoid_: Ship upgrades as the area's player-facing name, restaurant construction menu

**Equipment level**:
A submarine component's development rank, increased through salvage purchases up to its upgrade cap. Hull, Harpoon, and Collector advance independently.
_Avoid_: Chef level, overall ship level, capture milestone

**Extraction point**:
The successful finish of an expedition route, where its completion bonus is earned.
_Avoid_: Endless-run milestone

**Hull durability**:
The submarine's remaining capacity to withstand damaging collisions during an expedition.
_Avoid_: Shield when referring to the submarine's base durability

**Hit protection**:
The brief protection following a damaging collision that prevents repeated damage from the same hit.
_Avoid_: Hull upgrade, collectible shield

**Creature species**:
A distinct kind of catchable underwater creature associated with a distinct restaurant recipe.
_Avoid_: Recipe when referring to the animal itself, individual creature encounter

**Catch**:
The completed capture of a creature after harpooning and following it. The first catch of a species earns its associated recipe.
_Avoid_: Harpoon hit, incomplete pursuit

**Pursuit**:
The period of following a harpooned creature before completing its catch.
_Avoid_: Completed catch, ordinary forward travel

**Following range**:
The vertical strip aligned with a harpooned creature in which the submarine can advance its catch. Only lateral alignment matters; it has no forward or backward limit.
_Avoid_: Harpoon firing range, attack strip, forward-distance requirement

**Pursuit grace period**:
The brief opportunity to return to following range before a harpooned creature escapes.
_Avoid_: Hit protection, harpoon cooldown

**Harpoon cable**:
The tether connecting the submarine to a harpooned creature during pursuit. A broken cable ends that capture attempt without earning its recipe.
_Avoid_: Hull durability, completed catch

**Capture progress**:
The accumulated advancement toward catching a harpooned creature during pursuit.
_Avoid_: Hull durability, recipe-item collection progress

**Shooting window**:
The limited opportunity to harpoon an encountered creature before it swims away.
_Avoid_: Pursuit grace period, harpoon cooldown

**Creature resistance**:
The remaining effort needed to complete a catch, represented by the creature's top-screen bar. Resistance decreases as capture progress increases.
_Avoid_: Hull durability, damage to the creature

**Creature catalog**:
The finite collection of catchable species and their associated restaurant recipes.
_Avoid_: Job application pool, expedition route

**Capture milestone**:
A collection achievement that opens additional creature species for future expeditions.
_Avoid_: Purchased submarine upgrade, extraction bonus

**Ship charge**:
The submarine's readiness resource for one expedition, replenished at a fixed rate during night service independently of restaurant sales.
_Avoid_: Restaurant coins, salvage upgrade currency

**Reeling strength**:
The submarine's ability to reduce a harpooned creature's resistance while pursuing within following range.
_Avoid_: Harpoon aiming accuracy, damage to obstacles

**Salvage attraction range**:
The distance from which collection equipment draws nearby salvage pickups toward the submarine.
_Avoid_: Pickup value multiplier, following range

**Boost**:
A temporary increase in expedition forward speed that protects the submarine from collision damage.
_Avoid_: Permanent ship level, lateral steering acceleration

**Bonus passage**:
A safe separate route entered through a portal, where a strong current carries the submarine while it collects salvage without requiring maneuvering.
_Avoid_: Creature pursuit, ordinary lateral current

**Lateral current**:
A visible water flow on the main expedition route that pushes the submarine sideways while the player retains steering control.
_Avoid_: Boost, automatic bonus-passage current

**Creature attack**:
A species-specific action that directly threatens the submarine or creates encounter hazards, such as scattered reef fragments, swirls, currents, or electrical discharges.
_Avoid_: Ordinary creature movement, harpoon shot

**Attack strip**:
A vertical band selected and warned by a creature before its discharge threatens that area.
_Avoid_: Movement lane, submarine-tracking aim

**Night service**:
The persistent restaurant phase during which the submarine recharges for its next expedition.
_Avoid_: Restaurant reset, real-world nighttime restriction

**Early return**:
A deliberate end to an unfinished expedition that retains earned rewards without awarding the completion bonus.
_Avoid_: Paused expedition, successful journey finish

**Paused expedition**:
An unfinished submarine journey whose progress is stopped and state retained for later resumption. It does not begin night recharge.
_Avoid_: Early return, new departure
