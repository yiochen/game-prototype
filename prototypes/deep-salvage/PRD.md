# Deep Salvage — playable prototype PRD

## Fantasy and objective

Guide the engineering of a small yellow submarine through the ruins of a drowned dystopia. Navigation and shooting are automatic; the player survives by salvaging components and composing a working weapon circuit. Survive three encounters to reach the safe beacon. Hull reaching zero ends the dive. A complete run takes roughly two minutes of simulation, plus engineering and reading time.

## Agreed design

- Portrait mobile first. The upper half is the animated world; the lower half is the weapon lab with a full-width parts hold beneath both the grid and the always-visible vertical forge strip on the right. Cartoon shapes, thick ink outlines, cream instrument panels, turquoise beams, yellow machinery and purple enemies.
- The submarine follows a predefined route, never dodges, and automatically fires every powered gun at incoming enemies. Multiple guns choose targets independently.
- The lower panel is one 7 × 7 surface: a 6 × 5 lab, five forge cells in the right column, and two seven-cell storage rows along the bottom. Every part occupies exactly one square. Beams cross empty cells without needing connectors. Part order, rotation, branching and limited space create the puzzle.
- Every defeated enemy pays cash automatically. Roughly one in four also drops a component (the first kill is guaranteed salvage). Drops fall to the floor, remain selectable, flash shortly before expiring, then disappear.
- Tap a battlefield drop to salvage it into storage. Drag it directly into the lab to install it, or into storage to save it.
- Identical parts stack in storage only. Dragging a stack removes one copy only after a valid placement. Installed parts may be dragged to another empty cell or returned to storage.
- Tap an installed reactor or mirror to rotate it clockwise by 90 degrees. Amplifiers, splitters, lenses and guns accept inputs from any side and do not rotate. Circuit changes apply immediately. Tap is not an information dialog.
- First acquisition of a new part type pauses the game and shows a short explanation. Duplicates never interrupt play. Discoveries persist locally between runs. The Parts Guide pauses the dive and explains every prototype part, marking undiscovered types.
- Dragging slows simulation to 20%. A held drop cannot expire. Pointer cancellation or invalid placement returns the part to its source without consuming it. Dropping on an occupied cell does not swap parts.

## Prototype rules and chosen defaults

### Level selection

The welcome screen presents the game title, a “Levels” picker and the start button. Remove the story paragraph, salvage/rotation instructions, support-terminal explanation and per-level descriptive sentences. Each level card uses a distinct generated environment background: drowned watchtowers for Sunken City, a glowing green kelp forest for Kelp Wilds, and broken pipes with volcanic light for Cinder Foundry. The images provide setting context; only the level name, difficulty and wave count appear over them. A border and checkmark identify the selected level. Full gameplay explanations remain in the manual.

The picker fits smaller portrait phones without scrolling. Short landscape screens place the three level cards side by side. Image backgrounds are decorative; button text provides accessible names, and keyboard selection works. Choosing a level still requires pressing the start button; backing out preserves the active dive. Artwork and generation prompts are recorded in `assets/levels/PROMPTS.md`.

### Engineering layout and fixed storage slots

The lower panel contains only the 7 × 7 engineering surface: tiles, beams, stack counts, tier badges, charge/forge progress. No labels, headings, explanatory text or Forge button occupy it. The upper HUD keeps wave number, cash, hull/shield meters and icon-only guide/pause controls. Instructions and recipe details remain in the manual, with accessible names on every control.

Storage has a fixed capacity of fourteen stacks, all visible in a 7 × 2 arrangement. Identical parts share one slot and can stack even when all fourteen slots are occupied. There are no pages, navigation arrows or scrolling gestures. Dragging works in every direction; tapping a stack then an empty lab/forge cell still places one copy.

Occupied stacks retain their positions. Using the last copy frees that slot for another type; other stacks never shift. New types use the first empty slot. When storage is full, a new type cannot be salvaged or returned to storage: the part stays at its source, no quantity is consumed, no discovery is triggered, and a brief “Storage full” notification explains the rejection. A battlefield part can still be dragged directly into an empty lab or forge cell. Failed salvage leaves the drop's normal expiry timer running. A fresh dive resets storage.


| Area | Grid allocation | Interaction |
| --- | --- | --- |
| Weapon lab | Rows 1–5, columns 1–6 | Place one-square parts, rotate directional parts and preview beam changes. |
| Forge | Rows 1–5, column 7 | Stage any parts; complete affordable recipes start automatically. |
| Storage | Rows 6–7, columns 1–7 | Fourteen fixed stack slots; no pagination or scrolling. |

The entire bottom two rows, including their rightmost cells, belong to storage. The forge has five ingredient slots. Every lab, forge and storage cell uses the same square size.


### Components

| Part | Behavior |
| --- | --- |
| Reactor | Emits a directional beam. One starter reactor; an extra core can be salvaged later in the dive. Movable and rotatable. |
| Mirror | Reflects rays by 90 degrees; the mirror diagonal is visible. |
| Amplifier | Multiplies incoming power by 1.5, up to a per-beam safety cap. Accepts any input side and preserves travel direction. |
| Splitter | Accepts any input side and emits left/right branches perpendicular to that incoming beam, each with half its power. |
| Lens | Accepts any input side and passes it straight through as piercing fire; a pierced shot can also hit an enemy behind the target. |
| Laser gun | Converts received beam power into a continuous tracking beam with small damage ticks. Accepts beams from all four sides, independent of rotation. Multiple inputs combine up to the safety cap. |
| Shield | Stores 32 energy, then restores 12 shield, capped at 24. Fully charged terminals wait if the shield is full. |
| Medic | Stores 48 energy, then repairs 12 hull, capped at 100. Fully charged terminals wait if the hull is full. Cannot revive a destroyed submarine. |
| Pulse gun | Terminal accepting all four sides. Stores 36 energy, then releases a 54-damage pulse. Input power controls charge speed; piercing carries through. |

Empty-space beams travel in cardinal directions. Crossing beams do not interact. Beams hitting a reactor stop and are marked at the collision. Other components accept incoming beams from every side. Rays that leave the grid dissipate. Repeated directed visits terminate loops; no infinite energy feedback. Merged inputs sum up to the safety cap. Only reactor emission and mirror reflection depend on rotation. Mirrors have two visually distinct orientations.

### Combat and drops

Three waves of 8, 13 and 18 enemies introduce scout drones, fast swarms, armored crabs and shielded wardens, separated by a short refit interval. Target the closest enemy in range. Enemies approach and attack the vessel; it does not evade. Beam damage depends on the circuit, with armor and piercing interacting visibly. Drop lifetimes are 12 simulation seconds after landing, flashing in the final 3. Drops drift slowly with the seabed but stay reachable for their lifetime. Pause, manual, discovery, backgrounding and end screens stop all gameplay clocks. New discoveries appear only after the collection/placement gesture completes.

The initial lab fires through one amplifier into one gun. The hold starts with a spare laser gun, a pulse gun, Shield, Medic, an extra reactor, two mirrors and two spare amplifiers. The player starts with 24 cash, enough for an Overcharger. The first defeated drone drops a splitter so the player can expand into two branches quickly. Exact numbers live in balance.js, separate from rules. The starter weapon survives the opening wave but loses in wave two. Forging an Overcharger early and installing the first salvaged lens is a viable path, with substantial hull damage in the final wave.

Laser damage accumulates continuously at 1.1 times input power per second before armor. Armor reduces input power before the rate multiplier, with a floor of 1 damage per second. Laser impact labels aggregate every 0.35 seconds to stay readable; their beam follows the current target continuously. Pulse guns collect input power as energy per second: the starter 12-power circuit charges in 3 seconds, while an 18-power circuit charges in 2. A pulse deals 54 damage before armor, applied once, and then recharges. Fully charged guns wait for a target. Charge remains with a part when moved within the grid or disconnected; disconnected terminals cannot fire or charge. Returning a part to stacked storage clears its charge. Both weapons obey pause and slowed engineering time, fire independently, and inherit lens target counts and armor bypass.

The submarine starts with a 24-point shield. Damage drains the shield before hull; after six seconds without being hit, it regenerates three points per second. Enemy wardens carry a non-regenerating shield over armored hull. Piercing bypasses armor, hits additional targets, and still has to drain shields. Cash awards range from 5 to 18 by enemy type. Each map schedules 39 enemies. Killing all of them yields 10 part drops; bombers that self-detonate reduce kill rewards.

### Support terminals and route atlas

Shield and Medic accept energy from all four sides and terminate beams. Multiple inputs combine up to the same power cap as guns. Their charging is independent of weapon terminals. More power shortens the cycle; lenses do not add healing targets or bypass resource caps. Support charge follows grid moves, freezes while disconnected or paused, and clears when stacked in the hold. At full shield/hull, terminals hold a ready charge; restoration triggers automatically when damage creates room, including during the shield regeneration cooldown. Repairs cannot revive a destroyed submarine. Blue restoration rings and green repair rings/positive numbers distinguish these events from damage. The lab shows visual charge bars, a ready glow and unique enhanced icons for the two forged upgrades. Charge values remain available to assistive technology.

Three maps are selectable from the opening route picker and from pause/end screens. Selection does not reset the active dive until the player starts the route; Back returns to the current run. Restart preserves the chosen map. Each map has three encounters with 8, 13 and 18 enemies. City retains the original armored/shielded composition. Kelp Wilds introduces fast attackers, shield drain and healing allies in a tall luminous forest. Cinder Foundry features pipework, volcanic vents, armored bulwarks, snipers and bombers. Map palettes, geometry, route bob amplitude, depth readout and encounter schedules differ. This is authored route variety, not procedural map generation.

| New enemy | Distinct behavior / counter |
| --- | --- |
| Needle dart | Fastest movement, fragile hull; continuous laser avoids pulse overkill. |
| Bulwark | 300 HP and 9 armor, slow; piercing and strong pulses are useful. |
| Harpoon sniper | Stops 0.6 world-width from the submarine, shoots every 3 seconds, telegraphs its final second with an aiming line. |
| Volt leech | Drains twice the normal shield per hit; hull spillover accounts for shield absorption correctly. |
| Reef mender | Restores nearby allies for 5 HP/s within 0.22 world units; cannot heal itself or exceed max HP. Green links reveal its targets. |
| Depth bomber | 26-damage attack consumes the bomber. Destroying it first gives cash/salvage; a self-detonation gives no kill rewards. |

All ten enemies have distinct art and a field-guide entry with stats and counters. New enemy stats and all map encounter tables live in `balance.js`. Kelp rewards crowd control; Foundry requires further weapon upgrades beyond the initial Overcharger/lens route. An earned-cash Heavy laser forged in the first refit is a verified winning route. The same city weapon build ends at 54 hull unaided, 70 with Medic, or 80 with Shield on the spare reactor. These are deterministic example builds, not a guarantee for every placement.

### Forge

The forge occupies the rightmost column above storage, with five square slots and no heading, explanatory text or start button. The 6 × 5 lab and forge share the same cell size. Storage spans both complete bottom rows. All controls remain visible without tabs.

Drag any part from the hold, battlefield or lab into an empty forge slot. Parts do not need to contribute to a recipe. Empty slots continue accepting parts while a job runs; only the ingredients of that job lock. Unlocked ingredients can be moved to another forge slot, installed in the lab, dragged back to storage, or tapped to return them. Occupied slots reject placement without consuming anything.

Recipes are unordered ingredient multisets with exact quantities. A recipe can match within a larger collection of forge contents: unrelated items do not block it and are not consumed. As soon as a complete recipe is affordable, it starts automatically, deducts cash once and locks its matching slots. If cash is short, it waits for earnings; if another job is running, it waits for completion. One job runs at a time. If multiple affordable recipes match simultaneously, recipe-table order provides deterministic priority. Paid jobs cannot be cancelled.

No recipe may be a subset of another recipe, accounting for duplicate quantities. This prevents automatic forging from consuming an intended larger recipe halfway through assembly. The three- and four-part recipes use distinct upgraded ingredients to preserve this property. Automated tests enforce the invariant for every pair. All thirteen recipes are listed in the manual from the start, including quantities, output effects, prices and durations.

After adding an ingredient, possible remaining partners glow in the lab, hold and battlefield; unrelated ingredients do not suppress suggestions. While working, the selected slots show gold borders and progress bars. Completion clears only the consumed ingredients and triggers the output’s normal first-discovery introduction. If storage has room or already contains that output type, the result joins its stack. Otherwise, the output remains as an unlocked part in the first consumed forge slot; no output is discarded and capacity is never exceeded. The player can install it directly or tap/drag it into storage after freeing a slot. Other forge ingredients remain in place. Forge timing obeys pause, discovery dialogs, backgrounding and slowed engineering time.

| Ingredients | Output | Effect | Cash / seconds |
| --- | --- | --- | --- |
| 2 Shields | Aegis shield | Restores 20 shield per 32 energy | 28 / 7 |
| 2 Medics | Repair bay | Repairs 20 hull per 48 energy | 32 / 8 |
| Laser gun + reactor | Pulse gun | Stores energy, releases 54 damage | 24 / 6 |
| 2 reactors | Fusion core | Emits 12 energy | 30 / 8 |
| 2 mirrors | Prism mirror | Turns and amplifies ×1.25 | 16 / 5 |
| 2 amplifiers | Overcharger | Amplifies ×2.4 | 24 / 6 |
| 2 splitters | Trident | Three branches, each with half power | 30 / 7 |
| 2 Tridents | Duplicator | Three branches, each with full power | 65 / 10 |
| 2 lenses | Rail lens | ×1.25 power, piercing up to three enemies | 28 / 7 |
| 2 laser guns | Heavy laser | ×1.6 continuous damage | 24 / 6 |
| Amplifier + lens | Piercing amplifier | ×1.75 power and two-target piercing | 32 / 8 |
| Piercing amplifier + Overcharger + Rail lens | Prism overcharger | ×2.8 power and two-target piercing | 42 / 9 |
| Trident + Prism mirror + Fusion core + Heavy laser | Duplicator | Three branches, each with full power | 60 / 10 |

All outputs remain one square and inherit their base component's input rules. Only cores and mirrors rotate. Recipe data lives in recipes.js; component power rules live in balance.js.

### Controls and feedback

All battlefield drops have large hit targets. A drag preview stays above the finger. Its rendered center determines both the highlighted target and the final drop destination, for grid cells and storage. Empty cells highlight, an outline marks the intended destination, and the live beam preview shows what placement would do. Beam width scales with energy, weakened split branches become thinner/dimmer, amplified paths turn gold, and piercing paths become blue with longer, faster traveling dashes. There are no textual tile readouts. Pulse guns use a distinct pink capacitor icon, a charge bar and a ready glow. The submarine shows a growing charge ring and bright pulse projectile on release. Forged upgrades have enhanced icons: fusion core housing, faceted prism mirror, twin-chevron amplifier, three-way splitter branches, full-power splitter diamond, rail lens, double-barrel gun, and crystal amplifier/lens hybrids. Forged tiers also carry II/III badges. Hits produce sprite flashes, recoil and floating damage numbers; shield impacts produce blue expanding rings, and cash floats upward on a kill. A blue shield meter sits under the hull meter. Storage accepts dragged tiles anywhere in its panel. Desktop pointer and keyboard controls supplement touch: focus a reactor or mirror and press Enter/Space to rotate; select a stored part then choose an empty cell to install; arrow keys navigate cells; Delete/Backspace returns a focused installed part to storage. Pause is always available.

## Screen and device acceptance

Google lists the Pixel 10 Pro display as 1280 × 2856 physical pixels (https://store.google.com/product/pixel_10_pro_specs?hl=en-US). Physical pixels do not uniquely determine browser CSS viewport: density, display scaling, safe areas and browser bars vary. Validate at 412 × 924 and 448 × 1000 CSS pixels, shorter 412 × 820 and 360 × 740 phone viewports, and 924 × 412 landscape. Use dynamic viewport height and safe-area insets. No page scrolling or clipped controls in normal play. Main controls are at least 44 CSS pixels; portrait grid cells stay approximately 44–60 pixels. Landscape places world and console side by side. Desktop presents a centered portrait game cabinet.

## Implementation boundaries

Phaser 3 renders the world and effects. Framework-independent engine.js owns beam tracing, inventory, simulation and combat. DOM/SVG renders the lab, beam paths, readable UI, manual and dialogs. A single pointer controller handles cross-boundary dragging. The prototype owns all assets, dependencies, rules, documentation and tests; no sibling-game imports.

## Validation

Engine tests cover beam travel, rotation, splitting, amplification, piercing, inputs from all four sides, cycles, inventory transactions, loot expiry/protection, damage, shields, sparse drops/cash, every forge recipe, affordability, atomic cancellation, timer pauses, upgraded beam effects, and win/loss. Browser tests exercise the real UI: start, tap salvage, first discovery, repeat salvage, install/rotate/retrieve tiles, cancelled/invalid drags, manual/pause/restart, mobile touch input, duplicate and mixed forging, match highlights, upgraded beam visuals, shield effects and responsive bounds. Capture actual Phaser canvas screenshots at Pixel-shaped portrait and landscape sizes and inspect them. Run all repository engine tests and the production build.

### Layout and automatic forge acceptance criteria

- Normal play shows a single 7 × 7 lower panel without labels, explanations, textual power readouts or a Forge button. Stack counts, tier badges and visual progress remain visible.
- The panel contains 30 lab cells, 5 forge cells and 14 storage cells, all visible at once. There are no pagination controls or swipe scrolling.
- Occupied storage stacks never shift. Depleting a stack frees one slot; adding a fifteenth distinct type fails without consuming its source. Identical types can still join existing stacks.
- Any part can enter an empty forge slot, even if it contributes to no recipe or another job is running.
- Adding the last required ingredient starts an affordable recipe automatically. A complete recipe waiting for cash starts when sufficient cash arrives; a queued recipe waits for the current job.
- Starting a job deducts cash once and locks only its matched ingredients. Completion consumes only those ingredients and preserves unrelated parts. Its output goes to storage if it fits, otherwise remains recoverable in the forge.
- Every recipe appears in the manual with exact ingredients, cost, duration and output. For any two recipes, neither ingredient collection may be contained in the other, counting duplicate quantities; automated checks must reject duplicates and subset recipes.

## Explicitly deferred

Permanent upgrades, shops, bosses, sound/music, cloud saves, multiple vessels, procedural routes, component durability, heat, multiplayer, and production deployment. Discovery state is persistent; run state resets on reload. This prototype tests whether assembling a visible machine while collecting loot is fun.
