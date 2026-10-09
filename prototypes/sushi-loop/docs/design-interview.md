# Gameplay and control interview

This is a design discussion, not an implemented or registered game. Sushi Loop is a working name from the mockups.

## Checkpoint status

The user wrapped the grilling session after accepting the restaurant, expedition, and UI direction documented in [gameplay-and-controls.md](./gameplay-and-controls.md), [expedition-gameplay-and-controls.md](./expedition-gameplay-and-controls.md), and [ui-design-interview.md](./ui-design-interview.md). This is a design checkpoint, not an implementation-complete claim. One UI choice was deferred: whether the applicant Refresh button displays its remaining cooldown. Prior freeform recipe-acquisition ideas are superseded by the accepted creature-catching expedition that unlocks one new recipe per expedition.

## Established direction

- Mobile idle and incremental restaurant management with meaningful upgrade choices.
- Customers visibly react to the player's layout and food choices.
- A clear square grid contains belt tiles, customer seats, and chefs.
- A chef occupies one cell beside the belt and acts as an upgradeable worker.
- The initial business can operate with a short open belt; a complete loop is not required to start.
- A polished 2D game presentation with characters suitable for animation.

## Remaining design and balance work

- Numeric balance: recipe prices and preparation times, chef attributes and costs, cooldown duration, customer timing and seat-choice weights, expansion prices, staff-capacity thresholds, and offline-throughput values.
- Detailed content and presentation: recipe and creature catalogs, furniture effects, precise layout dimensions, animation timings, and device-specific insets.
- Prototype-level questions listed in the open-details sections of [gameplay-and-controls.md](./gameplay-and-controls.md) and [expedition-gameplay-and-controls.md](./expedition-gameplay-and-controls.md).

## Confirmed decisions

### Primary activity: diagnose and improve

The player primarily watches an automatic restaurant, identifies problems, and adjusts chefs, recipes, seating, or belt layout. Keeping service moving through repeated manual actions is not the core activity. Optional interventions remain undecided.

### Open belt endpoints: backpressure

Uneaten dishes accumulate at the end of an open belt rather than falling off or being discarded. A full belt stops the chef from placing additional dishes; production resumes automatically when customers create space. The player chose this to avoid harmful consequences while idle. Reduced potential earnings from congestion remain distinct from losing money or food. Offline simulation remains undecided; tile capacity and operating costs are resolved below.

### Customer food choices: flexible preferences

Customers prefer some recipes but eventually accept other dishes. Preferences do not permanently prevent consumption of available food. The purpose is to preserve menu strategy while letting an unpopular dish backlog clear without manual intervention. A circular preference countdown controls fallback acceptance, as resolved below. Any reward beyond the visual satisfaction cue remains undecided.

### Customer departure: hidden, individual fullness

Customers finish their visit based on fullness, not a satisfaction target. Their appetites vary internally; there is no default three-plate meal. Do not show a fullness progress bar, remaining plate count, or other appetite meter. Players manage the restaurant rather than counting individual meals.

Revenue is tied to dishes sold. For the same dishes, one customer eating three earns the same as three customers eating one each; customer turnover does not grant an additional reward by itself. Exact prices and any preference-related rewards remain undecided and must respect this principle.

### Chef production: one assigned recipe

Each chef produces one assigned recipe at a time. The player can change that assignment; chefs do not use recipe mixes or percentage allocations. The assignment control and the treatment of already prepared dishes during reassignment remain undecided.

### Congestion recovery: customers consume from stopped tiles

Customers can take acceptable dishes from the belt tile beside their seat whether the dish is moving or stopped. Removing a dish creates space that lets upstream dishes advance. Backpressure is local: a tile advances when the next tile has room or its occupant advances at the same time; a full endpoint does not globally stop every tile. Chefs can resume loading when their loading tile clears. Full-loop motion is resolved below.

### Spatial interaction: one facing tile

Each chef and customer seat faces exactly one adjacent belt tile. A chef loads onto that tile; a seated customer takes dishes from that tile. Objects do not interact with every adjacent belt tile, including at corners. Rotation changes the facing direction.

### Editing controls: pause, select, then manipulate

Entering edit mode pauses all NPCs and the belt. Tapping an existing object selects it and reveals local rotation controls; after selection, the player can drag it to move it. Without a selected object, dragging pans the view. Chef manipulation, deselection, and placement are defined in later accepted controls. The user’s word “table” is treated as the customer-seat object.

### Preview means the live view

Preview mode is the actual live restaurant view: NPCs and dishes move and normal gameplay progresses. It is not a hypothetical test simulation. The two modes are live preview and paused editing; do not add a separate sandbox preview or simulated economy.

### Simulation timing: running by default across scenes and popups

When a player enters another scene through an in-world entrance, the current simulation keeps running. Non-full-screen popups also leave it running. Explicit Pause freezes the expedition itself, while restaurant simulation continues independently in the background during the expedition. Edit mode freezes restaurant NPCs and belts; entering the Shop from edit mode preserves that paused state.

### Immediate edits: changes persist as they are made

Every edit-mode change takes effect and persists immediately. There is no Save, Done, or Cancel step and no rollback to the layout from before editing. NPCs and the belt remain paused while the player rearranges the restaurant; an explicit Live control in the edit toolbar exits edit mode and resumes service with the current layout. Purchases and inventory changes also apply immediately. There is no Undo control; players correct mistakes with another edit or by returning removed goods from inventory.

### Moving occupied objects: preserve their contents

Occupied seats and belt tiles can be moved during edit mode. A seated customer follows their seat, and a plate follows its belt tile. Both remain paused during rearrangement and resume when the player exits edit mode. Editing does not require objects to empty first. Removal and reactions to unreachable routes are resolved below.

### Applying disconnected objects: allowed, conveyed through animation

The player may leave a chef or seat facing an empty cell rather than a usable belt tile. An inactive chef cannot load dishes and a customer at an inactive seat cannot take dishes. Convey this through idle animation only; do not show inactive badges, warnings, or connection-error markers on these objects. Connections are not a prerequisite for making an edit. Recovery is to rearrange or reconnect the object. Overlapping placements, insufficient funds, and unreachable walking routes remain separate undecided constraints.

### Shop and inventory: stable essentials and changing goods

A shop entrance is part of the restaurant scene and is accessible in live and edit mode. The shop scene has a restaurant doorway for returning, and returning preserves the current restaurant and edit state. The shop offers stable essentials such as belt tiles and normal chairs, alongside changing random goods such as fancier chairs and other objects. Purchased goods go into the player’s inventory. In edit mode, the inventory appears as a paginated bottom panel, and the player drags an item from it into the restaurant scene. Each newly placed belt tile consumes one inventory item, with the remaining count shown; reusing an existing neighboring belt does not consume a new item. Changing goods refresh after each expedition and have displayed limited quantities that decrement on purchase; stable essentials remain available in unlimited quantities. Most furniture is appearance-only, while a smaller subset has functional benefits that do not change customer patience or preferences. Items the player cannot afford remain visible with the price shown and their purchase control disabled.

### Object placement: drag from inventory

In edit mode, drag a purchased item from the paginated inventory into the scene. If released in an invalid location, the item returns to its source and the game briefly indicates why placement was rejected. Belt placement starts a connected path: after placing a tile, highlight and slowly blink its four surrounding cells; tapping a neighboring cell places or connects the next belt tile and continues the path. The bottom panel changes to controls for the most recently placed belt tile, including rotate, delete, and an X to return to inventory and leave path placement. Tapping outside the highlighted cells stops the path and returns the panel to inventory. The old type-selected, repeated-cell-tap flow is superseded.

### Belt placement: connected centerline paths

Belt tiles connect through their center points, and the connected line determines belt direction. Tap order adds path connections, while the geometry determines the route through each tile. During active path placement, tapping an existing neighboring belt can take that segment into the new path and reorient it, potentially breaking its prior route. Other tiles from the old route remain in place as separate segments. If the player taps the path’s starting belt tile, the route closes into a loop and path placement ends, returning the bottom panel to inventory. For example, a path can enter a tile from the left and turn downward; tapping the right neighbor can reorient the tile to run from left to right only. The path does not split or merge. Exact connection replacement for more complex overlaps remains to be worked out.

### Belt topology: paths and loops, without junctions

Each belt tile has at most one incoming and one outgoing connection. Open paths and closed loops are supported. Separate belts may coexist; belts do not split or merge. Chef positions, recipes, and seats provide distribution strategy without branch-routing or merge-priority controls.

### Chef upgrades: one Level Up action

Chefs use one purchased Level Up action to improve cooking speed according to the chef's predefined growth attributes. Shared level thresholds unlock whole recipe quality tiers: Wood, Steel, Copper, Silver, and Gold. A chef capped below a tier's threshold cannot reach it. This explicitly supersedes the earlier separate speed/quality upgrade purchases and fine-grained quality grades. Strategy centers on which chef to hire and develop. Quality tier gates recipe eligibility and does not modify a recipe's fixed sale price. Upgrade costs, growth curves, ceilings, and tier thresholds remain to be balanced.

### Customer access: real walking routes

Customers walk through empty floor cells and can use only seats they can reach. Belts, chefs, and seating consume grid space, so aisles compete with seating density. Movement is functional rather than merely decorative. Seat reservation, exit access after rearrangement, and edit validation for trapped customers remain undecided.

### Customer traffic: automatic passing and yielding

Walking customers yield or pass automatically rather than permanently blocking each other's floor cells. Furniture and grid layout determine walking access; opposing pedestrian traffic does not create deadlocks or require aisle-width optimization. Brief yielding animation may convey natural movement without a second congestion system.

### Economy: investment costs only

Operating the restaurant incurs no ingredient charges, wages, or other recurring cash costs. Coins fund purchases and upgrades, including belt tiles, seating, chefs, recipes, and improvements. Inefficiency reduces potential earnings but does not drain savings while idle. Prices, purchase unlocks, offline earning rules, and how removed objects return to inventory or coins remain undecided.

### Recipe differences: preparation time and sale price

Recipes differ in both preparation time and fixed sale price, in addition to customer preferences. The intent is to make menu selection consequential even without ingredient costs: faster, cheaper dishes and slower, more valuable dishes create different service patterns. Exact values and relative earning rates are not yet decided; numerical examples from the interview are illustrative only. Chef speed improves production relative to recipe preparation time. Quality gates eligibility, without adding a chef-dependent sale-price bonus.

### Chef management: live preview controls

Players can tap a chef in live preview to open recipe and upgrade controls while the restaurant continues operating. Recipe changes and purchased upgrades take effect immediately in live play. Paused edit mode is for rearranging and adding floor objects; those changes also persist immediately. Recipe-switch timing is resolved below.

### Belt capacity: one dish per tile, including the endpoint

Every belt tile holds at most one dish. The final tile of an open belt is an ordinary tile: an uneaten dish stops there and following dishes queue behind it. Customers taking nearby dishes create space and allow local motion to resume. There is no special endpoint stacking capacity, separate collection tray, or manual Clear tray control. These elements in earlier mockups are superseded.

### Removing purchased objects: return to inventory

Removing a purchased object returns it to the player’s inventory without refunding coins. This replaces the earlier full purchase-cost refund rule; see Question 120 in the active UI interview. Chefs remain hired staff rather than construction objects; their lifecycle is resolved below. Occupied-object removal is resolved below.

### Progression: persistent restaurant with paid obstacle clearance

The core game grows one persistent restaurant rather than resetting it across separate restaurant stages. Initially, only a small rectangular area is usable. Garbage occupies surrounding spaces as obstacles. Players spend cash to remove garbage and expand the workable floor. Clearance purchases are available in both live preview and edit mode, as resolved below. Patch costs remain undecided; patch selection and permanence are resolved below.

### Garbage clearance: predefined patches

Each clearance purchase opens a predefined patch of floor cells, such as a strip or rectangle. Players do not pay to clear individual cells. Patch shapes, placement, prices, and purchase controls remain undecided.

### Expansion choice: neighboring alternatives

Players choose among available neighboring expansion patches rather than following a single fixed sequence. Different patch shapes enable different near-term layouts. The choice governs expansion order, not permanent exclusivity between patches. Exact number of simultaneous choices and patch costs remain undecided; two initial choices was a recommendation, not a confirmed number.

### Cleared floor: permanent unlock

After a clearance purchase is applied, its floor patch remains available permanently. Garbage does not return, and the player cannot surrender cleared floor for a refund. Expansion provides lasting progression while the objects within it remain rearrangeable.

### Seat choice: food availability and chef blackboards

Among reachable empty seats, customers favor food that matches their preferences rather than choosing solely by distance. They consider dishes currently on nearby belts and the recipes advertised by nearby chefs. A small blackboard beside each chef shows what dish that chef is currently making. If no preferred food is available or advertised, customers can choose another reachable seat. Exact seating preference weights remain undecided.

### Chef blackboard footprint: integrated with the chef

The blackboard is part of the chef's one-cell footprint. It sits beside the character within that footprint and moves and rotates with the chef. It is not independently placed and does not require a separate cell or purchase. The representation of the advertised recipe remains undecided; a recognizable dish illustration was recommended but not separately confirmed.

### Recipe reassignment: immediate restart

Changing a chef's recipe immediately abandons unfinished preparation and replaces any completed dish the chef is holding, then starts preparing the new recipe from the beginning. The blackboard updates immediately. There is no ingredient charge or refund because production has no operating cost; the lost investment is preparation time. Completed dishes already on the belt remain unchanged.

### Hungry customers: eventual departure without lasting penalty

Customers who receive no food for a long time become visibly restless and eventually leave. Their departure frees the seat for another arrival. There is no fine, cash deduction, or lasting reputation penalty; the consequence is a missed sale. This no-food patience rule is distinct from the wait before accepting a nonfavorite dish. Exact timing and feedback animations remain undecided.

### Camera: fixed scale with panning

The restaurant camera uses a fixed scale rather than pinch-to-zoom. Players swipe to pan as the floor expands beyond the phone viewport. Cells and character art retain consistent size. Camera boundaries and handling panning while an object is selected remain undecided.

### Opening: working starter restaurant

The player begins with a working starter bar: a short open belt, one chef, and a few seats already serving customers and earning money. The first player action improves an observable system rather than assembling a restaurant from an empty floor. Exact starter geometry, seat and tile counts, starting cash, and first-edit guidance remain undecided.

### Occupied-object removal: allowed, with customer reactions

Occupied seats and belt tiles may be removed. A dish on a removed tile disappears without earning money. When an occupied seat is removed, its customer retains their meal progress and stays at the seat's former position, looking puzzled while searching for another reachable seat. They move only after finding one; they do not return to the entrance automatically.

If a new seat or similar sit-on object occupies a standing customer's position, seat them immediately. Otherwise push the customer to the nearest valid empty cell with a pushed animation. If a customer is trapped by the layout with no route to an exit or a seat, they show panic and move around slowly. Trapping is an allowed consequence of applying a layout, not an edit-validation failure. These reactions occur after the player exits edit mode; the simulation remains paused during editing. If no empty cell exists, block placement to prevent object/customer overlap. Customers can still become trapped through the surrounding layout, and they remain in the panic behavior until the player edits the layout or drags them to safety. Direct manipulation is resolved below.

### Customer rescue and edit layers

Players may directly select and drag a stranded customer into empty space during paused edit mode rather than repairing the walking route first. Edit mode exposes layers so the player can target people, seats/belt objects, or floor tiles without ambiguity between overlapping content. The people layer includes customers and chefs; this does not introduce a separate controllable player avatar. Floor tiles may support decoration; decoration mechanics and their effects are not yet confirmed. Directly dragging a customer preserves their visit, preference, and eating progress. The player can drop them onto any empty floor cell or free seat, including cells they could not reach by walking; direct placement on a free seat resumes their visit there. Exact selection of push destinations remains undecided.

### Layer selector: icons without visible text labels

Edit-layer controls use icons rather than visible text labels. The three conceptual layers are People, Layout, and Floor; these names describe the model but are not captions in the game UI. People targets customers and chefs, Layout targets seats and belt objects, and Floor targets floor tiles. Exact icon artwork, inactive-layer rendering, and accessibility implementation remain open.

### Floor appearance: cosmetic only

Floor changes personalize the restaurant without affecting customer behavior, earnings, patience, food preferences, or walking access. Decorative floor choices are not passive gameplay bonuses. Alternate styles are premium collectibles bought with restaurant coins through the rotating shop; owned styles are excluded from future shop selections. Any unowned style is eligible from the beginning, with price and appearance odds establishing rarity. At most one floor style appears in a shop rotation, and a rotation may have no floor-style offer. A style uses one of the normal rotating-goods slots. An unpurchased style may return on the next rotation; there is no recent-offer protection. Styles use three price levels—low, middle, and high—to reflect rarity or premium appeal, with higher-priced styles appearing less often. Exact values and appearance odds remain balance work. Buying a style immediately spends its shown price and unlocks it for unlimited floor tiles; applying it does not consume tile items. A shop offer shows a large multi-cell sample of the floor pattern with its name and restaurant-coin price, without a separate rarity marker. After purchase, a brief text-only toast beside the coin balance names the unlocked style and confirms it was added to the Floor palette. The player remains in the shop and can apply the style later from the Floor layer. The Floor layer opens with no style selected. In the visible, paginated bottom swatch grid, the player taps an owned style to activate it, then taps a cell to paint one tile or drags across floor cells to paint multiple tiles, including cells beneath placed objects. Matching painted tiles may use subtle visual variants and share shader effects spanning across cells, such as a slow ambient flare over multiple tiles of the same type. Purchased styles are ordered newest first; the original floor style appears last. The selected brush stays active after each stroke. Directional carets at the screen edges pan the scene while keeping the selected style ready: a tap smoothly pans four grid tiles in that direction, holding continues panning, and releasing resumes painting. Carets are hidden for directions where the scene cannot move farther. The exact motion duration remains tuning work. A top X clears the brush and keeps the player in the Floor layer with the palette open. The original floor appearance is a free palette option. Cosmetic changes take effect immediately when made.

After a floor-style purchase, its current offer remains visible as Owned until the next shop refresh. The card keeps the pattern preview and style name but replaces the price and Buy action with the Owned state. Rotating shop goods refresh as soon as the player returns from an expedition, ready for the next shop visit; a small sparkle or glow badge on the shop entrance signals new stock until the player opens the refreshed shop.

### Full closed loops: simultaneous circulation

A closed belt loop continues circulating when every tile holds a dish: all plates advance together. A plate may enter an occupied next tile if that tile's plate advances simultaneously. Chefs still wait for a free loading tile before adding food. Closing a loop gives uneaten dishes repeat exposure to customers without introducing stacking capacity or manual clearing. Open endpoints still create backpressure.

### Offline earnings: restaurant layout matters

The restaurant earns while the app is closed according to the actual committed setup, including food distribution, congestion, customer access, and chef production. Offline income is not a generic allowance based only on purchased chefs and upgrades. Better layout strategy should improve both live and offline earnings. Operating costs and lasting penalties remain absent. The method of calculating offline performance remains undecided.

### Offline accumulation: unlimited

Offline earnings accumulate for the entire absence, without a time-based accrual cap or a required check-in to continue earning. Returning after a long absence may provide a large sum; progression must accommodate it. Layout improvements remain valuable because they increase future earning performance. Estimate offline earnings from the committed layout's production and customer throughput over the elapsed time, without simulating each individual visit; assume new customers continue arriving and filling reachable seats. Use each connected chef's assigned recipe, price, quality, and preparation time, preserve actual belt paths, loading points, and customer access as delivery bottlenecks, and use average preference demand to estimate how quickly dishes are taken. Restore the saved customer positions, meal progress, and belt dishes after the calculation rather than advancing each temporary state. On reopening, credit the total automatically, show the total in a top toast, and fade the toast out; animate the coin count rolling up to the new balance like a slot machine.

### Recipe unlocks: restaurant-wide, gated by quality tier

Recipes unlock for the restaurant rather than being taught separately to each chef. Each recipe belongs to a named quality tier: Wood, Steel, Copper, Silver, or Gold. A chef may prepare an unlocked recipe when its tier is at or below the highest tier that chef has unlocked. The shared starting thresholds are Wood 1, Steel 3, Copper 5, Silver 8, and Gold 12; a chef capped below a tier's threshold cannot reach it. These values remain open to balance tuning.

### Chef level advancement: purchased Level Up

Chef development advances through purchased Level Up actions, not a separate cooking-experience track. Each action improves cooking speed according to predefined growth attributes. Reaching designated chef levels unlocks whole quality tiers and therefore more recipes. Tier thresholds and upgrade costs remain undecided.

### Chef lifecycle: hire, assign, unassign, or fire

Chefs are hired staff, not construction objects that can be sold by removing them from the floor. Hiring adds a chef to the roster as unassigned staff; the player can later assign them to an ordinary floor cell. Removing them from that cell unassigns them and retains the chef, their level, and their upgrades for later reassignment. Firing is a distinct action that makes that chef disappear permanently and returns no cash. Tapping Fire opens a confirmation naming the chef before removal. Tapping the chef button opens the chef panel and roster. Each roster row shows the chef portrait, level, and assigned or unassigned status. Selecting a chef opens a separate detail popup with their level, attributes, recipe, and management actions. The paid Level Up action appears there beside the chef's level, growth, and next cost. The popup previews the current-to-next cooking-speed change and flags any recipe-tier unlock. When affordable, tapping Level Up immediately deducts the cost and applies the level without confirmation. At the chef's maximum level, the popup keeps their final stats and shows a noninteractive MAX status in place of Level Up and cost. A button there opens a separate applicants popup; there are no tabs. Exact button placement and popup layout remain undecided. The earlier question proposing chef removal refunds did not establish a decision and is superseded by this lifecycle.

### Hiring: applications expose predefined chef attributes

Each chef has predefined attributes that the player can learn by viewing their job application before hiring. These attributes determine strengths, growth speed, capability ceiling, highest quality tier reachable at that ceiling, and hiring cost. They differentiate candidates and make replacing limited-capability chefs with better-suited applicants meaningful. Growth, staff capacity, and application availability are resolved below; exact attribute formulas remain undecided.

### Staff capacity: proportional to workable floor space

Assigned and unassigned hired chefs both count toward a staff limit. That limit grows proportionally with the restaurant's cleared workable space. Firing frees a roster slot for a new applicant; unassigning does not. Show the current and maximum staff count in both the chef panel and applicants popup. At the staff limit, the applicants popup shows the roster is full and disables Hire until the player expands or fires a chef. Capacity depends on available floor area, not the amount left empty after furniture placement. This makes expansion useful for both layouts and staff retention. The floor-area-to-capacity ratio and rounding thresholds remain undecided.

### Growth and recipe eligibility: chef levels unlock quality tiers

Growth speed means larger cooking-speed boosts on each level-up, not cheaper upgrade costs or shorter training timers. Chef level thresholds unlock whole recipe-quality tiers, and recipes are eligible when their tier is at or below the chef's highest unlocked tier. This replaces fine-grained recipe and chef quality grades. Higher-tier chefs retain access to simpler recipes.

Each level-up improves cooking speed through one paid Level Up action; designated level thresholds unlock quality tiers. The user explicitly confirmed replacing the earlier separate speed/quality purchase controls. Quality tier gates recipe eligibility but does not modify fixed recipe prices. Do not implement the superseded separate-upgrade model alongside the confirmed model.

### Recipe sale value: fixed by recipe

A recipe sells for its fixed price regardless of the preparing chef's quality tier. Each higher recipe tier has a higher fixed-price band than every lower tier; quality unlocks recipe eligibility, while chef speed governs production rate. Preparation time varies independently of tier and price, so a higher-tier recipe may be quicker than a lower-tier recipe and a longer recipe within a tier does not guarantee a higher price. There is no chef-quality price multiplier. Exact recipe prices remain a balance decision.

### Recruitment: changing applications, retained until refresh

Recruitment presents a changing set of three applications rather than a permanent catalogue of all chefs. Candidates expose their predefined attributes before hiring. Unhired applications stay until the player chooses to refresh them rather than expiring while the player is absent. Tapping Hire immediately deducts the visible cost, adds the chef to the roster as unassigned staff, and removes that candidate from applications. If the player lacks coins or staff capacity, Hire is disabled while the cost remains visible. The applicants popup remains open showing the remaining candidates, and the opening stays empty until refresh. Each set is generated to offer distinct tradeoffs across chef attributes rather than three undifferentiated random candidates; exact attribute distributions remain balance work. The full set of three applications is replaced on refresh, with no individual pinning; refresh availability and cost are resolved below.

### Chef assignment footprint: ordinary floor cell

A chef's working spot is an ordinary floor cell next to a belt, not a separately built station. The player can drag an unassigned chef from the People layer in either live or edit mode; placing them immediately opens dish selection, and closing it leaves them idle. Assigning a chef occupies one cell, moving them changes the assignment, and unassigning them frees the cell. Their integrated blackboard follows them. There is no empty chef-station object or station purchase after unassignment.

### Application refresh: free, with a cooldown

Refreshing applications is free and becomes available after a cooldown. Tapping Refresh immediately replaces all three candidates and starts the cooldown, with no confirmation. Offers do not expire merely because the cooldown ends or the player is absent. Exact cooldown duration remains undecided.

### Chef capability ceiling: maximum chef level

A chef's predefined capability ceiling is their maximum chef level. At that level, further level-ups stop, so their final cooking speed and highest unlocked quality tier derive from starting attributes, per-level growth, and shared tier thresholds. A chef capped below a tier's threshold cannot reach it. Speed and quality do not have independent purchased cap systems. Exact maximum levels and the initial tier thresholds remain balance decisions.

### Financial feedback: no earning-rate display

Do not show earnings per minute or any earning-rate metric. The player sees their cash balance and diagnoses service through customer behavior, dish movement, chef activity, and sales feedback. Restaurant coins earned during an expedition stay pending and are credited when the player returns. After any outcome with earnings, show the credited total beside the updated cash balance; this is separate from expedition salvage and is not an earning rate. Suppress the notice when the total is zero. The brief text popup fades away without requiring dismissal. The earlier no-earnings-report choice is superseded only for this requested away-earnings total.

### Preference feedback: timed dish bubble and satisfaction cue

Customers show a dish-preference thought bubble with a circular progress indicator counting down their willingness to wait for the preferred dish. If it expires, they take whatever dish becomes available next at their facing belt tile. If the preferred dish is received, the bubble briefly becomes a happy face and fades while the customer plays a small celebratory body bounce. The timer is about dish preference, not fullness or plates remaining; fullness stays hidden. The preference cycle runs once per visit, as resolved below. Countdown duration and the exact animation timing remain tuning work. The no-food departure timer remains distinct from this fallback timer.

### Preference cycle: once per visit

The preference bubble and its countdown govern only the customer's first dish. After receiving that dish, preferred or fallback, the customer takes whatever becomes available for the rest of the meal. The preference timer does not renew between dishes. Hidden individual fullness still determines meal completion and departure.

### Chef preparation buffer: one held dish

A chef may prepare one dish while their loading tile is occupied and hold the completed plate until that tile has room. Once loaded, the chef begins preparing the next dish. There is no hidden stockpile or multi-dish chef buffer. Holding a finished plate visually conveys loading congestion. Recipe reassignment replaces the held dish and starts the new recipe immediately, just as it resets unfinished preparation.

### Eating duration: broadly similar across recipes

Recipes do not introduce strategically different eating durations. Their principal differences remain preparation time, fixed price, recipe-tier requirement, and customer preferences. Customer appetite remains individual and hidden. Balance must test the risk that the highest-priced available recipe dominates once chef speed is sufficient; recipe preparation curves and chef capability ceilings, rather than eating-time differences, must keep choices meaningful.

### Customer arrivals: grow with cleared floor area

Customer arrivals increase automatically as the restaurant's cleared workable area grows. There is no separate demand or marketing upgrade required for expansion to attract more potential customers. The layout determines whether those arrivals can find seats and receive food. Exact arrival rates and growth curves remain balance decisions.

### Expansion purchases: available in both modes

Players can purchase expansion patches in live preview as well as edit mode. Tapping a garbage patch pans the scene to center its highlighted footprint and opens a price card in the bottom half of the screen, with Clear and Cancel actions; unselected patches do not show prices; outside taps leave it open. Confirming spends the visible cost and permanently clears the patch. This applies immediately in either mode, and cleared floor cannot be refunded. If the player cannot afford the patch, its price remains visible and Clear is disabled. After the card closes, the camera stays centered on the selected patch whether the player confirms or cancels.

## Interview order

Resolve the recurring activity first; then customer success and failure, transport and production rules, spatial constraints, phone controls, automation, and progression. Ask one decision at a time, with a recommendation and a concrete scenario. Record confirmed decisions as they emerge; use ADRs only for consequential tradeoffs.
