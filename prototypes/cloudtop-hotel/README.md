# Cloudtop Hotel

A standalone Phaser 3 game about building a paper hotel for Bunny, Frog and Cat guests. Open `/prototypes/cloudtop-hotel/` after running `npm run dev` at the repository root. It is also registered on the prototype homepage.

## Play

Spend 100 coins on one of three offers. Purchases append rooms at the open top; earlier floors never change. Adjacent rooms of one type form neighborhoods and earn reusable balloons. When no paid card is affordable, the tray offers a single free Roof card. Select it to drop the roof onto the tower and finish the game. The roof changes no coins, floors, upgrades or purchase history.

The complete card set includes One Room, Prefab Pack, Room Choice, Surprise Parcel, 24 Mosaic sequences, Balloon Call, Copycat, Room Pattern, Master Fold, Lucky Bell, Reserve Delivery, Coupon Book, Neighborhood Streak and Type Lock. Rules and a balance reference are available in the game. Room Choice opens a cancellable picker; Streak and Lock remain visible while active.

- Keys 1 / 2 / 3 buy offers; Escape closes dialogs.
- Each card shows its coin cost at the top left and a question-mark button at the top right. The question mark opens an effect dialog without buying the card. Its purchase button buys that exact offer, or opens the cancellable room picker for Room Choice. Descriptions and projected coin balances do not fill the card face.
- Open the paper menu button for sound, motion, Workshop, rules, camera view and restart controls. Escape closes it; game shortcuts are blocked while a menu or dialog is open.
- The menu's Reveal now completes a selected card and its delivery once, without rerolling. Whole hotel is also available beside the persistent upgrade badges. It smoothly toggles between the open top and an overview that fits the roof and island in the unobscured area. Tap a badge to inspect the Workshop; tap the floor or balloon counters for an explanation.
- Sound is opt-in. Reduced motion respects the system setting and can be toggled in the menu.
- Replay restarts the same seed; New hotel creates a new guestbook. Both are directly available on the final score. Workshop and rules return to the menu when opened from there; a Workshop opened from a badge returns to the hotel.

The paper sky and transparent Phaser canvas fill the viewport behind the HUD and foreground tray, so the hotel continues behind the cards instead of ending at a separate playfield edge. Nine clouds drift independently while five cottage, windmill and forest islands gently bob and sway. Separate cutouts move over a clean paper-sky texture, keeping the center clear. Motion pauses in place for Reduced motion or a hidden tab, and resumes without resetting.

The HUD uses generated warm ivory paper tabs: a coin icon and balance, overlapping animal balloons with ×N counts, and a small paper-building icon beside the hotel height; its accessible label remains “Floors.” There is no Balloon Dock title or visible “Coins” or “Floors” label.

Cards lie on a shared perspective plane inside the textured cardboard tray. The tray preserves its native 3:1 aspect ratio and scales uniformly within the available space, filling the width on phones and capping at 1200 pixels on larger screens. Generated card faces combine fibrous ivory centers with folded colored paper borders; contact shadows and a front rim overlapping only their blank lower edges seat them in the box. The cards stand more upright on phones, with values above the rim, subtle press feedback and a lift on desktop hover. Disabled faces stay opaque so the decorative cards cannot show through them. Three decorative cards with parcel placeholder art sit beneath each playable offer. They remain in place as the selected card lifts, do not accept input, and do not predict future offers. Short or wide landscape layouts place the tray beside the hotel. Each power has a distinct illustration: Room Patterns use blueprints, Type Locks show locked future cards, and other powers have their own miniature dioramas. Room packs, Balloon Calls and Mosaic compose the room/balloon sprites to show quantities and order. The main view keeps counters, the Balloon Dock, upgrade badges, a camera toggle, current strategy effects and the cards; titles, headings, footer controls and decorative scene text are absent.

A selected card lifts from its actual projected position in the tray and flies to the screen center over 300 ms, inflates for 110 ms and pops. Payment and the engine effect happen once at the burst, then room delivery starts from that same screen position while fragments of the selected artwork scatter for up to 420 ms. Resetting before the pop cancels the pending purchase. Reveal now or enabling Reduced motion finishes it once; Reduced motion skips the flight and delivery from the start. Additional purchases are blocked throughout the sequence. The free roof card uses the same flight and pop, followed by a 740 ms roof fall and 360 ms settling bounce. Completion and confetti wait for landing. Reveal now or Reduced motion finishes the roof once; replay cancels both a pending roof card and an active drop. The roof lands in close-up. After landing, the tray disappears, a compact score and replay controls appear, and the camera smoothly pulls back to show the hotel in the newly available space. Reduced motion settles the camera immediately.

Ordinary delivery timing is shorter than surprise and Copycat sequences. Room and camera transforms update on each render frame while character poses retain their paper-animation cadence; idle scenes redraw at 12 fps. Reusable image, text and graphics pools avoid rebuilding Phaser objects every frame. Floors settle gently after unfolding, balloon counters pulse when the delivery completes, and a short receipt explains upgrade bonuses, streaks and expired effects. Upgrades fly toward the tools row and remain visible as badges. Coins show the payment and any refund. New offers enter with a short stagger. Replay and reduced motion cancel transient feedback without changing committed purchases.

## Lobby and guestbook

The welcome screen introduces the paper hotel with a sign, a miniature hotel that assembles from the island upward, drifting guest balloons, and staggered play / resume / guestbook controls. The guestbook opens like a paper page; its heading, tabs, submission form, empty states and ranked rows have coordinated entrances. All entrances settle immediately with reduced motion, and keyboard focus follows screen changes. Returning to the lobby pauses access to game controls. Sound and motion preferences persist locally; a changed system motion preference is respected immediately.

Purchases save the seed and card choices locally. Continue your stay reconstructs the unfinished run, including a pending roof, without rerolling. Finished hotels are saved in **Your hotels** (best 50 on this device). From the completion panel or an unshared personal entry, choose a public nickname and sign the shared **Everyone** leaderboard. Failed submissions can be retried; private browsing still permits play even when storage is unavailable.

The shared leaderboard ranks the top 100 by floors, neighborhoods, then coins saved. Earlier submissions break exact ties. The Netlify function at `/api/cloudtop-hotel/leaderboard` replays every purchase using the same deterministic engine and derives the score server-side. It checks the schema, name, size, origin and score version; identical replays occupy one place. Strongly consistent conditional Blobs writes retry concurrent submissions. Netlify limits requests to 30 per minute per IP/domain. This is an anonymous prototype guestbook: deterministic replay validates a legal run but does not prove a human played it.

Production scores persist across deployments in a site-wide Netlify Blobs store. Each deploy preview has its own disposable store, so preview scores never reach production. Bump `SCORE_VERSION` when changing balance or replay rules. No external database or credentials are required on Netlify. `npm run dev` serves the game and personal history; use `npx netlify dev` for the shared function locally. A plain Vite preview truthfully shows the shared leaderboard as unavailable.

## Shared origami UI

The paper world uses complementary materials: illustrated colored card stock and layered deck backs, cut-paper HUD labels, printed guestbook rows and circular seals. Larger surfaces—the Cloudtop title, guestbook sheet, score form, six dialogs, purchase receipt and finale—use real CSS nine-slice borders, as do prominent action buttons. Their folded corners stay a fixed size as panels resize. Utility controls keep their lighter treatment. See [the material guide](assets/ui/README.md) for the source, slice dimensions and generation prompt.

Large sheets unfold as two hinged halves with separate lighting and a brief settle; text appears after opening begins without stretching. Prominent buttons use a shorter fold, book rows fade in, and cards retain their quick staggered deal-and-settle entrance. Popups cleanly cancel on close, screen transitions clear old folds, and reduced motion shows the settled surface immediately. Card delivery still commits once.

## Neighborhood balloons

A new neighborhood releases one balloon from its own top-floor window after
the rooms settle. It opens for 420 ms, hovers on a short tether for 380 ms,
then follows a gently swaying curve to its matching dock over 1,680 ms.
Multiple neighborhoods release 220 ms apart; extending an existing neighborhood
does not release another balloon. The camera briefly frames all launch floors
when a delivery creates several neighborhoods.

The dock count increments on arrival and its balloon gives a small settling
bounce. Flight targets come from the actual dock icon; both endpoints follow
live camera and viewport layout. Reveal now and reduced motion immediately
settle the delivery, while replay cancels pending arrivals. All travel and dock
feedback are presentation only; the deterministic score and purchase rules
are unchanged. `balloon-journey.js` owns the choreography and path sampling.

## Ownership and architecture

This folder owns its gameplay, art, UI, tests and Phaser dependency. Its rule engine began as a copy of the append-only One More Card rules and is now independent: it imports nothing from sibling games. The original game remains playable unchanged.

- `balance.js`: costs, relative offer weights, floor types, strengths, outcome tables and durations.
- `engine.js`: deterministic purchases, append-only floors, neighborhoods, upgrades, streaks and offer locks. Internal `links` and `suit` fields represent floors and room types; player copy uses hotel language.
- `world.js`: Phaser scene, asset loading, camera presentation, paper-pose deliveries, resident animation, balloon flights, Copycat and end-of-run roof. It reads committed state and never decides a payout.
- `card-flight.js`, `card-flight.css`: the selected card's flight, inflation and paper burst; one guarded callback applies the purchase at the pop, with explicit finish/cancel handling.
- `scenery.js`: independent full-viewport scenery, with compositor animations and pause/resume for motion preferences and tab visibility. Its positions are independent of the hotel camera and game state.
- `main.js`, `index.html`, `style.css`: accessible DOM shop, HUD, room picker, dialogs, mobile/landscape layouts and the engine/scene boundary.
- `feedback.js`, `polish.css`: cancellable purchase feedback, upgrade badges, responsive card readability and compact finale presentation.
- `card-table.css`, `paper-hud.css`: shared card-plane perspective, textured card faces, front-rim layering and the paper-tab HUD.
- `assets.js`, `assets/sprites/`: seven generated game/UI sheets plus one scenery atlas, totaling 68 sprite frames: 48 room/actor/prop frames, 14 card illustrations and six scenery cutouts. A separate six-frame atlas provides blank paper card faces; single-image assets provide the paper sky, cardboard tray and blank HUD tab; the removed Dock banner remains as unused source art. The manifest registers shared frames for Phaser and DOM card art plus individual scenery bounds. Original PNGs and prompts are preserved; WebP exports ship to players. See the [sprite-sheet guide](assets/sprites/README.md).
- `paper-ui.js`, `paper-ui.css`, `assets/ui/`: shared nine-slice surfaces, tint palette, folding leaves and lifecycle cleanup.
- `lobby.js`, `lobby.css`: welcome screen, guestbook, network states and entrance choreography.
- `guestbook-storage.js`, `score-rules.js`: local saves, deterministic resume, versioned scoring and validation.
- `leaderboard-service.js`, `functions/cloudtop-leaderboard.mts`: testable leaderboard handler and Netlify Blobs adapter.
- `audio.js`: optional quiet synthesized paper clicks.
- [`CLOUDTOP_HOTEL_DESIGN.md`](CLOUDTOP_HOTEL_DESIGN.md): story, current mechanics and visual/animation direction, moved here from One More Card.

Phaser is declared in this prototype's package manifest, installed through the root npm workspace. The root provides only shared build, catalog, test and hosting tooling.

## Verify

From the repository root:

```sh
npm test
npm run build
npx playwright test prototypes/cloudtop-hotel/tests/
```

Engine tests cover every card interaction, deterministic runs, money accounting and immutable floor prefixes. Browser checks compare complete played runs to the engine, inspect the Phaser floor count and final roof, exercise Choice/Mosaic/Streak/Lock, verify animated resolution and replay cancellation, and check phone and landscape layouts. Screenshots are saved under `artifacts/cloudtop-hotel/`.

Animation checks also observe all four Copycat poses, its spot–stamp–send–unfold sequence, actual room-unfolding frames, changing idle frames and frozen frames under reduced motion. Card checks cover effect-help dialogs, distinct artwork, the full-screen canvas and the flight/inflate/burst purchase boundary. Scenery checks verify cloud/island movement, transparent assets, manual and system motion preferences, phase-preserving resume, and phone/landscape fit. The detailed style pass changes presentation and when a selected purchase commits; append-only rules and prices stay in the engine and balance table.
