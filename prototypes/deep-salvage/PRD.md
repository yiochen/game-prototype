# Deep Salvage — playable prototype PRD

## Fantasy and objective

Guide the engineering of a small yellow submarine through the ruins of a drowned dystopia. Navigation and shooting are automatic; the player survives by salvaging components and composing a working weapon circuit. Survive three encounters to reach the safe beacon. Hull reaching zero ends the dive. A complete run takes roughly two minutes of simulation, plus engineering and reading time.

## Agreed design

- Portrait mobile first. The upper half is the animated world; the lower half is the weapon lab with a separate parts hold. Cartoon shapes, thick ink outlines, cream instrument panels, turquoise beams, yellow machinery and purple enemies.
- The submarine follows a predefined route, never dodges, and automatically fires every powered gun at incoming enemies. Multiple guns choose targets independently.
- Every part occupies exactly one square of a 5 × 5 grid. Beams cross empty cells without needing connectors. Part order, rotation, branching and limited space create the puzzle.
- Defeated enemies drop components. Drops fall to the floor, remain selectable, flash shortly before expiring, then disappear.
- Tap a battlefield drop to salvage it into storage. Drag it directly into the lab to install it, or into storage to save it.
- Identical parts stack in storage only. Dragging a stack removes one copy only after a valid placement. Installed parts may be dragged to another empty cell or returned to storage.
- Tap an installed reactor or mirror to rotate it clockwise by 90 degrees. Amplifiers, splitters, lenses and guns accept inputs from any side and do not rotate. Circuit changes apply immediately. Tap is not an information dialog.
- First acquisition of a new part type pauses the game and shows a short explanation. Duplicates never interrupt play. Discoveries persist locally between runs. The Parts Guide pauses the dive and explains every prototype part, marking undiscovered types.
- Dragging slows simulation to 20%. A held drop cannot expire. Pointer cancellation or invalid placement returns the part to its source without consuming it. Dropping on an occupied cell does not swap parts.

## Prototype rules and chosen defaults

### Components

| Part | Behavior |
| --- | --- |
| Reactor | Emits a directional beam. One starter reactor; no extra reactor loot in this version. Movable and rotatable. |
| Mirror | Reflects rays by 90 degrees; the mirror diagonal is visible. |
| Amplifier | Multiplies incoming power by 1.5, up to a per-beam safety cap. Accepts any input side and preserves travel direction. |
| Splitter | Accepts any input side and emits left/right branches perpendicular to that incoming beam, each with half its power. |
| Lens | Accepts any input side and passes it straight through as piercing fire; a pierced shot can also hit an enemy behind the target. |
| Gun | Converts received beam power into automatic world attacks. Accepts beams from all four sides, independent of rotation. Multiple inputs combine up to the safety cap. |

Empty-space beams travel in cardinal directions. Crossing beams do not interact. Beams hitting a reactor stop and are marked at the collision. Other components accept incoming beams from every side. Rays that leave the grid dissipate. Repeated directed visits terminate loops; no infinite energy feedback. Merged inputs sum up to the safety cap. Only reactor emission and mirror reflection depend on rotation. Mirrors have two visually distinct orientations.

### Combat and drops

Three waves introduce scout drones, small swarms, and armored crabs, separated by a short refit interval. Target the closest enemy in range. Enemies approach and attack the vessel; it does not evade. Beam damage depends on the circuit, with armor and piercing interacting visibly. Drop lifetimes are 12 simulation seconds after landing, flashing in the final 3. Drops drift slowly with the seabed but stay reachable for their lifetime. Pause, manual, discovery, backgrounding and end screens stop all gameplay clocks. New discoveries appear only after the collection/placement gesture completes.

The initial lab fires through one amplifier into one gun. The hold starts with a spare gun and two mirrors. The first defeated drone drops a splitter so the player can expand into two branches quickly. Exact numbers live in balance.js, separate from rules.

### Controls and feedback

All battlefield drops have large hit targets. A drag preview stays above the finger. Its rendered center determines both the highlighted target and the final drop destination, for grid cells and storage. Empty cells highlight, an outline marks the intended destination, and the live beam preview shows what placement would do. A connected-gun count makes the effect legible. Storage accepts dragged tiles anywhere in its panel. Desktop pointer and keyboard controls supplement touch: focus a reactor or mirror and press Enter/Space to rotate; select a stored part then choose an empty cell to install; arrow keys navigate cells; Delete/Backspace returns a focused installed part to storage. Pause is always available.

## Screen and device acceptance

Google lists the Pixel 10 Pro display as 1280 × 2856 physical pixels (https://store.google.com/product/pixel_10_pro_specs?hl=en-US). Physical pixels do not uniquely determine browser CSS viewport: density, display scaling, safe areas and browser bars vary. Validate at 412 × 924 and 448 × 1000 CSS pixels, shorter 412 × 820 and 360 × 740 phone viewports, and 924 × 412 landscape. Use dynamic viewport height and safe-area insets. No page scrolling or clipped controls in normal play. Main controls are at least 44 CSS pixels; portrait grid cells stay approximately 44–60 pixels. Landscape places world and console side by side. Desktop presents a centered portrait game cabinet.

## Implementation boundaries

Phaser 3 renders the world and effects. Framework-independent engine.js owns beam tracing, inventory, simulation and combat. DOM/SVG renders the lab, beam paths, readable UI, manual and dialogs. A single pointer controller handles cross-boundary dragging. The prototype owns all assets, dependencies, rules, documentation and tests; no sibling-game imports.

## Validation

Engine tests cover beam travel, rotation, splitting, amplification, piercing, inputs from all four sides, cycles, inventory transactions, loot expiry/protection, damage, pause, and win/loss. Browser tests exercise the real UI: start, tap salvage, first discovery, repeat salvage, install/rotate/retrieve tiles, cancelled/invalid drags, manual/pause/restart, mobile touch input and responsive bounds. Capture actual Phaser canvas screenshots at Pixel-shaped portrait and landscape sizes and inspect them. Run all repository engine tests and the production build.

## Explicitly deferred

Permanent upgrades, shops, bosses, sound/music, cloud saves, multiple vessels, procedural routes, component durability, heat, multiplayer, and production deployment. Discovery state is persistent; run state resets on reload. This prototype tests whether assembling a visible machine while collecting loot is fun.
