# Cloudtop Hotel

A standalone Phaser 3 game about building a paper hotel for Bunny, Frog and Cat guests. Open `/prototypes/cloudtop-hotel/` after running `npm run dev` at the repository root. It is also registered on the prototype homepage.

## Play

Spend 100 coins on one of three offers. Purchases append rooms at the open top; earlier floors never change. Adjacent rooms of one type form neighborhoods and earn reusable balloons. The run ends only when no eligible card is affordable, and the completed hotel receives its roof.

The complete card set includes One Room, Prefab Pack, Room Choice, Surprise Parcel, 24 Mosaic sequences, Balloon Call, Copycat, Room Pattern, Master Fold, Lucky Bell, Reserve Delivery, Coupon Book, Neighborhood Streak and Type Lock. Rules and a balance reference are available in the game. Room Choice opens a cancellable picker; Streak and Lock remain visible while active.

- Keys 1 / 2 / 3 buy offers; Escape closes dialogs.
- Reveal now finishes the committed delivery without rerolling.
- Whole hotel toggles between the open top and an overview.
- Sound is opt-in. Reduced motion respects the system setting and can be toggled in game.
- Replay restarts the same seed; New hotel creates a new guestbook.

## Ownership and architecture

This folder owns its gameplay, art, UI, tests and Phaser dependency. Its rule engine began as a copy of the append-only One More Card rules and is now independent: it imports nothing from sibling games. The original game remains playable unchanged.

- `balance.js`: costs, relative offer weights, floor types, strengths, outcome tables and durations.
- `engine.js`: deterministic purchases, append-only floors, neighborhoods, upgrades, streaks and offer locks. Internal `links` and `suit` fields represent floors and room types; player copy uses hotel language.
- `world.js`: Phaser scene, asset loading, camera presentation, paper-pose deliveries, resident animation, balloon flights, Copycat and end-of-run roof. It reads committed state and never decides a payout.
- `main.js`, `index.html`, `style.css`: accessible DOM shop, HUD, room picker, dialogs, mobile/landscape layouts and the engine/scene boundary.
- `assets.js`, `assets/`: stable keys and original local SVG art. Assets stay external in the production build because Phaser's SVG loader expects fetchable URLs, not Vite's inline SVG data encoding.
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
