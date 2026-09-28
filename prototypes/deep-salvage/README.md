# Deep Salvage

A portrait-first Phaser prototype about building a weapon circuit inside a little submarine. The full product brief and interaction decisions are in [PRD.md](./PRD.md).

From the repository root:

```sh
npm install
npm run dev
```

Open `/prototypes/deep-salvage/`. No account or runtime network request is needed. Nunito is bundled under the SIL Open Font License; see `assets/fonts/OFL.txt`. All world and component art is original procedural/vector artwork owned by this prototype.

## Play

- Choose Sunken City, Kelp Wilds or Cinder Foundry before diving. Each route has its own scenery, path, depth and three enemy waves. Pause or finish a dive to choose another route; restarting keeps the current map.
- The submarine travels and fires connected guns automatically. Survive all three waves.
- Tap a fallen part to salvage it. Drag it into the grid to install immediately, or into the parts hold to store it.
- Use the tray arrows to find a stored part. Drag one copy from a stack into an empty cell. Align the floating preview with the destination; placement follows its center, not your finger. Alternatively, tap a stack and then tap an empty cell.
- Tap an installed reactor or mirror to rotate it. Other components work from any side and do not need rotation. Drag it elsewhere or back into the hold.
- Dragging slows time. Invalid drops and cancelled gestures preserve the part. The part being held cannot expire.
- Beam energy crosses empty squares. Mirrors turn it. Amplifiers and lenses work straight through in any direction. Splitters send half the energy left and half right relative to the incoming beam. Guns accept inputs from all four sides.
- Lasers track enemies continuously for small damage ticks. The spare Pulse gun in your hold stores 36 energy and fires a 54-damage burst. Stronger input charges it faster; lenses add piercing. Charge waits when full or disconnected, pauses with the dive, and clears when returned to the hold. Forge a laser gun + reactor for another Pulse gun (24 cash / 6 seconds).
- Shield terminals store 32 energy to restore 12 shield, even while taking fire. Medic terminals store 48 energy to restore 12 hull HP. Both hold full charge until needed, accept every input side, and share the Pulse gun’s charge rules. Amplifiers charge them faster; lenses do not multiply healing. Each dive includes one of each and a spare reactor. Forge two Shields into Aegis or two Medics into a Repair bay for 20 restoration per charge.
- Ten enemy roles include fast darts, armored bulwarks, long-range snipers, shield-draining leeches, allied-healing menders and explosive bombers. The field guide lists strengths, counters and stats. Destroy bombers before they reach you: their self-destruction deals damage without cash or kill credit.
- Every kill pays cash; only one in four drops a part. The lower panel is one 7 × 7 surface: a 6 × 6 weapon lab, six forge cells down the right, and a full-width storage row along the bottom. The row has five fixed stack slots and two paging arrows. Slots never scroll or shift when a stack runs out.
- Drag any part from the hold, battlefield or lab into an empty forge cell. Matching recipe ingredients glow, but unrelated parts are also welcome. A complete affordable recipe starts automatically and pays once. Only its ingredients lock; other slots remain usable. Unrelated ingredients stay when the finished upgrade returns to the hold. Tap an unlocked ingredient to recover it. If cash is short, forging waits until you earn enough. Queued recipes start after the current job completes.
- No headings, explanatory text, forge button or power readouts occupy the lower panel. Instructions, part names, recipe costs and durations are in the guide. Charge bars and forge progress remain visual; accessible names describe controls and charge state.
- Thicker beams carry more power, gold means amplified, and blue dashes mean piercing. Charged terminals show a fill bar and glow when ready. Forged parts have distinct enhanced icons and tier badges. The blue shield meter regenerates after six seconds without damage.
- A newly acquired part type pauses the game for its introduction. The guide explains all 20 parts and thirteen forge recipes, plus enemies and maps, including exact quantities, effects, costs and times from the start. Only discovery history persists between runs.
- Keyboard: Tab to controls, Enter/Space to activate or rotate, arrow keys between grid cells, Delete/Backspace to store a focused tile, Escape to cancel a drag or pause.

Try forging your two spare amplifiers into an Overcharger first, then install it above the starter amplifier. Add the first salvaged lens before your gun to handle armor.

For a support circuit, place the spare reactor in the bottom-left cell and Shield or Medic above it. For the Foundry, forge the installed laser and spare laser into a Heavy laser during the first refit interval, then reinstall it before the next wave.

For branching, try moving the starter gun to the top-left branch, installing the spare gun on the top-right branch, and placing a splitter above the amplifier with a mirror on each side. Leave empty space between mirrors and guns. Tap the left mirror once to face the correct way.

## Structure

- `balance.js`: numbers, waves, drop order and tuning.
- `recipes.js`: ingredient combinations, costs, durations and outputs.
- `engine.js`: deterministic circuit tracing, combat, forge jobs, inventory and loot lifetime; no Phaser or DOM.
- `parts.js`: definitions and shared tile icons.
- `artwork.js`: SVG texture manifest for the submarine and ten enemy silhouettes.
- `environments.js`: procedural kelp forest and foundry scenery.
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

No backend, sound, permanent upgrades or saved active run are included in this prototype.
