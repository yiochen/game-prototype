# Deep Salvage

A portrait-first Phaser prototype about building a weapon circuit inside a little submarine. The full product brief and interaction decisions are in [PRD.md](./PRD.md).

From the repository root:

```sh
npm install
npm run dev
```

Open `/prototypes/deep-salvage/`. No account or runtime network request is needed. Nunito is bundled under the SIL Open Font License; see `assets/fonts/OFL.txt`. All world and component art is original procedural/vector artwork owned by this prototype.

## Play

- The submarine travels and fires connected guns automatically. Survive all three waves.
- Tap a fallen part to salvage it. Drag it into the grid to install immediately, or into the parts hold to store it.
- Drag one copy from a stack into an empty cell. Align the floating preview with the destination; placement follows its center, not your finger. Alternatively, tap a stack and then tap an empty cell.
- Tap an installed reactor or mirror to rotate it. Other components work from any side and do not need rotation. Drag it elsewhere or back into the hold.
- Dragging slows time. Invalid drops and cancelled gestures preserve the part. The part being held cannot expire.
- Beam energy crosses empty squares. Mirrors turn it. Amplifiers and lenses work straight through in any direction. Splitters send half the energy left and half right relative to the incoming beam. Guns accept inputs from all four sides.
- A newly acquired part type pauses the game for its introduction. The guide explains all six types. Only discovery history persists between runs.
- Keyboard: Tab to controls, Enter/Space to activate or rotate, arrow keys between grid cells, Delete/Backspace to store a focused tile, Escape to cancel a drag or pause.

Try moving the starter gun to the top-left branch, installing the spare gun on the top-right branch, and placing a splitter above the amplifier with a mirror on each side. Leave empty space between mirrors and guns. Tap the left mirror once to face the correct way.

## Structure

- `balance.js`: numbers, waves, drop order and tuning.
- `engine.js`: deterministic circuit tracing, combat, inventory and loot lifetime; no Phaser or DOM.
- `parts.js`: definitions and shared tile icons.
- `artwork.js`: SVG texture manifest for the submarine and enemies.
- `world.js`: Phaser rendering, parallax ruins, actors and beam effects.
- `main.js`: DOM interface, pointer gestures, dialogs, discovery persistence and simulation boundary.
- `style.css`: responsive console, safe areas, portrait/landscape layout and local font.

## Checks

```sh
npm test
npm run build
npx playwright test prototypes/deep-salvage/tests/game.spec.js
```

Tests capture screenshots in `artifacts/deep-salvage/` (ignored by git). The browser suite covers 412 × 924 and 448 × 1000 portrait, 412 × 820 with browser chrome, 360 × 740, and 924 × 412 landscape, plus a mobile touch context at 3× density. These are browser emulations, not physical-device testing.

Append `?test` to opt into `window.__deepSalvage`, a deterministic fixture API for snapshots, dropping known parts, advancing simulation and arranging a circuit. Ordinary sessions do not expose it. Production and development builds run the same game rules.

No backend, deployment, sound, permanent upgrades or saved active run are included in this prototype.
