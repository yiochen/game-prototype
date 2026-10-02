# Floaty Ferry

A tiny route-management toy. Open `/prototypes/floaty-ferry/`.

The starting idea is transport-network planning. The branch gives each drawn connection its own little ferry, instead of asking players to author long train lines. Ducklings can change boats at any connected island and automatically choose a path with the fewest transfers. A shared budget makes direct routes and useful hubs compete. The coast stays cheerful: a long-waiting duck goes for a swim, and the day continues.

## Play

- Draw from one island to another, or tap two islands. Each connection receives a three-seat ferry that goes back and forth.
- A duck's color and tiny shape badge match its destination's sign. Boats collect suitable passengers in queue order; transfers happen automatically.
- Start with four routes. Eight arrivals earn a fifth ferry, enough to connect all six islands.
- Pink queue rings warn that ducks have waited a while. After 38 seconds waiting on shore, they swim away. Time aboard does not consume patience.
- Edit routes, then tap a connection or its `×` button to free a ferry. Its passengers return to the last shore they departed.
- Each day lasts 100 seconds. Tomorrow shifts the request sequence; replay repeats that day's demand. There is no hard failure state.
- The first visit teaches a drawn route, a second destination, and a passenger actually changing boats. There is no demand timer or expiry during practice. `?` replays it.
- Island buttons provide the same route actions to touch, pointer, and keyboard users. Escape cancels a selected island, then opens pause. Sound is opt-in. Reduced motion stops decorative drift and particles while boats still travel.

Tutorial completion and best delivery count persist locally when available. No backend or active-run resume is needed. Wide layouts rotate the map while keeping island signs, ducks and boats upright.

## Implementation

`balance.js` owns islands, demand, capacity and timing. `engine.js` owns fixed-step voyages, queueing, graph routing, transfers, expiry and progression. `world.js` renders the original vector sea, islands, passengers and boats with Phaser. `main.js` owns drawing, accessible island/route buttons, dialogs, sound and tutorials. The cover is original SVG. Nunito is bundled under the SIL Open Font License in `assets/OFL.txt`.

```sh
node --test prototypes/floaty-ferry/tests/engine.test.js
npm run build
npx playwright test prototypes/floaty-ferry/tests/game.spec.js
```

Engine checks cover tutorial transfers, invalid connections, route budgets, passenger conservation, FIFO boarding, route removal, progression, frame-rate independence and the end of a day. Browser checks exercise drawing, emulated touch cancellation, accessible connections, editing, a complete day, tutorials, keyboard input, pause and responsive layouts. Screenshots are saved to ignored `artifacts/floaty-ferry/`.

`?test` exposes `window.__floatyFerry` for snapshots, time advancement and coordinate mapping, using the ordinary game engine. It is absent from normal sessions.
