# Cloudtop Hotel

A standalone Phaser 3 game about building a paper hotel for Bunny, Frog and Cat guests. Open `/prototypes/cloudtop-hotel/` after running `npm run dev` at the repository root. It is also registered on the prototype homepage.

## Play

Spend 100 coins on one of three offers. Purchases append rooms at the open top; earlier floors never change. Adjacent rooms of one type form neighborhoods and earn reusable balloons. The run ends only when no eligible card is affordable, and the completed hotel receives its roof.

The complete card set includes One Room, Prefab Pack, Room Choice, Surprise Parcel, 24 Mosaic sequences, Balloon Call, Copycat, Room Pattern, Master Fold, Lucky Bell, Reserve Delivery, Coupon Book, Neighborhood Streak and Type Lock. Rules and a balance reference are available in the game. Room Choice opens a cancellable picker; Streak and Lock remain visible while active.

- Keys 1 / 2 / 3 buy offers; Escape closes dialogs.
- Each card shows its coin cost at the top left and a question-mark button at the top right. The question mark opens an effect dialog without buying the card; descriptions and projected coin balances do not fill the card face.
- Open the paper menu button for sound, motion, Workshop, rules, camera view and restart controls. Escape closes it; game shortcuts are blocked while a menu or dialog is open.
- The menu's Reveal now completes a selected card and its delivery once, without rerolling. Whole hotel toggles between the open top and an overview that fits the roof and island in the unobscured area.
- Sound is opt-in. Reduced motion respects the system setting and can be toggled in the menu.
- Replay restarts the same seed; New hotel creates a new guestbook. Workshop and rules return to the menu when closed.

The paper sky and transparent Phaser canvas fill the viewport behind the HUD and foreground tray, so the hotel continues behind the cards instead of ending at a separate playfield edge. Nine clouds drift independently while five cottage, windmill and forest islands gently bob and sway. Separate cutouts move over a clean paper-sky texture, keeping the center clear. Motion pauses in place for Reduced motion or a hidden tab, and resumes without resetting.

The HUD uses generated warm ivory paper tabs: a coin icon and balance, overlapping animal balloons with ×N counts, and a pink heart beside the hotel height. The heart presents the existing floor total, not a lives mechanic; its accessible label remains “Floors.” The Balloon Dock title is a generated torn-paper banner. There are no visible “Coins” or “Floors” labels.

Cards lie on a shared perspective plane inside the textured cardboard tray. The tray preserves its native 3:1 aspect ratio and scales uniformly within the available space, filling the width on phones and capping at 1200 pixels on larger screens. Generated card faces combine fibrous ivory centers with folded colored paper borders; contact shadows and a front rim overlapping their lower edges seat them in the box. Short or wide landscape layouts place the tray beside the hotel. Each power has a distinct illustration: Room Patterns use blueprints, Type Locks show locked future cards, and other powers have their own miniature dioramas. Room packs, Balloon Calls and Mosaic compose the room/balloon sprites to show quantities and order. The main view keeps only counters, the Balloon Dock, current strategy effects and the cards; titles, headings, footer controls and decorative scene text are absent.

A selected card lifts from its actual projected position in the tray and flies to the screen center over 470 ms, inflates for 220 ms and pops. Payment and the engine effect happen once at the burst, then the room delivery plays while fragments of the selected artwork scatter for up to 420 ms. Resetting before the pop cancels the pending purchase. Reveal now or enabling Reduced motion finishes it once; Reduced motion skips the flight and delivery from the start. Additional purchases are blocked throughout the sequence.

## Ownership and architecture

This folder owns its gameplay, art, UI, tests and Phaser dependency. Its rule engine began as a copy of the append-only One More Card rules and is now independent: it imports nothing from sibling games. The original game remains playable unchanged.

- `balance.js`: costs, relative offer weights, floor types, strengths, outcome tables and durations.
- `engine.js`: deterministic purchases, append-only floors, neighborhoods, upgrades, streaks and offer locks. Internal `links` and `suit` fields represent floors and room types; player copy uses hotel language.
- `world.js`: Phaser scene, asset loading, camera presentation, paper-pose deliveries, resident animation, balloon flights, Copycat and end-of-run roof. It reads committed state and never decides a payout.
- `card-flight.js`, `card-flight.css`: the selected card's flight, inflation and paper burst; one guarded callback applies the purchase at the pop, with explicit finish/cancel handling.
- `scenery.js`: independent full-viewport scenery, with compositor animations and pause/resume for motion preferences and tab visibility. Its positions are independent of the hotel camera and game state.
- `main.js`, `index.html`, `style.css`: accessible DOM shop, HUD, room picker, dialogs, mobile/landscape layouts and the engine/scene boundary.
- `card-table.css`, `paper-hud.css`: shared card-plane perspective, textured card faces, front-rim layering and the paper-tab HUD.
- `assets.js`, `assets/sprites/`: seven generated game/UI sheets plus one scenery atlas, totaling 68 sprite frames: 48 room/actor/prop frames, 14 card illustrations and six scenery cutouts. A separate six-frame atlas provides blank paper card faces; single-image assets provide the paper sky, cardboard tray, torn Dock banner and blank HUD tab. The manifest registers shared frames for Phaser and DOM card art plus individual scenery bounds. Original PNGs and prompts are preserved; WebP exports ship to players. See the [sprite-sheet guide](assets/sprites/README.md).
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

Animation checks also observe all four Copycat poses, its spot–stamp–send–unfold sequence, actual room-unfolding frames, changing idle frames and frozen frames under reduced motion. Card checks cover effect-help dialogs, distinct artwork, the full-screen canvas and the flight/inflate/burst purchase boundary. Scenery checks verify cloud/island movement, transparent assets, manual and system motion preferences, phase-preserving resume, and phone/landscape fit. The detailed style pass changes presentation and when a selected purchase commits; append-only rules and prices stay in the engine and balance table.
