# Pollen Club

Tiny bee golf, built for a thumb and a spare minute. Open `/prototypes/pollen-club/`.

The starting idea is miniature golf and billiards. The branch is a living garden: one bee can wake several flowers in a flight, dew is elastic, and a missed shot never erases a bloom. There is no ball to sink, health bar, purchase, or hard failure. Five gardens introduce direct shots, rebounds and crosswinds. Three flights earn the top medal; every completed garden earns at least one flower medal. All five also have a tested one-flight solution for curious players.

## Play

- Drag anywhere in the garden to pull the bee in the opposite direction. Release to fly. The dots use the real collision and wind simulation.
- Touch every sleepy flower. Bounce off dewdrops and the garden edges.
- Call bee returns a flight early. Restart clears this garden. The numbered buds select a garden.
- Arrow Left/Right rotate aim; Up/Down adjust strength; Space launches. The Launch button flies the current aim, initially straight up.
- The first visit offers two playable lessons: wake a flower, then bounce off a dewdrop. Lessons are replayable from `?`.
- `?` pauses. A hidden tab also pauses. Sound is opt-in. Reduced motion disables decorative drift and particles while preserving the flight and aiming cues.

Tutorial completion and best medals are stored locally when storage is available. No active-run resume or backend is needed. The interface is portrait first; wide views rotate the garden layout while keeping the characters upright.

## Implementation

`balance.js` owns geometry, wind, physics constants and par. `engine.js` owns fixed-step motion, collision, bloom collection and medals, independently of Phaser. `world.js` renders original procedural vector art and disposable effects. `main.js` owns gestures, keyboard controls, tutorials, dialogs and optional synthesized sound. Each game owns its CSS and assets. The bundled Nunito font is licensed under the SIL Open Font License in `assets/OFL.txt`; the cover is original SVG artwork.

```sh
node --test prototypes/pollen-club/tests/engine.test.js
npm run build
npx playwright test prototypes/pollen-club/tests/game.spec.js
```

Engine checks cover lesson feasibility, frame-rate independence, trajectory accuracy, retry behavior, duplicate inputs, and all garden solutions. Browser checks exercise real pointer and emulated touch gestures, tutorial completion, all five results, keyboard input, pause, storage, and phone/landscape layouts. Screenshots are saved to ignored `artifacts/pollen-club/`.

`?test` exposes `window.__pollenClub` for snapshots, time advancement and coordinate mapping. It is absent from ordinary sessions; it uses the same engine and renderer as normal play.
