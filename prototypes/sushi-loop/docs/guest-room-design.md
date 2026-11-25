# Guest room design

Status: prototype the user approved on 2026-11-25. Not yet built in Godot.

- Prototype: [`design/guest-room-preview/`](../design/guest-room-preview/). Rules live in `engine.js` and tuning lives in `balance.js`.
- Tests:
  - [`tests/guest-room.test.js`](../tests/guest-room.test.js) covers the engine.
  - [`tests/guest-room-preview.spec.js`](../tests/guest-room-preview.spec.js) covers the browser.
- Live: https://yiochen.github.io/game-prototype/prototypes/sushi-loop/design/guest-room-preview/

## Intent

- The kitchen ([kitchen-line-design.md](kitchen-line-design.md)) is the puzzle. The guest room is **decoration, and where the money is made**.
- Every piece is a plus, so placing one never breaks anything. The choices are which pluses to buy, how coherent the room looks, and how long to keep guests inside.
- The user rejected anything that adds to a dish in the guest room, such as garnish stations or a dome cover. Adding to dishes belongs to the kitchen.

## The room

- The room is 7×7. A fixed belt loop runs out of the kitchen hatch in the west wall and back, like a conveyor-sushi counter. Plates arrive at the kitchen's rate.
- The street door is on the south wall.
- Floor runs round the loop on three sides:
  - a top seat row with an aisle behind it;
  - a bottom seat row with an aisle behind it;
  - a two-tile corridor down the east side joining the two.
- The three tiles inside the loop can't be reached on foot, so only a Sports TV can go there.

## Rules

### Guests walk on the floor

- Guests path tile by tile and never cross the belt or another piece. The only pieces they step onto are the seat or game they're going to or getting up from.
- Placing or moving a piece is refused if guests couldn't walk to it ("Guests could not walk to it there"), or if it would cut off another seat or game ("That would block the way to the Stool").
- A guest whose path is blocked mid-walk finds a new route.
- Known simplification: guests may overlap one another while walking.

### One guest per tile

Each guest takes a whole tile, as in the game. The user chose option B: seats are sized so each chair is one tile, rather than shrinking guests.

| Seat | Footprint | Chairs |
|---|---|---|
| Stool | 1×1 | 1 |
| Bird cage | 1×1 | 1 |
| Glass room | 2×1 | 2 |
| Booth | 2×2 | 4 |

A seat has to touch the belt somewhere.

- **Parties** of 1, 2 or 4 need a seat their size. A party of four can sit only at a booth.

### Traffic, appeal and coherence

- Parties per minute = base + Appeal × perAppeal.
- **Appeal** is the room's total charm multiplied by **coherence**, the share of pieces in the room's main style.
  - The styles are Zen wood, Lantern night and Ocean.
  - A room all in one style gets ×1.4. A mix of three gets about ×0.87.
- Repainting a piece to another style is free.
- **Upgrades** (★ to ★★★) multiply a piece's charm, and seats add a tip to every plate.
- Selling refunds everything spent on a piece.

### Capacity and queue

- Room **capacity** is how many people may be inside at all. It is upgradable.
- Once the room is full, parties queue at the door, up to a limit. They give up when their patience runs out.
- The status line names the current limit: kitchen speed, capacity, seats, or guests.

### Keeping guests longer

Guests arrive wanting 2 or 3 plates. Entertainment tops their appetite back up, so each guest is worth more but holds a place for longer. The top-ups a guest can get in one visit are capped.

- **Pinball:** a full guest gets up, plays a round, comes back hungry and sits at a free chair. They leave if none frees up in time.
- **Sports TV:** at every goal, the whole room wants another plate.
- **Band** (2×2, at most one): each set brings in more guests while it plays and makes everyone seated hungry again.

The engine test confirmed the trade-off. Entertainment lowers how many guests the room serves but raises plates eaten and income.

### Other pieces

- **Arches and tunnels** stand over a belt tile, and plates run underneath. They are pure charm. Their name follows the style: Torii arch, Lantern arch or Wave tunnel.
- **Kitchen speed** (plates per minute) is bought from the dock in this prototype. It stands in for the kitchen line.

## Controls (prototype)

- Pick a piece in the dock, then tap the floor. Valid tiles are shown in green.
- Tap a piece to select it. Drag it to move it.
- The selection bar has Paint, Turn, ★ upgrade and Sell.
- For testing: speed ×1/×4/×16, a +10k cheat, and Reset.
- The save key is `sushi-loop-guest-room-v3`. Add `?fresh` to the URL to ignore the save.
