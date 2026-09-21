# Cloudtop Hotel

A standalone Phaser 3 game about building a paper hotel for Bunny, Frog and Cat guests. Open `/prototypes/cloudtop-hotel/` after running `npm run dev` at the repository root. It is also registered on the prototype homepage.

## Play

Spend 100 coins on one of three offers. Purchases append rooms at the open top; earlier floors never change. Adjacent rooms of one type form neighborhoods and earn reusable balloons. The run ends only when no eligible card is affordable, and the completed hotel receives its roof.

The complete card set includes One Room, Prefab Pack, Room Choice, Surprise Parcel, 24 Mosaic sequences, Balloon Call, Copycat, Room Pattern, Master Fold, Lucky Bell, Reserve Delivery, Coupon Book, Neighborhood Streak and Type Lock. Rules and a balance reference are available in the game. Room Choice opens a cancellable picker; Streak and Lock remain visible while active.

- Keys 1 / 2 / 3 buy offers; Escape closes dialogs.
- Open the paper menu button for sound, motion, Workshop, rules, camera view and restart controls. Escape closes it; game shortcuts are blocked while a menu or dialog is open.
- The menu's Reveal now finishes the committed delivery without rerolling. Whole hotel toggles between the open top and an overview.
- Sound is opt-in. Reduced motion respects the system setting and can be toggled in the menu.
- Replay restarts the same seed; New hotel creates a new guestbook. Workshop and rules return to the menu when closed.

The paper sky fills the viewport behind the HUD, hotel and cards. Nine clouds drift independently while five cottage, windmill and forest islands gently bob and sway. Separate cutouts move over a clean paper-sky texture, keeping the center clear. Motion pauses in place for Reduced motion or a hidden tab, and resumes without resetting. Cards sit in a slanted tray with CSS perspective, slight individual rotations and a raised front lip. The main view keeps counters, the Balloon Dock, current strategy effects and the cards; titles, headings, footer controls and decorative scene text are absent. Portrait and short landscape layouts share the same scene and menu.

## Ownership and architecture

This folder owns its gameplay, art, UI, tests and Phaser dependency. Its rule engine began as a copy of the append-only One More Card rules and is now independent: it imports nothing from sibling games. The original game remains playable unchanged.

- `balance.js`: costs, relative offer weights, floor types, strengths, outcome tables and durations.
- `engine.js`: deterministic purchases, append-only floors, neighborhoods, upgrades, streaks and offer locks. Internal `links` and `suit` fields represent floors and room types; player copy uses hotel language.
- `world.js`: Phaser scene, asset loading, camera presentation, paper-pose deliveries, resident animation, balloon flights, Copycat and end-of-run roof. It reads committed state and never decides a payout.
- `scenery.js`: independent full-viewport scenery, with compositor animations and pause/resume for motion preferences and tab visibility. Its positions are independent of the hotel camera and game state.
- `main.js`, `index.html`, `style.css`: accessible DOM shop, HUD, room picker, dialogs, mobile/landscape layouts and the engine/scene boundary.
- `assets.js`, `assets/sprites/`: five generated Phaser sprite sheets (48 frames), six separate scenery cutouts in one atlas, and a clean paper-sky texture. The manifest registers shared frames for Phaser and DOM card art plus individual scenery bounds. Original PNGs and prompts are preserved; small WebP exports ship to players. See the [sprite-sheet guide](assets/sprites/README.md).
- `audio.js`: optional quiet synthesized paper clicks.
- [`CLOUDTOP_HOTEL_DESIGN.md`](CLOUDTOP_HOTEL_DESIGN.md): story, current mechanics and visual/animation direction, moved here from One More Card.

Phaser is declared in this prototype's package manifest, installed through the root npm workspace. The root provides only shared build, catalog, test and hosting tooling.

## Verify

From the repository root:

```sh
npm test
npm run build
npx playwright test prototypes/cloudtop-hotel/tests/game.spec.js
```

Engine tests cover every card interaction, deterministic runs, money accounting and immutable floor prefixes. Browser checks compare complete played runs to the engine, inspect the Phaser floor count and final roof, exercise Choice/Mosaic/Streak/Lock, verify animated resolution and replay cancellation, and check phone and landscape layouts. Screenshots are saved under `artifacts/cloudtop-hotel/`.

Animation checks also observe all four Copycat poses, its spot–stamp–send–unfold sequence, actual room-unfolding frames, changing idle frames and frozen frames under reduced motion. Scenery checks verify cloud/island movement, transparent assets, manual and system motion preferences, phase-preserving resume, and phone/landscape fit. The detailed style pass changes presentation only; append-only rules and prices stay in the engine and balance table.
