# Cloudtop Hotel — Story and Animation Direction

Status: concept specification for re-theming the One More Card prototype. Names for individual cards are working names unless marked as a core term.

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

## Screen composition

### Persistent HUD

The top of the screen contains:

1. Current hotel height.
2. Coins remaining.
3. Balloon Dock counters: Bunny/Pink ×N, Frog/Green ×N, Cat/Orange ×N.

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

On pointer-up over the card:

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

### 4. Finish and deal

After the result is physically settled:

1. Increment height and any secondary counters on the same frame as the final paper snap.
2. Resolve a new-neighborhood balloon, if applicable.
3. Fold the spent card flat and slide it away.
4. Deal three new cards as closed paper packets, then unfold them together.

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

A new neighborhood begins when the newly appended floor type differs from the previous top floor type.

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

Working rule: Recall and Polish merge into this single power. Append one matching floor for each existing matching neighborhood. The output is the matching Balloon Dock count captured before the action.

### Preview

- Expand the matching Dock chip.
- Show `balloons ×N → +N floors`.
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

Working rule: identify the largest existing neighborhood, derive a configured number of floors from its length, and append copied floors of that type at the open top. The source neighborhood never changes.

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

### Choice 1 and Mosaic

Choice 1 is a premium single-floor base card: select its floor type before payment. The picker previews all applicable bonuses and cancellation spends nothing.

Mosaic presents its full three-floor order before purchase. Variants are ABC, ABA, AAB, and ABB across floor-type permutations. Deliver and unfold boxes in exactly that order, bottom to top. Each new neighborhood registers its own balloon; there can be multiple new neighborhoods in a Mosaic delivery. Existing floors never change. Mosaic uses its printed pattern without Reactor or Assembler extras.

### Foundation and Attunement

Foundation replaces the earlier Landmark idea. The next suited purchase starts a streak at +1, then same-type purchases earn +2, +3, and so on. Switching types or buying Mosaic ends it; suitless purchases pause the streak. Show the chosen type and next bonus in the persistent HUD. Bonus floors arrive after the ordinary purchase resolves, with no recursive triggers.

Attunement fixes all suited offers to its type for the next three shops. Display its type and remaining shops in the HUD. Choice 1 is restricted to that type; Mosaic offers pause until it expires. Suitless powers keep their normal behavior. Each purchase consumes one shop; installing the effect does not consume its first use.

## Persistent upgrades

Exact names can change, but every upgrade needs a visible home and a future trigger.

| Current mechanic | Working presentation | Install animation | Future trigger |
| --- | --- | --- | --- |
| Floor-type Reactor | **Room Pattern** | Card folds into a patterned swatch and pins beside the matching Balloon Dock chip. | Swatch stamps bonus boxes after a matching base build. |
| Assembler | **Master Fold** | Instruction card folds into a golden crease guide in the Workshop. | Guide flashes and slides bonus boxes from behind fixed Prefab cards. |
| Stabilizer | **Lucky Bell** | Tiny bell charm clips beneath the Surprise Parcel icon. | Bell rings once before the committed Mystery parcel opens. |

Upgrade levels replace their old visual value. Do not stack three separate copies of the same charm. Instead, enrich the installed prop with another fold, stripe, star, or bell.

Upgrades never modify existing floors. Their animation occurs only when a later eligible construction card creates bonus boxes.

## Economy effects

### Coupon Book / Rebate

1. Card folds into a coupon strip under the coin counter.
2. Each eligible base purchase tears off one perforated tab.
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
- [ ] Copycat identifies a source, leaves it intact, stamps copies, and sends them only to the top.
- [ ] Resident animation begins only after the room shell locks.
- [ ] Floor variants preserve type color, size, and fold anchors.
- [ ] No roof appears until the run is complete.
- [ ] All committed animations can be skipped without changing the result.
- [ ] Reduced-motion mode communicates sources and results without large movement.
- [ ] One ordinary purchase resolves in about one second; large powers remain under about two seconds before optional celebration.

