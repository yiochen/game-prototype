# Recipe acquisition: submarine runner candidate

Status: the expedition grilling session has resumed. Current accepted direction and new interview decisions are recorded in [expedition-design-interview.md](./expedition-design-interview.md). Older proposals below are exploratory unless explicitly accepted. The restaurant core checkpoint remains separate.

## User proposal

- A separate submarine-diving game inspired by the interaction of Subway Surfers.
- The submarine advances automatically. Upward travel is the latest direction, replacing literal downward movement to improve visibility around the player's hands.
- Freeform lateral drag steering is the latest input direction.
- Occasional power-ups improve the shell or provide fast-forward movement.
- Catch a new creature species by harpooning and following it to unlock its restaurant recipe. This supersedes the earlier collect-a-set proposal.

This replaces belt-combat reuse as the current direction of exploration. The acquisition interaction can stand alone; it does not need to reuse the restaurant floor or chef behavior.

## Latest control direction

The latest user direction replaces the three-button acceleration proposal with a full-screen ocean-bed scene. The player can touch anywhere in the playfield and drag left or right to steer freely. Direct relative drag steering is accepted: drag moves the submarine sideways, release stops its own sideways motion while forward travel continues, and touching again does not snap it to the finger. There are no discrete lanes or dedicated control footer. Destructive firing remains deferred. The later creature-capture design introduces shooting a harpoon; its input is under discussion. Sensitivity, smoothing, environmental forces, and camera framing remain to be tested.

The upward-travel presentation is an overhead view of the submarine moving forward along the ocean bed, into a descending canyon. The user accepted this visual explanation after reviewing the generated mockup. The control deck in that image is now superseded by the full-screen scene and drag input.

## Expedition rewards and visibility

- Do not preview rewards or ask the player to choose a target recipe before departure. The player goes on an expedition without knowing what rewards they will discover.
- Salvage is the normal reward, including expeditions that yield no recipe. It replaces the earlier shared-cash idea.
- Recipe discoveries provide an additional reward; the earlier choose-a-target-recipe recommendation is rejected.
- Upward screen travel keeps incoming encounters above the submarine, away from the player's usual touch area. The scene now fills the screen without a dedicated control deck.
- The latest accepted acquisition design guarantees one previously uncaught creature species per expedition while any remain in a finite catalog. Harpooning and following it to complete the catch earns its recipe. Reward previews remain absent; capture itself is not guaranteed. After catalog completion, expeditions remain available for salvage.

## Earlier candidate design to discuss

The following are recommendations, not accepted rules:

- The earlier literal downward camera proposal is superseded. For upward travel, place the submarine in the lower portion of the playfield and scroll terrain downward; exact framing remains to be tested.
- Three-lane steering and the later three-button acceleration/fire proposal are both superseded by freeform drag steering.
- Put discovered collectibles behind meaningful obstacle/risk choices.
- A shield absorbs a collision; a temporary boost crosses a difficult section quickly with collision protection.
- Restaurant cash buying submarine improvements was an earlier recommendation. The user accepted separate expedition and restaurant currencies instead.
- The earlier component-set candidate is superseded by creature capture. Failed runs retain earned recipes and collected salvage; unfinished pursuits are not completed catches.
- Catching a new species unlocks its recipe restaurant-wide; chef quality requirements still govern who can prepare it.

## Accepted economy separation

The user accepted separate currencies to prevent earnings in one mode from overwhelming the economy of the other. Expedition salvage funds submarine upgrades; restaurant coins fund restaurant progression. Recipes connect the two economies. Currency exchange is omitted from this direction.

Restaurant coins fund chefs, chef levels, layout purchases, and expansion, with expedition salvage funding submarine improvements. This revises the earlier direct restaurant-income-to-submarine-upgrades proposal. Balance should examine whether manual expedition play becomes a required bottleneck for the idle game and whether either mode runs out of useful spending options.

## Open questions

Exact camera framing, steering sensitivity and smoothing, encounter mechanics, power-ups, harpoon input and aiming, pursuit and escape rules, repeated-species rewards, catalog exhaustion, run duration, and depth progression remain unresolved. The latest direction is upward travel along the ocean bed, full-screen direct relative drag steering, harpoon-and-pursuit creature capture, unknown rewards before departure, and salvage even without catching a new species. Finite varied journeys, hull damage, retention of earned rewards on failure, and an extraction salvage bonus are accepted; see the interview record. Do not replace the core restaurant rules with this acquisition-mode brainstorm.
