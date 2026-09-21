# Cloudtop Hotel — Story and Animation Direction

Status: playable Phaser prototype and continuing story/animation direction. Gameplay below reflects the current append-only card set; visual details describe both the implemented foundation and the target polish. Names for individual cards are working names unless marked as a core term. Prices and strengths are a snapshot of [`balance.js`](balance.js); [`engine.js`](engine.js) is the implemented rules reference.

## Prototype implementation

The playable Phaser implementation now lives in this folder, independently of One More Card. The homepage registers it as Cloudtop Hotel. See [README.md](README.md) for local play, ownership and verification.

The prototype implements the full current card set with hotel terminology, append-only floor rules, exact Mosaic order, Room Choice, Neighborhood Streak and Type Lock. The September 2026 art revision follows the supplied colorful paper-diorama references: a textured blue sky, floating islands, flower-filled windows, gold lanterns and dimensional folded-paper animals. Phaser uses five generated sprite sheets with 48 frames: 24 room frames, 16 Copycat/balloon frames and eight scenery/prop frames. Each room type has folded, opening and assembled poses plus blinking, reading, waving and sleeping guests. Copycat plays spot, stamp, send and celebration poses; balloon frame animation, paper unfolding, camera follow, confetti and the final roof complete the presentation. The DOM provides the accessible shop, Balloon Dock, persistent strategy indicators, rules and Workshop. Reveal now, replay cancellation, reduced motion and optional sound are supported.

Original generated PNG sheets, WebP delivery exports, frame maps and the exact generation prompts live in [assets/sprites](assets/sprites/README.md). The three windows across a rendered floor are decorative: one complete row remains one floor and one scoring unit. Guest idle poses never change a floor's type, order or identity.

The sections below remain the visual direction for continued polish: detailed actor choreography, contact haptics and richer sound design can build on the playable implementation. The acceptance checklist describes the target presentation; automated coverage is listed in the README.


## Product fantasy

Cloudtop Hotel is a cozy, cartoony drafting game about unfolding an impossibly tall hotel in the sky. Every purchased room arrives as a compact origami box, lands on the open construction platform, and unfolds into a new floor. Matching consecutive floors form a neighborhood. Each new neighborhood sends a hot-air balloon to the Balloon Dock, where it becomes a visible, permanent record of that neighborhood.

The player should feel like an innkeeper, paper engineer, and stop-motion director at the same time. The strategy can be numerical underneath, but every number must have a physical cause the player can see: boxes become floors, neighborhoods launch balloons, balloons deliver more boxes, and Copycat stamps existing designs onto blank paper.

## Background story

### Short pitch

High above Patchwork Valley, migrating animals travel between floating islands in tiny hot-air balloons. The old Cloudtop Hotel opens for one night during the annual Sky Parade, but this year more guests are arriving than the hotel has rooms.

The player is the hotel's new innkeeper. With a pouch of coins, a box of enchanted folding paper, and help from the hotel's guests, they must build upward before nightfall. Bunny, Frog, and Cat guests each prefer their own style of room. When matching rooms touch, they form a neighborhood. Every new neighborhood launches a delivery balloon, and the growing balloon fleet can bring even more folded rooms from the clouds.

Copycat is a mysterious traveling cat who can remember any room after seeing it once. With a spyglass, tracing paper, and a large paw-shaped stamp, Copycat can reproduce part of the hotel's largest neighborhood at the top of the tower.

When the player can afford no more cards, construction ends. A final sheet of paper descends and folds into the hotel's roof. The camera pulls back to reveal the completed hotel, its residents fill the windows, and its height determines how many sky travelers found a home that night.

### Tone

- Cozy rather than urgent.
- Playful physical comedy rather than elaborate magic lore.
- Handmade and imperfect rather than glossy or technologically precise.
- The player never fails a guest; a short tower is a modest hotel, while a tall tower is a joyful achievement.

## Core language

These terms should be used consistently in rules, card copy, UI, animation notes, and implementation.

| Term | Meaning |
| --- | --- |
| **Floor** | One physical origami room module and one scoring unit. This replaces “link.” |
| **Floor type** | Bunny/Pink, Frog/Green, or Cat/Orange. This replaces “suit.” |
| **Neighborhood** | One maximal consecutive run of floors of the same type. This replaces “segment.” |
| **Open top** | The only place where new floors may be added during a run. Existing floors never move or receive insertions. |
| **Prefab box** | The compact folded state that transforms into a floor. |
| **Neighborhood balloon** | One balloon earned when a new neighborhood begins. |
| **Balloon Dock** | Persistent HUD counters recording the exact number of neighborhood balloons of each type. |
| **Copycat** | The white-and-lavender traveling cat who copies part of the largest neighborhood. |
| **Construction platform** | The flat, unfinished paper surface at the open top where boxes land and unfold. It is not a roof. |
| **Roof** | The final cap added only after the run ends. It never appears during active play. |

### Immutable construction rule

All effects may inspect the completed tower, but every newly created floor is appended at the open top. No effect inserts, replaces, recolors, or removes an existing floor.

### Snapshot rule

Every power calculates its sources and output before it creates new floors. A balloon earned by the resulting floors appears after the delivery and cannot contribute to the same action.

## Current card set

Prototype names identify implemented cards; hotel names describe their intended presentation. Every output goes to the open top. Power purchases have no incidental floor, but a suited power purchase can earn Foundation bonus floors.

| Prototype card | Hotel presentation | Current price | Rule |
| --- | --- | --- | --- |
| Fixed 1 | One Room | $3 | Append 1 floor of its printed type, plus applicable bonuses. |
| Fixed 3 | Prefab Pack | $6 | Append 3 floors of its printed type, plus applicable bonuses. |
| Choice 1 | Choice 1; working name | $4 | Choose the type before payment; append 1 floor plus that type's applicable bonuses. |
| Mystery | Surprise Parcel | $6 | One draw: 1 / 3 / 8 floors at baseline odds of 60% / 30% / 10%, then applicable bonuses. |
| Mosaic | Mosaic Trio / Sandwich / Pair | $6 | Append the exact printed three-floor pattern; 24 possible sequences. |
| Recall | Balloon Call | $7 | Append 1 matching floor per existing matching neighborhood, regardless of neighborhood length. |
| Overgrow | Copycat | $5 | Append the largest neighborhood's type: half its length, rounded down, minimum 1 and maximum 8. Earliest neighborhood wins ties. |
| Suit Reactor | Room Pattern | $6 / $8 / $10 per level | Future base builds of its type gain +1 / +2 / +3 floors. Includes Choice 1 and Mystery; excludes Mosaic. |
| Assembler | Master Fold | $9 / $12 / $15 per level | Future Fixed 1, Fixed 3 and Choice 1 builds gain +1 / +2 / +3 floors. Stacks with Room Pattern. |
| Stabilizer | Lucky Bell | $7 / $9 / $11 per level | Improves Surprise Parcel odds; the chance of 8 floors becomes 19% / 27.1% / 34.39%. |
| Vault | Reserve Delivery | $8 | Append 1 floor per $10 left after payment, rounded down. Use the current top type, or the configured opening type on an empty tower. |
| Rebate | Coupon Book | $5 | Refund $2 on each of the next 3 base purchases, including Choice 1 and Mosaic. |
| Foundation | Neighborhood Streak | $7 | Next suited purchase gains +1; each subsequent same-type purchase gains +2, +3… A different type or Mosaic ends it. |
| Attunement | Type Lock | $6 | Lock suited offers to its printed type for the next 3 shops. |

Reactor levels replace their previous strength rather than adding together. Foundation, Attunement and Coupon Book cannot stack or refresh while active; they can be purchased again after their effect ends. Every purchase requires the full price upfront. Refunds cannot reduce a base purchase's net cost below $1.

Polish and the old capped Recall / Full Load are replaced by Balloon Call. Foundation replaces the proposed Landmark. Extension, Scaffolding, Follow Suit and Wild Selection are outside this card set. Delivery Contract—the proposed automatic floor after each of the next N purchases—remains a separate, unimplemented idea.

## Screen composition

### Persistent HUD

The top of the screen contains:

1. Current hotel height.
2. Coins remaining.
3. Balloon Dock counters: Bunny/Pink ×N, Frog/Green ×N, Cat/Orange ×N.
4. Active Foundation type and next bonus, or “Foundation ready · next +1” before its first suited purchase.
5. Active Attunement type and remaining shops, including the currently visible shop.

Keep the two strategy indicators visible while viewing the tower; do not hide essential streak or expiry information exclusively in the Workshop. Use small paper tabs that disappear when their effect ends.

The Balloon Dock is authoritative. Balloons do not remain attached to lower neighborhoods because those floors eventually move offscreen.

When a power card is pressed, the relevant Dock counter expands into an equation such as:

```text
Pink balloons ×4 → +4 Pink floors
```

### Tower camera

- Keep the open construction platform in the upper-middle playfield.
- Show approximately 10–15 recent floors at readable scale.
- Allow older floors to travel below the screen as the camera follows construction upward.
- Keep HUD and offer cards fixed while the tower moves behind them.
- Do not automatically pan to old neighborhoods during ordinary play.
- If Copycat's source is offscreen, show it on a small fold-out paper snapshot instead of moving the camera away from the open top.

### Offer tray

Three large paper cards remain fixed at the bottom. The card art is part of the physical world:

- Construction cards contain folded boxes.
- Technique cards unfold like tiny paper stages.
- Persistent upgrades fold into charms or tools and move into the Engine/Workshop view.
- Strategy powers install a visible Foundation counter strip or Attunement seal with remaining-shop tabs.
- Mosaic cards display all three type symbols and arrows in construction order: left to right on the card means bottom to top in the tower. No type has a fixed bottom or top position across offers.

## Motion language

### Hybrid stop-motion

- World objects—boxes, residents, balloons, Copycat, clouds, and paper props—animate at an intentional 12 frames per second using pose swaps and stepped transforms.
- Input feedback, text, counters, focus rings, and camera settling remain smooth at display refresh rate so the game does not feel sluggish or uncomfortable.
- Add at most 1–2 pixels of seeded positional variation between stop-motion poses. Do not apply continuous random jitter.
- Hinges and folds rotate around visible paper creases. Objects should never stretch like rubber.
- Use soft cast-shadow changes to clarify which paper layer is above another.

### Causality

Every result follows the same readable sequence:

1. **Source:** show what caused the effect.
2. **Transfer:** show paper, balloons, stamps, or coins moving toward the destination.
3. **Result:** attach floors at the open top.
4. **Record:** update height, coins, balloons, and installed upgrades.

Never update a counter before the physical event that caused it.

### Timing targets

| Beat | Target |
| --- | --- |
| Card press response | 60–100 ms |
| Card commit/focus | 120–180 ms |
| Box travel to platform | 250–350 ms |
| One box unfolding | 400–550 ms |
| Resident emergence | 200–300 ms |
| New balloon to Dock | 350–500 ms |
| Ordinary one-floor purchase total | 0.9–1.2 s |
| Multi-floor or power purchase total | 1.2–1.8 s |
| End-of-run roof reveal | 1.8–2.5 s |

Multi-floor actions must overlap their sub-animations. Never play eight complete one-second floor animations sequentially.

## Card interaction and play sequence

### 1. Press and preview

On pointer-down:

- Depress the card immediately to roughly 97% scale.
- Raise its paper edge shadow on the opposite side of the press.
- Highlight the predicted source in the playfield or Balloon Dock.
- Show the exact output and projected coins.
- Do not roll Mystery/Surprise outcomes during preview.

Dragging roughly 10 pixels away cancels the pending purchase and restores the card. Returning before release restores the preview.

### 2. Commit

For Choice 1, pointer-up first opens the type picker. Show the exact total and Foundation consequence for each allowed type. Cancel or Escape restores the offer without payment, rerolling, or consuming an Attunement shop. Block background purchases while the picker is open and restore focus on cancellation. Choosing a type performs the commit below once.

For other cards, pointer-up over the card commits directly:

1. Charge the price immediately.
2. Fold the two unchosen cards closed and slide them downward into the tray.
3. Lift the chosen card toward the action area.
4. Resolve the engine transaction once. Animation reads the committed result; it never decides gameplay.
5. Use the chosen card's family-specific animation.

### 3. Resolve

- Construction card: its pictured box lifts out and travels to the construction platform.
- Technique card: it unfolds into a miniature stage and releases balloons, Copycat, or another actor.
- Upgrade card: it folds into a charm/tool and attaches to the appropriate Dock chip or Workshop slot.
- Economy card: coins, coupons, or paper scraps visibly move between the card and HUD.
- Strategy card: a paper counter strip or seal unfolds into its HUD home.
- If Foundation awards a bonus, append its separately marked boxes after the card's ordinary output. A suited upgrade or Attunement purchase can install its prop and then deliver Foundation floors. Calculate the bonus from the pre-purchase streak; do not let generated floors advance it again.

### 4. Finish and deal

After the result is physically settled:

1. Increment height and any secondary counters on the same frame as the final paper snap.
2. Register one balloon for each new neighborhood created by the full ordered output. A same-type batch creates at most one; Mosaic can create several. Foundation floors may extend the final neighborhood rather than creating another.
3. Fold the spent card flat and slide it away.
4. Consume one active Attunement shop for this purchase, unless this purchase installed Attunement. Deal three new cards under the resulting lock state as closed paper packets, then unfold them together. The engine commits the countdown with the purchase; the visual tab tear presents that committed change without decrementing it a second time.

Further purchases remain unavailable while resolving, but a **Reveal now** control immediately completes the current sequence without rerolling or changing the committed result.

## Prefab box unfolding into a floor

This is the most reused animation and should receive the most polish.

### Required assets

- Compact cube.
- Landed/squashed cube.
- Cross-shaped open paper net.
- Half-raised walls.
- Nearly closed room with visible tabs.
- Completed floor shell.
- Separate window, resident, curtain, and accessory layers.

### Sequence

1. **Approach:** the box follows a shallow arc toward the open top. Its paper shadow grows as it approaches.
2. **Land:** it compresses by only 2–3%, makes a soft paper tap, and settles between the four construction tabs.
3. **Open:** the top and side faces rotate outward around their creases until the cube becomes a cross-shaped paper net.
4. **Raise walls:** the rear and side panels fold upward. Their cast shadows move across the center panel.
5. **Raise façade:** the front panel folds up last, revealing the window aperture.
6. **Lock tabs:** corner tabs tuck inward in two alternating beats. A tiny paper snap and restrained haptic mark completion.
7. **Dress floor:** window frame, curtains, flower box, and other cosmetic pieces unfold from slots or pop into place.
8. **Welcome resident:** the resident animation begins only after the shell is locked.
9. **Advance camera:** once the floor is stable, the tower shifts downward smoothly enough to return the open construction platform to its standard screen position.

The tower height increases at step 6, not when the box first appears.

### Multiple floors

- Land all required boxes as a small stack or queue above the platform.
- Unfold them bottom-to-top with a 60–90 ms stagger.
- Start the next box as soon as the previous façade is upright; do not wait for its resident animation.
- Let residents emerge in a brief cascade after their respective shells lock.
- For more than four floors, fully animate the first two and final floor. Compress the middle floors into a faster rhythmic fold sequence while preserving the exact count.

## Resident emergence

Every completed floor gets one cosmetic resident moment.

### Sequence

1. Window shutters or folded curtains open from the center crease.
2. A flat resident cutout rises from below the sill.
3. The body unfolds from a narrow accordion pose into its normal silhouette.
4. One short behavior plays: wave, blink, read, nap, water a plant, drink tea, or hang laundry.
5. The resident settles into a low-motion idle pose.

Resident actions must not imply gameplay bonuses. Floor type remains recognizable through paper color, resident species, and icon shape.

### Variation rules

- Use at least four façade variants and five resident behaviors per floor type.
- Pick variants deterministically from seed plus floor ID so replays match.
- Avoid the same façade/behavior combination on adjacent matching floors when another variant is available.
- Keep all modules the same width and height.
- Keep the same fold anchors across variants so every module can reuse the unfolding animation.
- Do not use a miniature roof, cupola, or large overhang as a floor decoration.

### Suggested variants

| Bunny/Pink | Frog/Green | Cat/Orange |
| --- | --- | --- |
| Flower-box arch; waving | Lily window; reading | Sunny bay; sleeping |
| Heart curtains; reading | Round window; umbrella | Striped curtains; waving |
| Carrot planter; watering | Vine trellis; watering | Fish mobile; watching |
| Tiny balcony; tea | Rain barrel; napping | Laundry rail; folding clothes |
| Moon mobile; sleeping | Paper tub; smiling | Plant shelf; pawing a leaf |

## New neighborhood and balloon registration

A new neighborhood begins on the first floor of an empty tower, or when the newly appended floor type differs from the previous top floor type. Inspect the complete ordered batch, including Mosaic transitions and any Foundation bonus. Queue a balloon for every new neighborhood and register them after the delivery; none can affect that same purchase’s payout.

### Sequence

1. Complete the first floor and resident emergence.
2. The resident notices the color change and looks upward.
3. A small folded balloon packet slides out through the window.
4. The packet opens into four petals, inflates over 3–4 stop-motion poses, and reveals the matching animal emblem.
5. The resident releases the string.
6. The balloon travels on a curved path toward its matching Balloon Dock chip.
7. The chip makes room by opening like a small paper envelope.
8. The balloon scales down and slips into the envelope; it does not dissolve in mid-air.
9. The envelope closes and the count flips from N to N+1.
10. Briefly show “New neighborhood” the first few times this occurs; omit the label after onboarding.

If the appended floor matches the previous top type, skip the balloon sequence. The matching Dock chip may give one subtle acknowledgment bob, but its count does not change.

## Balloon Call

Current mechanic: **Recall**, $7. Recall and Polish merge into this single power. Append one matching floor for each existing matching neighborhood, regardless of its length. The output is the matching Balloon Dock count captured before the action: one Pink neighborhood of length 8 pays one floor; two Pink neighborhoods of lengths 1 and 8 pay two. There is no per-neighborhood length cap or Full Load variant.

### Preview

- Expand the matching Dock chip.
- Show `balloons ×N → +N floors`. If Foundation applies, show its bonus separately, for example `4 balloons + Foundation 2 → 6 Pink floors`; the balloon count remains four.
- Fan the stored balloon edges just enough to imply a fleet.
- Show N ghost floor outlines above the open top, or show up to five outlines plus an ×N label for larger results.

### Commit sequence

1. The selected card unfolds into a small cloud-shaped launch mat.
2. The matching Dock envelope opens.
3. For N up to five, N individual balloons emerge. For larger N, show a layered bouquet of five representative balloons with a visible ×N cargo tag.
4. Each balloon carries a compact matching prefab box. For large outputs, the bouquet carries a paper rack labeled ×N rather than rendering dozens of boxes.
5. The fleet arcs toward the open top and releases its cargo into the construction queue.
6. Prefab boxes unfold using the standard multi-floor sequence.
7. Source balloons loop back along the reverse path and tuck into the Dock envelope. The Dock count is unchanged because the fleet is reusable.
8. If the delivered type differed from the old top type, the resulting new neighborhood launches exactly one new balloon after all delivered floors settle. That balloon increments the Dock for future actions only.

## Copycat

Current mechanic: **Overgrow**, $5. Identify the largest existing neighborhood, calculate `floor(length / 2)` clamped between 1 and 8, and append copied floors of that type at the open top. Read the source once before adding floors. No source floor is changed or moved. An earlier source neighborhood stays the same size; if the source is already at the open top, the new matching floors naturally extend it. Copycat is a suitless purchase, so it neither advances nor ends Foundation, even when its output type differs from the Foundation type.

### Copycat character

- White paper cat with lavender patches.
- Star-patterned cape.
- Brass bell at the neck.
- Oversized paw-shaped stamp.
- Small folding cloud used as a stage.
- Distinct from ordinary orange Cat residents.

### Preview

- Card displays source type, source length, and exact output: `Tallest: Frog ×8 → +4 Frog floors`.
- If the source neighborhood is visible, outline it with a lavender stitched-paper bracket.
- If it is offscreen, slide a small fold-out snapshot from the card showing the relevant neighborhood. Do not pan away from the construction platform.

### Commit sequence: Spot → Stamp → Send → Unfold

1. **Spot:** the Copycat card unfolds into a cloud. Copycat springs up, opens a paper spyglass, and identifies the largest neighborhood. The source outline or snapshot pulses once.
2. **Take impression:** a translucent sheet of tracing paper presses briefly against the source representation, then peels away carrying its color, resident emblem, and façade pattern. The source remains intact.
3. **Stamp:** blank cream prefab boxes pop out of Copycat's cape. Copycat places the tracing sheet on each and presses the paw stamp. Each box changes into the copied neighborhood type with a papery thump.
4. **Send:** Copycat points upward. The printed boxes bounce along a curved dotted path toward the open top. Copycat does not use the Balloon Dock; this keeps the technique visually distinct.
5. **Unfold:** boxes land and become floors through the standard unfolding sequence.
6. **Finish:** show the exact `+N` result beside Copycat. Copycat bows, folds the cloud closed, and returns to the card.
7. **Register:** if the copied type differed from the old top, the completed block forms one new neighborhood and launches one new balloon after Copycat leaves.

Ties use the earliest largest neighborhood according to the game rule. Preview must identify the chosen source before purchase.

## Base construction cards

Names remain provisional; the animations are canonical.

### One Room

- One box lifts from the card.
- It travels to the open top and performs the complete unfolding sequence.
- Resident and possible new-neighborhood balloon follow.

### Prefab Pack

- A paper belly-band tears open to reveal three boxes.
- Boxes queue over the platform and unfold bottom-to-top.
- Resolve only one new-neighborhood check after the complete same-type block lands.

### Surprise Parcel

- A sealed cream parcel with question-mark folds rises from the card.
- It shakes in three unequal stop-motion beats. It does not cycle through fake results.
- Lucky Bell or other odds upgrades flash before the seal breaks.
- The parcel unfolds once to reveal the committed result: 1, 3, or 8 boxes.
- Boxes then use the normal construction sequence.
- Skipping the reveal never rerolls the outcome.

### Choice 1

Current rule: $4 for one floor of a chosen type, compared with $3 for One Room. Room Pattern, Master Fold, Coupon Book and Foundation all use the final choice normally.

1. Open a small paper sample book with a tab for each allowed type.
2. Each tab shows the exact output and price. When Foundation is active, also show its bonus or “Ends Foundation.”
3. Do not spend coins or choose a result until the player selects a tab. Cancellation closes the book and returns to the unchanged shop.
4. On selection, stamp a blank prefab box with the chosen type and deliver it to the open top. Only the new, undelivered box changes appearance.
5. Show upgrade and Foundation bonus boxes as additional deliveries, using the same type.

While Attunement is active, show only its allowed type and explain the lock. Choice 1 does not bypass it. Preserve this explicit choice step and its exact payout preview even when only one option remains.

### Mosaic

Current rule: $6 for an exact three-floor sequence, fixed when the offer is dealt. Letters below stand for distinct floor types, not particular colors.

| Variant | Pattern | Example, bottom to top |
| --- | --- | --- |
| Trio | ABC | Frog → Bunny → Cat |
| Sandwich | ABA | Cat → Frog → Cat |
| Pair first | AAB | Bunny → Bunny → Frog |
| Pair last | ABB | Frog → Cat → Cat |

Each pattern has six type assignments with the current three types, giving 24 distinct sequences. Every type can appear first or last. Preview the full order and its relationship to the current top; never choose a new order during resolution.

1. The card unfolds into a three-pocket delivery sleeve, numbered 1–3.
2. Lift out the three printed boxes in order. Keep their type symbols visible throughout travel.
3. Deliver to the open top in the displayed order, first printed box at the bottom of the new batch.
4. The first box may extend the old top neighborhood. Each subsequent type change begins another neighborhood.
5. After the batch settles, register one balloon per new neighborhood. A Trio on an empty tower creates three; a Pair creates two. Matching the previous top can reduce the number of new neighborhoods by one.

Mosaic receives no Room Pattern or Master Fold extras and ends Foundation before any bonus. It counts as a base purchase for Coupon Book. It is unavailable during Attunement, so the player never sees a mixed-type offer contradicting the 100% lock.

## Strategy powers

### Neighborhood Streak

Current rule: $7. The next purchase with a printed or chosen type starts a streak at +1 bonus floor. Each further purchase of that type gains +2, +3, and so on, with no fixed duration or cap. Buying another type or Mosaic ends the effect before awarding a bonus; it does not automatically restart on the new type.

The streak follows **purchase types, not the current top neighborhood**. Type-specific Balloon Call, Room Pattern and Attunement purchases advance it, as do ordinary base cards and the selected type of Choice 1. Suitless purchases, including Copycat, Reserve Delivery, Master Fold, Lucky Bell and Coupon Book, leave it unchanged. Generated floors do not count as purchases. Foundation cannot be refreshed or stacked while active; after it ends, it can be bought again.

#### Install and trigger animation

1. Foundation unfolds into an accordion counter strip beside the tower HUD, showing “Ready · next +1.” It adds no floor on installation and places nothing beneath the existing tower.
2. The first suited purchase stamps that type onto the strip. Preview its normal output and Foundation bonus separately, then show the total.
3. Resolve the purchased card normally. Pull the committed number of matching bonus prefab boxes from the strip and append them at the open top.
4. Advance the strip to the next bonus after delivery: +1 earned → next +2. A suited power that creates no ordinary floors still gets this delivery.
5. On a different-type purchase or Mosaic, show “Ends Foundation” before commitment. Fold the strip closed without a bonus delivery. Suitless purchases leave it visibly paused at the same next bonus.

Example: Foundation → Pink One Room yields 2 floors → Pink Balloon Call with one Pink neighborhood yields 1 + 2 = 3 floors → Pink Choice 1 yields 1 + 3 = 4 floors, before other upgrades. A Green One Room then yields its normal output and closes Foundation.

### Type Lock

Current rule: $6 for a card with a printed type. **100% of suited offers** in the next three shops use that type. Card families and types still vary; suitless cards remain eligible with their normal effects. This is an offer filter, not a conversion of existing floors, a Mystery-odds change, or a guarantee of three base cards.

Choice 1 permits only the locked type. Mosaic is temporarily ineligible. Foundation still evaluates the Attunement card's printed type: buying matching Attunement can earn a streak bonus; a different type ends the streak. Attunement cannot stack or refresh while active, and can be bought again after expiry.

#### Install, countdown and expiry animation

1. Fold the card into a colored seal on the offer tray with three perforated shop tabs. The installation purchase consumes no tab.
2. Stamp the seal onto the next three offer packets before they open. Every type-bearing offer displays the locked type; keep suitless card art neutral.
3. The HUD shows “Pink Attunement · 3 shops left,” including the currently open shop.
4. Every committed purchase from a locked shop tears off one tab, including suitless purchases. Merely previewing a card, opening or canceling Choice 1, or skipping an animation consumes nothing extra.
5. After the first and second purchases, reveal shops with two and one tabs left. The third shop is still locked. After its purchase, fold the empty seal away and reveal an unrestricted fourth shop.

Do not show mixed-type mosaics or off-type Choice tabs during a lock. On replay or a new game, clear both strategy props and all pending animation state.

## Persistent upgrades

Exact names can change, but every upgrade needs a visible home and a future trigger.

| Current mechanic | Working presentation | Install animation | Future trigger |
| --- | --- | --- | --- |
| Floor-type Reactor | **Room Pattern** | Card folds into a patterned swatch and pins beside the matching Balloon Dock chip. | Swatch stamps bonus boxes after a matching base build, including Choice 1 and Surprise Parcel; excludes Mosaic. |
| Assembler | **Master Fold** | Instruction card folds into a golden crease guide in the Workshop. | Guide flashes for One Room, Prefab Pack and Choice 1; excludes Surprise Parcel and Mosaic. |
| Stabilizer | **Lucky Bell** | Tiny bell charm clips beneath the Surprise Parcel icon. | Bell rings once before the committed Mystery parcel opens. |

Upgrade levels replace their old visual value. Do not stack three separate copies of the same charm. Instead, enrich the installed prop with another fold, stripe, star, or bell.

Upgrade effects never modify existing floors. Their bonus animation occurs only when a later eligible construction card creates boxes. A separate Foundation bonus can accompany the installation purchase of a type-specific Room Pattern; show its source as Foundation, not as the newly installed upgrade.

## Economy effects

### Coupon Book / Rebate

1. Card folds into a coupon strip under the coin counter.
2. Each eligible base purchase, including Choice 1 and Mosaic, tears off one perforated tab.
3. Refund coins arc back into the counter after the gross cost is visibly paid.
4. Remaining uses decrement on the same frame as the tab tear.
5. Non-base purchases leave the strip untouched.

### Reserve Delivery / Vault

The final name and fiction should be confirmed with the rule. For the current behavior:

1. Show the amount of reserve remaining after the card price.
2. Convert the calculated payout into prefab boxes matching the current top type.
3. A neutral cargo balloon delivers the rack to the open top.
4. Boxes unfold normally and merge with the current top neighborhood.

The preview must show the exact payout; do not visually imply that all remaining coins were consumed if the rule leaves them in the player's balance.

## Camera advancement

After each locked floor:

- Keep the construction platform's resting Y position stable.
- Translate the tower downward by one floor height while the camera tracking layer moves smoothly over roughly 250–350 ms.
- For large batches, follow at a steady rate rather than snapping after the entire batch.
- World objects may retain their 12 fps pose cadence, but camera motion should remain smooth and critically damped with no bounce.
- Never move the Balloon Dock, counters, or cards with the tower.

## End of run and roof reveal

No roof is visible at any point during active construction.

### Sequence

1. The last floor and any new balloon finish resolving.
2. Offer cards fold closed. Ambient residents pause and look upward.
3. Hold for approximately 250 ms of quiet anticipation.
4. A large neutral sheet of paper descends from above, carried by a special golden hotel balloon.
5. The sheet lands on the construction platform and folds into the final roof or cupola.
6. A Cloudtop Hotel sign unfolds from the façade and a small flag pops from the roof.
7. All visible residents cheer in a staggered wave. Balloon Dock envelopes open and release a brief celebratory cluster without changing their counts.
8. The camera pulls back to show the complete tower from base to roof.
9. Display final height, coins left, neighborhoods, and replay controls.

Roof variations may depend on height tier for celebration, but they are cosmetic and must not imply an unearned gameplay bonus.

## Ambient animation

Ambient motion supports the handcrafted world but must never compete with a resolving card.

- Drift one background cloud layer very slowly.
- Allow one visible resident at a time to blink, wave, read, or nap.
- Give Balloon Dock chips an occasional one-frame paper rustle, never continuous synchronized bobbing.
- Dim or pause ambient loops during Mystery, Balloon Call, Copycat, and the roof reveal.
- Do not animate every window simultaneously.

## Sound and haptics

Suggested sounds are short and tactile:

- Card press: fingertip tap on cardstock.
- Fold: dry paper crease.
- Tab lock: soft snap.
- Balloon inflation: tiny accordion puff.
- Dock merge: envelope tuck plus bell tick.
- Copycat stamp: padded wooden thump.
- Coin change: small wooden token clack.
- Roof completion: layered fold, bell chord, then cheers.

Trigger sound, haptic, and visual contact on the same frame. Reserve haptics for card commit, final tab lock, Dock increment, Copycat stamp, and roof completion.

## Reduced motion and skipping

### Reduced motion

When `prefers-reduced-motion: reduce` is active:

- Replace travel arcs and camera following with short cross-fades.
- Show cube, open net, and completed floor as three static states rather than rotations through space.
- Highlight the relevant Balloon Dock chip, update its count, and outline the new floor without flying a balloon across the screen.
- Reduce Copycat to source highlight → stamp flash → completed floors.
- Replace the end camera pullback with a dissolve to the full-tower view.
- Preserve all counts, source highlights, and completion feedback.
- Show Mosaic in its exact order with static type symbols. Update Foundation and Attunement props directly; skipping never adds a streak step or consumes another shop.

### Reveal now

At any time during a committed resolution, **Reveal now**:

1. Cancels pending visual timers.
2. Places every object directly in its final state.
3. Updates HUD and Dock counters.
4. Preserves the already committed Mystery result.
5. Continues to the next offer or end-of-run state.

## Asset production plan

The paper style is designed to work with generated still assets and deterministic transforms rather than generated video.

### Minimum asset groups

- Three prefab box colorways, plus blank cream Copycat boxes.
- Six unfolding states per box/floor shell.
- Four or more façades per floor type.
- Five or more resident poses/activities per species.
- Balloon states: folded packet, inflating poses, full flight, basket/cargo variations, Dock chip.
- Copycat poses: card idle, spring out, spyglass, trace, stamp, point/send, bow.
- Construction platform and separate corner tabs.
- Technique stages/clouds.
- Upgrade charms and level variants.
- Choice 1 sample-book tabs and a blank prefab box.
- Reusable three-pocket Mosaic sleeve with type symbols and order markers.
- Foundation accordion strip with ready, typed, increment, and closed states.
- Attunement seals for each type with three, two, one, and zero remaining-shop tabs.
- Final roof tiers and completion sign.

### Generation constraints

- Request transparent cutouts for composited game assets.
- Lock camera angle, light direction, module dimensions, and fold anchors across every variant.
- Generate residents, accessories, and windows separately from floor shells when possible.
- Preserve generous transparent padding around moving limbs, balloons, and unfolding flaps.
- Name assets by semantic role and state, not by generation batch.

Example organization:

```text
assets/
  floors/
    bunny-shell-unfold-01.webp
    bunny-facade-flowerbox.webp
    frog-facade-lily.webp
    cat-facade-sunnybay.webp
  residents/
    bunny-wave.webp
    frog-read.webp
    cat-sleep.webp
  balloons/
    bunny-folded.webp
    bunny-inflate-01.webp
    bunny-flight.webp
  copycat/
    spyglass.webp
    stamp.webp
    send.webp
```

## Acceptance checklist

- [ ] Every created floor visibly arrives at and attaches to the open top.
- [ ] No gameplay effect changes a completed floor.
- [ ] A new neighborhood creates exactly one new balloon.
- [ ] A continuing neighborhood creates no balloon.
- [ ] Newly earned balloons never contribute to the action that earned them.
- [ ] Balloon Dock counters remain readable when source neighborhoods are offscreen.
- [ ] Balloon Call visibly connects its Dock count to the number of delivered floors.
- [ ] Copycat identifies a source, copies half its length rounded down (minimum 1, maximum 8), and sends copies only to the top; earlier neighborhoods keep their size.
- [ ] Balloon Call pays one floor per matching neighborhood, regardless of length, and displays Foundation extras separately.
- [ ] Choice 1 previews the selected type's bonuses; canceling preserves coins, offers, streak, countdown, and random state.
- [ ] Mosaic shows the exact order before purchase, supports all 24 sequences, and awards one balloon per newly created neighborhood.
- [ ] Mosaic receives no Room Pattern or Master Fold extras, ends Foundation, and remains eligible for Coupon Book.
- [ ] Foundation advances once per matching suited purchase, pauses on suitless purchases, and ends before a switched-type or Mosaic bonus could be awarded.
- [ ] Foundation bonus floors only arrive at the open top; no animation suggests work under or inside the existing tower.
- [ ] Attunement locks exactly three future shops, including Choice 1, excludes Mosaic, and releases the fourth shop.
- [ ] Installing Attunement consumes no shop; each subsequent purchase consumes one, even a suitless purchase.
- [ ] Strategy state stays readable on phone and landscape layouts; replay clears it.
- [ ] Resident animation begins only after the room shell locks.
- [ ] Floor variants preserve type color, size, and fold anchors.
- [ ] No roof appears until the run is complete.
- [ ] All committed animations can be skipped without changing the result.
- [ ] Reduced-motion mode communicates sources and results without large movement.
- [ ] One ordinary purchase resolves in about one second; large powers remain under about two seconds before optional celebration.
