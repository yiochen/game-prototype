# Kitchen line design

Status: prototype the user approved, including the seared-nigiri fix. Not yet built in Godot.

- Prototype: [`design/kitchen-line-preview/`](../design/kitchen-line-preview/). Rules live in `engine.js` and tuning lives in `balance.js`.
- Tests:
  - [`tests/kitchen-line.test.js`](../tests/kitchen-line.test.js) covers the engine.
  - [`tests/kitchen-line-preview.spec.js`](../tests/kitchen-line-preview.spec.js) covers the browser.
- Live: https://yiochen.github.io/game-prototype/prototypes/sushi-loop/design/kitchen-line-preview/

## Why

In the current game the only reason to build a bigger belt is to seat more guests, so building the belt is not much fun. The goal was to make belt building the core puzzle: a growing assembly line the player keeps revising and enjoys watching run.

The user steered the design toward these principles:

- Constraints that appear one at a time, like Mini Motorways. New demands force the player to revise an earlier layout.
- A line that builds up to something great, with no decay or upkeep.
- Rules simple enough that nothing has to be memorised. No plate ordering, no smart machines and no hidden routing.
- Tidy, predictable layouts. A messy belt is ugly, and the restaurant is also something to decorate.

## The split: kitchens make, guest rooms serve

- Chefs and stations leave the dining room. A **kitchen** is a room of its own that builds dishes on an assembly line.
- The kitchen sends dishes through wall connectors to the **guest rooms** (see [guest-room-design.md](guest-room-design.md)).
- Every room is **7×7**, the size the final graphics will draw. A tile of wall separates rooms, and belt never crosses it.

## Rules

### Wall connectors are fixed

- **Inlets** are the only source of ingredients and the only place a line can start.
  - Tap an inlet to choose what it delivers: any ingredient the kitchen has unlocked, or nothing.
  - Each plate arrives already plated, with a single ingredient on it. There is no empty-plate station.
- **Outlets** are where a line ends. Tap an outlet to switch it between **serving** its room and **clearing** the line (throwing everything away).
  - An outlet never puts anything back on the belt.
- Connectors are scattered over all four walls, and two may share a wall. An inlet never faces an outlet straight across the room, so every line has to turn.
- Rooms deliberately have different counts of inlets and outlets (3/1, 3/2, 4/1, 3/3).

### Belt carries the direction

- Belt flows in the direction it was drawn. Machines have no direction of their own.
- A line may be drawn only out of an inlet, out of a Join's middle, out of a Splitter's end, or on from belt already laid. Nothing starts in the middle of the floor.
- A line runs from a **head** to a **tail**:
  - Heads: an inlet, a Join's middle, a Splitter's end.
  - Tails: an outlet, a Bin, a Join's end, a Splitter's middle.
- A closed loop needs neither. Tapping a loop reverses it.
- A dead end is flagged as a **loose end**, and plates stack up against it.
- A tile with three or four links is a junction. A junction **takes turns** between its ways out without looking at the plate or down the line, and prefers a free tile over an occupied one. **Nothing sorts:** a dish ends up wherever the belt shape takes it.
- Dishes move one tile per tick, one plate per tile. A packed loop still turns.

### Plates are sets; processes are ordered

- A plate holds a **set** of ingredients, so salmon-then-rice and rice-then-salmon are the same nigiri. Each ingredient has a fixed draw order (`z`) so it stacks the same way whichever went on first.
- A **process** (sear, press) marks everything on the plate at that moment. Order matters for processes and nothing else.
- A plate carrying anything no recipe allows, or anything over-processed, is **ruined** and shown clearly. A process cannot be undone.

### Equipment is dumb, the same speed, and covers floor

- Every machine takes the same time over a plate and holds it while it works, so the belt behind it backs up. Faster equipment is a possible later upgrade.
- A machine does its one thing to whatever arrives and passes straight through any plate it has nothing to do to.
- Every machine stands on a belt tile and covers a block of floor. Blocks may not overlap, and that is the whole spacing rule.

The machines:

| Machine | Size | What it does |
|---|---|---|
| **Join** | 3 tiles in a line | Takes a plate in at each end, waits for both, merges them into one plate and hands it on from the middle. Untyped: it merges whatever arrives. |
| **Splitter** | 3 tiles in a line | A Join in reverse: belt runs into its middle and it pushes plates out of its ends strictly alternating, exactly half each. Split three ways and merge two to send ⅔. |
| **Bin** | 1 tile | Ends a line and takes anything off the belt, ruined plates included. |
| **Add-on station** (Wasabi 1 tile, Roe 2 tiles) | — | Adds its ingredient. Add-ons never come from inlets. |
| **Sear** | 2 tiles | Sears everything already on the plate. |
| **Press** | 2×2 | Stands on a corner of its own block, so the only two free faces are at right angles. The belt has to turn through it. |

- Select a machine to **turn** it with the Turn button or **drag** it somewhere else. Belt stays where it was drawn, so moving a machine can leave loose ends.
- Erasing refunds a piece in full.

### Recipes

A dish made of *n* ingredients from inlets needs *n* inlets and *n − 1* Joins in series.

Seared nigiri and Pressed tuna teach the process rule from opposite sides:

- **Seared nigiri** is seared salmon on plain rice. The Sear must stand on the salmon line *before* the Join, because searing the whole nigiri sears the rice too and ruins it. (This was the user's fix to the first version.)
- **Pressed tuna** is pressed rice and tuna, so the Press goes *after* the Join.

The full recipe list, with ingredients, values and unlock stages, is in `balance.js`.

### Progression

- Rooms A to D open over seven stages. Each stage has a dish count to reach and a dish one room asks for, which it pays a bonus for (`wantBonus` 1.6×).
- A room takes whatever its belt brings. A full room backs the line up rather than throwing dishes away.
- Stages, unlock levels (`from`) and prices are all in `balance.js`.

## Rejected or replaced along the way

These ideas were tried in earlier prototypes, which are not kept:

- Waypoints the belt must pass.
- Requests that link a source to a sink.
- Belt heads anywhere on the floor.
- The chef as a pass-through station.
- Filter and traffic-light gates.
- An empty-plate station.
- Fish and egg stations. Base ingredients come only from inlets.
- Ordered plates.
- By-products.
- Terrain such as fountains and trees.
- Surplus-only connectors.
- A chute in front of outlets.
