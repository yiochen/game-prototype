# UI design interview

Status: wrapped at the user's request. Accepted UI decisions are recorded below; unresolved balance and presentation details remain open for prototyping. Question 206 is intentionally deferred and has no selected answer.

Visual direction: [doodle](./art-direction.md). Questions 1–23 used image-generated, polished 2D screen options. On 2026-10-06 the user requested text descriptions only for follow-on questions. In Question 41 the user explicitly requested image-generated backgrounds for the three result outcomes. That request is an exception for these backgrounds; continue follow-on questions in text unless images are requested again.

Orientation: locked portrait throughout the game, including the sushi bar, expedition, Workshop, and related screens, as accepted in Question 31. Exact device insets and sizes remain open.

Recipe action label: **Prepare**, accepted in Question 54. Earlier Assign labels are preserved in historical option descriptions below; Prepare is the current player-facing label. Chef assignment to a working spot remains a separate concept.

The fixed lower recipe preview described in this interview is the **recipe details panel** containing the selected dish's artwork, facts, and Prepare action. It is distinct from the live restaurant's Preview mode.

## Question 1: contextual harpoon button placement

Accepted: **A — anchored lower-right button**. During the shooting window, the contextual harpoon button stays in the lower-right corner rather than following the submarine. It overlays the continuous scene without a footer. Question 30 retains this position for all players, and Question 31 locks the game to portrait. Exact insets and button size remain unresolved.

- **A — anchored lower-right button**: a consistent thumb target, separate from the submarine and upcoming hazards.
- **B — submarine-following button**: positioned beside the submarine, visibly connected to the action but moving with steering.

Recommendation: A, because aiming already requires tracking the creature and steering; a stable action target avoids an additional moving target under the thumb. Both options overlay the full-screen scene without a footer. Hull, salvage, pause, and boss-bar arrangement in the images are provisional and are not accepted by selecting the harpoon placement.

Generated options: [A — anchored](../design/ui/01a-harpoon-anchored.png), [B — follows submarine](../design/ui/01b-harpoon-follows-ship.png). [Exact prompts](../design/ui/01-harpoon-placement-prompts.md) are saved alongside them. The illustrated species and scene details are examples, not additions to the accepted creature catalog.

Question 27 resolved simultaneous steering and shooting, Question 30 resolved handedness as a fixed lower-right position, and Question 31 locks orientation to portrait throughout the game.

## Question 2: following-range presentation

Accepted: **A — visible following area**, with the user's revision: a narrow vertical following strip tracks the creature's horizontal position. It has no upper or lower boundary and does not test forward/backward distance. During pursuit, ship and creature advance at the same forward speed; the player controls lateral alignment. The narrower strip increases tracking difficulty. Exact width remains open.

- **A — visible following area**: a subtle translucent area behind the creature, in addition to the existing cable feedback.
- **B — cable feedback only**: no area overlay; the cable's tautness, color, and fraying communicate when the ship leaves range.

Original recommendation: A. The player can see where to recover before the cable breaks, while planning dodges inside the allowed area. Keep the overlay quieter than attack warnings. B leaves the water clearer but requires learning the boundary through feedback. Strip width, colors, visibility timing, and warning behavior remain unresolved; the earlier images show the superseded rounded geometry.

Corrected generated options: [A — visible area](../design/ui/02a-visible-following-area.png), [B — cable only](../design/ui/02b-cable-only.png). [Exact generation and correction prompts](../design/ui/02-following-range-prompts.md) are saved alongside them. Cable feedback remains part of both options.

The rounded area in the earlier A image is superseded by the user's vertical-strip revision. Cable warnings and the grace period still apply when leaving the strip. Preserve the accepted attack rule: standard discharge strips leave a usable safe position inside following range.

## Question 3: following-strip width

Accepted: **B — about two ship widths** as the initial strip-width target. The rendered hull silhouette is an illustrative reference, not a finalized hitbox. Exact width and associated creature speed, hazards, and grace duration remain playtest tuning.

- **A — about three ship widths**: focused tracking with space for a short sideways dodge.
- **B — about two ship widths**: tighter tracking with less margin for movement and hazards.

Original recommendation: A as the initial prototype target. The user selected B for tighter tracking. Width, creature lateral speed, hazard size, and grace duration must be tuned together; this selection does not establish a species-specific width rule.

Generated options: [A — three ship widths](../design/ui/03a-three-width-strip.png), [B — two ship widths](../design/ui/03b-two-width-strip.png). [Exact prompts](../design/ui/03-following-strip-prompts.md) are saved alongside them. Both are continuous vertical strips with no visible top or bottom boundary.

## Question 4: out-of-range recovery cue

Accepted: **B — cable warnings only**. Leaving following range adds no return arrow. The visible strip and the cable's tautness, color change, and fraying communicate the need to recover. The existing grace period remains, without an explicit countdown.

- **A — return arrow plus cable warnings**: a local inward arrow helps the player recover; it disappears upon return.
- **B — cable warnings only**: the taut, changing-color, fraying cable and visible strip provide the feedback, without an extra arrow.

Original recommendation: A for a clearer recovery direction. The user selected B to retain cable warnings without another cue. Both mockups show the same out-of-range state, not hull damage or a broken cable.

Generated options: [A — return arrow](../design/ui/04a-return-arrow.png), [B — cable warnings only](../design/ui/04b-cable-warning-only.png). [Exact prompts](../design/ui/04-recovery-cue-prompts.md) are saved alongside them.

## Question 5: creature attack-strip warning

Accepted: **A — translucent amber fill and diagonal hatching** for the electrical attack-strip warning, with a small lightning symbol. This distinguishes the dangerous band from the mint following strip. Exact warning timing, opacity, and active-discharge appearance remain open.

- **A — translucent amber fill and diagonal hatching**: the entire affected band is marked, with a small lightning symbol.
- **B — amber boundaries and lightning symbol**: the area has no extra fill or hatching, preserving more seabed detail.

Recommendation accepted: A, because a distinct pattern makes the dangerous area readable without relying on color alone and prevents confusing it with following range. Both are warning-state images, before discharge. They leave a safe position inside the accepted narrow following strip; no new targeting rule, countdown, or damage behavior is proposed.

Generated options: [A — hatched warning](../design/ui/05a-hatched-attack-warning.png), [B — outlined warning](../design/ui/05b-outlined-attack-warning.png). [Exact prompts](../design/ui/05-attack-warning-prompts.md) are saved alongside them.

## Question 6: first-catch recipe reveal

Accepted: **B — dedicated recipe card** for first-time discoveries. A large reveal celebrates the new dish; Continue leads to expedition results. The recipe is earned immediately upon catching, rather than gated by the continuation tap, and no hazards continue behind the reveal. Ordinary repeat catches do not need a new-recipe reveal.

- **A — brief in-scene badge**: show the new recipe over the finished encounter, then transition automatically to results with its details.
- **B — dedicated recipe card**: celebrate the new dish in a large reveal card; Continue leads to the expedition results.

Recommendation accepted: B for first-time recipe discoveries, because they are the main connection between expeditions and restaurant growth and are deliberately not previewed before launch. Question 38 subsequently adds a full-screen catch cutscene before the award dialog. The illustrated dish name and art are examples, not an accepted recipe entry. Results layout, recipe statistics, and exact transition timing remain open.

Generated options: [A — brief badge](../design/ui/06a-recipe-badge.png), [B — reveal card](../design/ui/06b-recipe-reveal-card.png). [Exact prompts](../design/ui/06-recipe-reveal-prompts.md) are saved alongside them.

## Question 7: information on the recipe reveal

Accepted: **A — compact recipe facts**. The reveal shows fixed price per dish, base preparation time before chef speed improvements, and minimum chef quality requirement. Numeric examples in the image do not establish balance values.

- **A — compact recipe facts**: show those three facts below the dish artwork, before Continue.
- **B — art and name only**: retain the selected card's simpler presentation; inspect the facts later in the recipe collection.

Recommendation accepted: A. The facts help the player understand the recipe's restaurant value and eligibility before returning. Unit selling price is not an earning-rate estimate. Question 50 subsequently accepts inspecting a recipe before a separate action, renamed Prepare in Question 54. Question 52 refines preparation-time display in that chef-specific preview to the adjusted time only. The expedition award remains the accepted recipe-wide reveal with base preparation time; exact collection/picker layout remains unresolved.

Options: [A — recipe facts](../design/ui/07a-recipe-facts.png), [B — the existing art-and-name card](../design/ui/06b-recipe-reveal-card.png). [Generation record](../design/ui/07-recipe-facts-prompts.md) includes the exact A edit prompt and the source of the reused B reference.

## Question 8: submarine-upgrade shortcut on expedition results

Accepted: **A — Restaurant only**. Expedition results have one Restaurant continuation; access the submarine upgrade area from the restaurant afterward. The user named that area **Workshop**, replacing the proposed player-facing label "Ship upgrades". Question 9 subsequently accepts its scene doorway.

- **A — Restaurant only**: one clear continuation; access submarine upgrades from the restaurant afterward.
- **B — Restaurant plus Ship upgrades**: keep Restaurant as the primary action and add a secondary shortcut to spend salvage.

Recommendation accepted: A to make the return to restaurant play clear and keep the results concise. The required night recharge remains. Questions 21–26 subsequently resolve the Workshop layout and upgrade interactions; the rejected B image retains its historical "Ship upgrades" label.

Both image proposals show collected salvage, completion bonus, total earned, and a small summary of the already-revealed recipe. This question concerns only the upgrade shortcut. Question 40 subsequently accepts the salvage receipt, including a repeat-catch bonus when earned and a zero completion bonus with explanation on failure or early return. Question 41 accepts outcome-specific titles and different generated backgrounds. Question 42 subsequently accepts receipt-only results, superseding the recipe summary in these historical images. Exact layout remains open; sample amounts and recipe art remain illustrative.

Generated options: [A — Restaurant only](../design/ui/08a-results-restaurant.png), [B — upgrade shortcut](../design/ui/08b-results-upgrade-shortcut.png). [Exact prompts](../design/ui/08-results-shortcut-prompts.md) are saved alongside them.

## Question 9: Workshop entry from the restaurant

Accepted: **B — scene doorway** for the Workshop. The user additionally specified that expedition access is also an entrance in the restaurant scene. Neither destination needs a toolbar entry. Exact landmark placement remains open. Questions 10–14 subsequently resolve the dock appearance, charge-indicator location, and tap behavior; Question 43 resolves readiness feedback.

- **A — fixed Workshop button**: a wrench icon with the Workshop name stays reachable while panning the restaurant.
- **B — scene doorway**: tap a Workshop doorway/sign in the scene to open the same upgrade area.

Original recommendation: A for access while panning. The user selected scene navigation for both destinations. The illustrated doorway is a navigation prop, not a purchased object or an obstacle consuming workable cells. Other toolbar entries and HUD placement in these images are provisional, not additional accepted navigation decisions. The icon-only edit-layer rule remains separate from these live-view navigation controls.

Corrected generated options: [A — toolbar entry](../design/ui/09a-workshop-toolbar.png), [B — scene doorway](../design/ui/09b-workshop-doorway.png). [Exact generation and correction prompts](../design/ui/09-workshop-entry-prompts.md) are saved alongside them. Restaurant layouts are illustrative; the accepted one-cell occupancy model remains authoritative.

## Question 10: expedition entrance appearance

Accepted: **B — visible docked submarine**. The expedition entrance is the yellow submarine moored at a small dock beside the restaurant. Workshop access remains its separate scene doorway. Exact landmark placement remains open; Questions 12 and 14 subsequently resolve ready and charging taps.

- **A — submarine hatch**: a compact porthole hatch and Expedition sign in the restaurant wall.
- **B — visible docked submarine**: the yellow submarine moored in a small scene-side dock, opened by tapping that destination.

Recommendation accepted: B because the visible ship connects the restaurant, recharging, and underwater journey. Positions in these images are illustrative, outside the workable floor. Question 11 subsequently places the charge indicator at the dock, Questions 12 and 14 resolve tap behavior, and Question 43 accepts headlight animation for readiness.

Generated options: [A — hatch](../design/ui/10a-expedition-hatch.png), [B — docked submarine](../design/ui/10b-expedition-dock.png). [Exact prompts](../design/ui/10-expedition-entry-prompts.md) are saved alongside them.

## Question 11: ship-charge indicator location

Accepted: **A — at the dock only**. The restaurant's charge indicator belongs to the dock scenery; remove the persistent top-right charge badge. The player sees it when the dock is in view. Question 43 subsequently accepts a gently pulsing submarine headlight while the local battery stays full. Question 44 adds time remaining to the brief message shown when the charging dock is tapped. Exact charging effects, ready-animation colors/timing, and message wording/duration remain open.

- **A — at the dock only**: a small battery indicator belongs to the dock scenery; remove the persistent top-right charge badge.
- **B — persistent top HUD**: keep the charge badge at the top so it remains visible while panning; the dock remains the scene entrance.

Original recommendation: B for readiness awareness while panning. The user chose the scene-local indicator. Both images show a partially charged battery. Questions 12 and 14 subsequently resolve dock tap behavior; Question 43 resolves the readiness cue. Question 44 accepts on-demand time remaining in the brief charging message.

Options: [A — dock-local indicator](../design/ui/11a-dock-charge-indicator.png), [B — existing top HUD badge](../design/ui/10b-expedition-dock.png). [Generation record](../design/ui/11-charge-location-prompts.md) includes the exact A edit prompt and the reused B reference.

## Question 12: tapping the ready submarine

Accepted: **B with the user's revision — enter the expedition screen, then press Start**. A ready dock tap changes to the expedition start screen without a restaurant launch card. Travel does not begin on that tap; the player must press Start there. Opening the screen is preparation, while Start begins the journey and consumes readiness.

- **A — open a launch card**: show a small Expedition card with Launch and a close control; only Launch starts the journey and spends readiness.
- **B — launch immediately**: one tap on the ready submarine starts the journey and spends readiness.

Original recommendation: A for deliberate departure. The user's revision achieves deliberate departure on the expedition screen rather than through a restaurant popup. The old B image illustrated immediate launch and is superseded on that behavior. Charging-state taps are resolved in Question 14; Start remains the departure action.

Generated options: [A — launch card](../design/ui/12a-launch-card.png), [B — direct launch](../design/ui/12b-direct-launch.png). [Exact prompts](../design/ui/12-ready-dock-tap-prompts.md) are saved alongside them.

## Question 13: expedition start-screen information

Accepted: **A — underwater scene and Start**. The expedition start screen shows the ship on the ocean bed and a prominent Start button, without an equipment summary. Equipment is inspected and improved in the Workshop.

- **A — underwater scene and Start**: a simple view of the ship on the ocean bed, with a prominent Start button.
- **B — add equipment summary**: show the current hull, harpoon, and collector levels above the ship, with the same Start action.

Recommendation accepted: A because equipment is managed in the Workshop and this screen is the final step into play. No new-creature or recipe reward preview appears in either. Sample equipment levels and exact layout are illustrative; the decision concerns the presence of the equipment summary. Start is an overlay before departure and does not establish a footer during active play. The back-arrow button in these historical images is superseded by the scene entrance requested after Question 14.

Generated options: [A — simple start screen](../design/ui/13a-simple-expedition-start.png), [B — equipment summary](../design/ui/13b-equipment-expedition-start.png). [Exact prompts](../design/ui/13-expedition-start-prompts.md) are saved alongside them.

## Question 14: tapping the submarine while charging

Accepted: **B — stay in the restaurant**. Tapping the charging submarine shows a brief local Charging message at the dock. Question 44 subsequently adds time remaining to this message. The expedition start screen becomes accessible when the battery is full.

- **A — open the start screen**: show the underwater preparation view with a disabled Start button and a small Charging status. Charging continues because departure has not begun.
- **B — stay in the restaurant**: show a brief Charging message at the dock. The expedition start screen becomes accessible when the battery is full.

Recommendation accepted: B because the player can watch and manage the restaurant while waiting, with readiness already visible at the dock. Question 43 subsequently accepts the readiness animation. Question 44 accepts time remaining in the brief Charging message; exact wording and message duration remain open.

The user additionally requested a **scene entrance back to the sushi bar on the expedition screen, replacing the back button**. On the preparation screen, tapping that entrance returns to the restaurant without departure or charge consumption. Its airlock appearance is accepted in Question 15. Its availability during active travel is not established by this start-screen decision; early return and pause retain their existing distinct rules.

Generated options: [A — charging start screen](../design/ui/14a-charging-start-screen.png), [B — local dock message](../design/ui/14b-charging-dock-message.png). [Exact prompts](../design/ui/14-charging-dock-tap-prompts.md) are saved alongside them.

## Question 15: sushi-bar return entrance appearance

Accepted: **A — sushi-bar airlock**. A warm doorway built into the scene edge, with a red sushi curtain and Sushi Bar sign, is the tappable return entrance. It replaces the generic back-arrow button on the expedition preparation screen.

- **A — sushi-bar airlock**: a small warm doorway built into the scene edge, with a sushi curtain and Sushi Bar sign.
- **B — surface lift**: a compact underwater lift cabin with cables rising out of view and the same Sushi Bar sign.

Recommendation accepted: A because the doorway directly identifies the destination and follows the Workshop's scene-entrance convention. Tapping it before departure returns to the restaurant without spending readiness. The prop illustrates navigation, without settling additional world lore, exact placement, or active-run early-return controls.

Generated options: [A — sushi-bar airlock](../design/ui/15a-sushi-bar-airlock.png), [B — surface lift](../design/ui/15b-sushi-bar-lift.png). [Exact prompts](../design/ui/15-sushi-bar-entrance-prompts.md) are saved alongside them.

## Question 16: hull durability during an active expedition

Accepted: **A — compact hull meter**. The active-expedition hull indicator uses a submarine icon and a continuous meter showing remaining durability as a proportion of capacity, without a numeric current/maximum readout.

- **A — compact hull meter**: a submarine icon and a continuous meter show remaining hull as a proportion of capacity.
- **B — numeric hull readout**: the same submarine icon accompanies current and maximum hull, such as 70/100.

Recommendation accepted: A because the player mainly needs to judge how much damage they can still withstand while steering. Both occupy the same top-left badge area; this question concerns hull representation. Question 34 subsequently accepts the top status row and separate creature bar below. Sample values and colors are illustrative, without fixing hull capacity, damage, hit count, or warning animations. These active-play images omit the stationary preparation entrance and Start; they do not resolve deliberate early-return controls.

Generated options: [A — compact hull meter](../design/ui/16a-hull-meter.png), [B — numeric hull readout](../design/ui/16b-hull-numbers.png). [Exact prompts](../design/ui/16-hull-indicator-prompts.md) are saved alongside them.

## Question 17: expedition pause-menu layout

Accepted: **A — centered card**. A compact Paused card presents a prominent Resume action and a separate Return early action over the frozen expedition scene.

- **A — centered card**: a compact Paused card presents a prominent Resume action and a separate Return early action over the frozen scene.
- **B — bottom sheet**: the same actions and explanation sit in a panel rising from the bottom, within easier thumb reach.

Recommendation accepted: A because the centered overlay clearly marks the interruption and gives the two actions space away from steering. The world remains visible behind the card. The card explains that early return keeps collected salvage but awards no completion bonus. It adds no retry, repair, upgrade, or new launch action. Resume is resolved in Question 18 and early-return confirmation in Question 19. Question 33 resolves outside taps as leaving the card open. Question 34 places the pause button at upper-right in the top status row.

Generated options: [A — centered card](../design/ui/17a-centered-pause.png), [B — bottom sheet](../design/ui/17b-bottom-pause.png). [Exact prompts](../design/ui/17-pause-menu-prompts.md) are saved alongside them.

## Question 18: resuming expedition control

Accepted: **B — countdown**. Tapping Resume dismisses the pause card and starts a brief visible countdown. The expedition remains frozen until the countdown ends, then resumes automatically without requiring another playfield touch.

- **A — touch to resume**: dismiss the pause card but keep the scene frozen with a small Touch to resume prompt. A new touch in the playfield resumes the journey and anchors a fresh relative steering gesture.
- **B — countdown**: dismiss the pause card and keep the scene frozen through a brief visible countdown, then restart automatically. Steering uses a fresh relative gesture without snapping the ship.

Original recommendation: A for player-controlled readiness. The user selected the countdown, which restarts without an additional playfield touch. Travel, attacks, shooting windows, grace timing, resistance, and capture progress remain frozen through it. The Resume-button touch is consumed by the menu and cannot steer the world. Question 32 accepts preparing a separate steering touch during the countdown, anchoring to its current position when play restarts without a jump or accumulated movement. The illustrated countdown value does not fix its duration. No extra invulnerability, timer refill, or capture progress is awarded. Early-return confirmation is resolved in Question 19 and app-foreground entry in Question 20.

Generated options: [A — touch to resume](../design/ui/18a-touch-to-resume.png), [B — countdown](../design/ui/18b-resume-countdown.png). [Exact prompts](../design/ui/18-resume-transition-prompts.md) are saved alongside them.

## Question 19: early-return confirmation

Accepted: **A — confirm first**. Return early on the pause card opens a centered confirmation card. Cancel restores the Paused card; a second Return early tap ends the journey and opens results.

- **A — confirm first**: replace the Paused card with a Return early? card. Cancel restores the pause card; a second Return early tap ends the journey and opens results.
- **B — end immediately**: one Return early tap ends the journey and opens results, with no confirmation card.

Recommendation accepted: A because ending the current journey also abandons an unfinished catch; an accidental tap cannot be undone by Resume. The scene stays frozen throughout confirmation. Cancel does not resume travel or start its countdown. Confirmed return keeps previously earned rewards and begins night recharge; it adds no retry or recipe guarantee. The confirmation shows salvage retention and the absent completion bonus, and during an ongoing pursuit explains that the unfinished catch earns no recipe. A travel-only version omits that catch-specific line. The B results presentation and sample amount remain illustrative, without settling all result fields.

Generated options: [A — confirmation](../design/ui/19a-confirm-early-return.png), [B — immediate results](../design/ui/19b-immediate-early-return.png). [Exact prompts](../design/ui/19-early-return-prompts.md) are saved alongside them.

## Question 20: reopening an unfinished expedition

Accepted: **A — pause card**. Reopening an unfinished expedition restores the saved scene behind the existing centered Paused card, with Resume and Return early.

- **A — pause card**: restore the saved scene behind the existing centered Paused card, with Resume and Return early.
- **B — frozen scene and Resume**: show more of the saved scene with a small Paused label and a large Resume overlay near the bottom. The existing pause control opens the card to access Return early.

Recommendation accepted: A for consistency with manual pause and immediate access to either continuing or ending the saved journey. The expedition remains frozen until the player presses Resume, then uses the accepted countdown; reopening alone does not restart travel or countdown. It does not consume another charge, refill hull or pursuit timers, start recharge, or grant extra rewards. Return early retains its accepted confirmation. This restores an unfinished journey rather than starting a new expedition.

Options: [A — existing pause card](../design/ui/17a-centered-pause.png), [B — frozen scene with Resume](../design/ui/20b-reopen-resume.png). [Generation record](../design/ui/20-app-reopen-prompts.md) contains the exact B prompt and the reused A reference.

## Question 21: Workshop upgrade selection

Accepted: **A — three upgrade cards**. The Workshop shows Hull, Harpoon, and Collector together so the player can compare all three upgrade choices without selecting ship parts first.

- **A — three upgrade cards**: show Hull, Harpoon, and Collector together, each with its level, a short benefit description, and a salvage-cost Upgrade action.
- **B — select a ship part**: tap a component icon on the illustrated submarine to open its upgrade card. One card is visible at a time.

Recommendation accepted: A because comparing the three choices helps the player decide where to spend limited salvage. Cards show their component, current level, benefit, and salvage cost. Question 22 resolved the benefit as a current-to-next stat preview, Question 23 accepted one-tap purchases, Question 24 resolved insufficient-funds buttons, and Question 25 resolved maximum-level presentation. The accepted separate, capped permanent upgrade tracks use salvage only. Example levels, costs, balance, scene-return doorway, and feedback treatment are illustrative; exact upgrade gains and caps remain open.

Generated options: [A — three upgrade cards](../design/ui/21a-workshop-upgrade-cards.png), [B — select ship parts](../design/ui/21b-workshop-ship-parts.png). [Exact prompts](../design/ui/21-workshop-layout-prompts.md) are saved alongside them.

## Question 22: upgrade benefit detail

Accepted: **B — current to next stat**. Each Workshop card shows a compact before-and-after value for the next improvement to maximum hull, reeling strength, or pickup reach, alongside its current level and salvage cost.

- **A — short descriptions**: More durability, Faster reeling, and Wider pickup reach explain the three benefits without numeric gains.
- **B — current to next stat**: show a compact before-and-after value for maximum hull, reeling strength, and pickup reach.

Recommendation accepted: B because seeing the size of the next improvement helps the player compare its benefit with its salvage cost. These are equipment stats, not restaurant earning rates. All mockup values are illustrative; the decision does not set upgrade gains or balance. The reeling and reach multipliers compare equipment with its base capability, without promising a fixed capture duration or multiplying salvage pickup values. Exact stat units and wording remain tunable. The three-card layout, costs, current levels, and scene were held constant for comparison.

Options: [A — existing short descriptions](../design/ui/21a-workshop-upgrade-cards.png), [B — current-to-next stat preview](../design/ui/22b-workshop-stat-preview.png). [Generation record](../design/ui/22-workshop-benefit-prompts.md) includes the exact B prompt and the reused A reference.

## Question 23: purchasing a Workshop upgrade

Accepted: **A — one-tap purchase**. An affordable Upgrade tap buys exactly one level without a confirmation card, deducts its salvage cost, and updates the balance and that card's level, stat preview, and next cost in place.

- **A — one-tap purchase**: an affordable Upgrade tap buys one level, deducts its salvage cost, and updates that card's level, stat preview, and next cost in place.
- **B — confirm purchase**: the Upgrade tap opens a compact review card showing the selected upgrade, level/stat change, and cost. Upgrade there purchases one level; Cancel returns without a purchase.

Recommendation accepted: A because the cards already show the cost and stat change, keeping repeated upgrades quick. The player remains in the Workshop, and purchases use salvage only. A illustrates the state just after one Hull purchase; B illustrates a still-pending purchase. Updated levels, stats, future costs, and feedback colors are examples, without fixing balance or final upgrade animation. Unaffordable buttons are resolved in Question 24 and maximum-level presentation in Question 25.

Generated options: [A — one-tap purchase](../design/ui/23a-workshop-instant-upgrade.png), [B — purchase confirmation](../design/ui/23b-workshop-confirm-upgrade.png). [Exact generation and correction prompts](../design/ui/23-workshop-purchase-prompts.md) are saved alongside them. The final B review temporarily hides the list behind its confirmation card to avoid duplicated background rows; Cancel restores the three-card Workshop.

## Question 24: insufficient salvage for an upgrade

Accepted: **A — disabled cost button**. When salvage is insufficient, mute and disable Upgrade while keeping its cost legible. The card's current level and current-to-next stat preview remain visible for planning.

- **A — disabled cost button**: mute the Upgrade button while keeping its salvage cost legible. The current level and current-to-next stat preview stay visible for planning.
- **B — tap explains the shortage**: keep the cost button tappable; tapping it shows a brief local message stating how much more salvage is needed, without purchasing anything.

Recommendation accepted: A because the visible balance, cost, and disabled action make affordability clear while preserving comparison across the three cards. A disabled tap makes no purchase and opens no shortage message. Maximum-level tracks are a separate state resolved in Question 25. No image options were generated under the user's updated interview preference.

## Question 25: a completed upgrade track

Accepted: **A — keep the full card**. A maximum-level card retains its full size and position, shows the final level and stat, and replaces Upgrade and its cost with a noninteractive MAX badge. Its next-stat arrow is removed because no further upgrade is available.

- **A — keep the full card**: retain its position and show the final level and stat. Replace Upgrade and its cost with a noninteractive MAX badge; there is no next-stat arrow.
- **B — compact completed row**: collapse it to its component name, final level, and MAX badge. Tap the row to expand its final stat for inspection.

Recommendation accepted: A because there are only three tracks, keeping their positions stable and the player's completed equipment visible. The permanent cap remains, with no further purchase. Exact cap values and spending uses after all tracks are complete remain separate balance decisions. This was a text-only question.

## Question 26: visible equipment improvements

Accepted: **A — visible equipment changes**. At a few selected equipment levels, the submarine gains visible hull-panel, harpoon, or collector improvements that persist in the Workshop, dock, and expedition.

- **A — visible equipment changes**: at a few selected equipment levels, add visible hull-panel details, improved harpoon details, or upgraded collector details. These appearances persist in the Workshop, dock, and expedition.
- **B — fixed submarine appearance**: keep the same ship artwork throughout; show progression through levels, stats, and purchase feedback on the cards.

Recommendation accepted: A because visible equipment gives the player a lasting reminder of where their salvage went. Changes stay within the existing ship footprint, preserving its recognizable yellow silhouette and collision size; they add no new equipment effect beyond the accepted stats. Exact appearance thresholds and artwork remain to be designed. These are equipment-level thresholds, separate from capture milestones that unlock species. This was a text-only question.

## Question 27: steering and firing together

Accepted: **A — independent touches**. One finger can keep steering while another taps the harpoon button. Firing does not cancel or reanchor the steering drag. One-thumb play also works by releasing, firing, and starting a new relative drag without snapping the submarine.

- **A — independent touches**: one finger can continue steering while another taps the harpoon button. Firing does not cancel or reanchor the steering drag. One-thumb play remains possible by releasing the drag, tapping fire, and starting a new relative drag.
- **B — one touch at a time**: the player must release the steering drag before tapping the harpoon button, then touch the playfield again to steer.

Recommendation accepted: A because lining up a shot should not interrupt steering, especially around currents and obstacles. Using two fingers is optional. Question 28 resolves shot timing and hold behavior, and Question 30 resolves button handedness. Touch handoff remains open. This was a text-only question.

## Question 28: tapping or holding the harpoon button

Accepted: **A — one shot per press**. A fresh press fires immediately when the harpoon is ready. Holding does not repeat; another attempt requires another press after cooldown.

- **A — one shot per press**: a fresh press fires immediately when the harpoon is ready. Holding does not repeat; press again after cooldown for another attempt.
- **B — hold to repeat**: pressing fires immediately when ready, then holding fires again whenever the short cooldown ends, until release or the shooting window closes.

Recommendation accepted: A because each shot is a deliberate attempt to align with the creature. The accepted control retains free shots, straight-ahead firing, the short cooldown, and simultaneous steering. A successful hook ends the shooting window and begins the accepted single pursuit attempt. Question 29 resolves cooldown feedback; its exact duration remains open. This was a text-only question.

## Question 29: harpoon cooldown feedback

Accepted: **A — circular recharge ring**. Keep the harpoon button in place, mute its icon during cooldown, and fill a ring around it as it recovers. Restore its active appearance when ready.

- **A — circular recharge ring**: keep the button in place, mute its harpoon icon during cooldown, and fill a ring around it as it recovers. Restore its active appearance when ready.
- **B — dim then ready**: keep the button in place and muted during cooldown, then restore its active appearance when ready, without a progress ring.

Recommendation accepted: A because it makes the next firing opportunity predictable within the existing button footprint. The ring adds no numeric timer or separate HUD element. This decides feedback only, without changing the short cooldown, one-shot-per-press rule, or shooting window. Exact timing, colors, and animation treatment remain open. This was a text-only question.

## Question 30: harpoon button handedness

Accepted: **B — fixed lower-right position**. The contextual harpoon button and its recharge ring stay in the lower-right corner for all players, with no left-side placement setting.

- **A — optional left-side setting**: default to the accepted lower-right position, with a setting that moves the button and its recharge ring to the lower-left. Save the preference across expeditions; the button remains anchored in the chosen corner.
- **B — fixed lower-right position**: use the same lower-right button position for all players.

Original recommendation: A to allow either thumb to reach the firing target. The user selected B, retaining one consistent lower-right position for all players. Contextual shooting-window visibility and the accepted input and cooldown behavior remain unchanged. Question 31 subsequently locks orientation to portrait. Exact insets remain open. This was a text-only question.

## Question 31: game screen orientation

Accepted: **A — portrait-only**, with the user's extension to the sushi bar: "same for sushi bar. Let's lock orientation." Portrait is locked throughout the game, including the restaurant, expedition, Workshop, and related screens. Rotating the device does not switch the game to a landscape layout.

- **A — portrait-only expedition**: keep the expedition in portrait, preserving the tall view of approaching obstacles and the accepted lower-right firing target.
- **B — portrait and landscape**: adapt the expedition scene and HUD to both orientations, keeping automatic travel upward and the harpoon button in the lower-right. The wider view needs decisions about visible route width and forward warning distance.

Recommendation accepted: A because the tall screen gives the player more space to see what is approaching before it reaches the submarine. It also keeps the expedition's layout and viewing distances consistent. The original question concerned the expedition; the user explicitly extended the decision to the sushi bar and locked orientation. Exact device insets and sizes remain open. This was a text-only question.

## Question 32: preparing steering during the resume countdown

Accepted: **A — prepare steering during the countdown**. A new playfield touch can be held ready while the world stays frozen. When the countdown ends, steering anchors to the finger's position at that moment. Subsequent dragging moves the submarine without a jump or accumulated countdown movement.

- **A — prepare steering during the countdown**: a new playfield touch can be held ready. The world stays frozen, and at countdown completion steering anchors to the finger's position at that moment. Subsequent dragging moves the submarine without a jump or accumulated countdown movement.
- **B — require a new touch after the countdown**: touches begun during the countdown do not become steering gestures. The player must lift and touch again after play restarts.

Recommendation accepted: A because the player can prepare their grip before hazards resume. The Resume-button touch remains consumed by the menu; preparation requires a separate playfield touch. This resolves steering readiness only, preserving the frozen countdown, automatic restart, saved timers, and existing relative steering. Countdown duration and touch handoff between steering fingers remain open. This was a text-only question.

## Question 33: tapping outside the pause card

Accepted: **A — Resume button only**. Outside taps leave the Paused card open and the expedition frozen. Pressing Resume starts the accepted countdown.

- **A — Resume button only**: outside taps leave the card open and the world frozen. The player presses Resume to start the accepted countdown.
- **B — outside tap also resumes**: tapping outside dismisses the card and starts the same countdown as Resume. That dismissing touch is consumed by the menu; preparing steering requires a separate playfield touch.

Recommendation accepted: A because a player can examine the frozen scene without accidentally restarting the expedition. This concerns only the Paused card; the accepted early-return confirmation and its Cancel behavior remain separate. The countdown, prepared-steering rule, and return flow remain unchanged. This was a text-only question.

## Question 34: expedition top HUD arrangement

Accepted: **A — status row with creature bar below**. The compact hull meter sits at upper-left, salvage collected this expedition in the center, and pause at upper-right. When shown, the creature's name and resistance bar occupy a separate wide row just below.

- **A — status row with creature bar below**: put the compact hull meter at upper-left, salvage collected this expedition in the center, and pause at upper-right. When shown, the creature's name and resistance bar occupy a separate wide row just below.
- **B — corner clusters with central creature bar**: stack the compact hull meter and collected salvage at upper-left, keep pause at upper-right, and fit the creature's name and resistance bar between the corner clusters.

Recommendation accepted: A because the separate wide creature bar stays readable while ship status keeps consistent positions. The accepted arrangement retains the continuous hull meter without numeric durability and shows collected salvage as an icon and amount, rather than an earning rate or the Workshop's banked balance. This question resolves HUD content and arrangement; Question 35 accepts showing the creature bar when the shooting window opens. Exact insets, sizes, and colors remain open; Question 37 accepts keeping the low-hull warning at the meter. This was a text-only question.

## Question 35: when the creature bar appears

Accepted: **A — when the shooting window opens**. The creature's name and full resistance bar appear as the harpoon becomes available. The bar stays full while the player lines up shots, then drains during pursuit when the ship is within following range.

- **A — when the shooting window opens**: show the creature's name and full resistance bar as the harpoon becomes available. It stays full while the player lines up shots, then drains during pursuit when the ship is within following range.
- **B — after a successful hook**: keep the creature bar hidden during aiming and show its name and full resistance bar when pursuit begins.

Recommendation accepted: A because it clearly introduces the main encounter before the player hooks the creature. The bar always represents remaining resistance, not time until escape. Harpoon shots do not drain resistance, and the existing shooting timeout, single pursuit attempt, and damage setbacks remain unchanged. Exact entrance/exit animation remains open; Question 36 accepts creature animation as the shooting-timeout warning. This was a text-only question.

## Question 36: warning before an unhooked creature escapes

Accepted: **A — creature animation**. Shortly before the shooting window expires, the creature becomes visibly restless, with cues such as quicker fin movements and extra bubbles. At expiry, it swims away. There is no shooting-window countdown in the HUD.

- **A — creature animation**: shortly before escape, show a clearly restless creature animation, such as quicker fin movements and extra bubbles. At expiry, it swims away. Add no shooting-window countdown to the HUD.
- **B — countdown ring by the name**: show a small countdown ring beside the creature's name throughout the shooting window, making the remaining opportunity explicit. At expiry, the creature swims away.

Recommendation accepted: A because expressive creature behavior fits the doodle style and keeps urgency in the scene. The warning animation does not change the creature's movement path or hit area, and the full resistance bar continues to represent capture rather than elapsed time. It does not extend the shooting window, add a second encounter, or change pursuit grace warnings. Exact warning duration, animation, and escape presentation remain open. This was a text-only question.

## Question 37: low-hull warning

Accepted: **A — hull meter only**. While hull is low, the upper-left meter takes on a warning color and gently pulses. The warning is confined to the meter, without a screen-edge tint.

- **A — hull meter only**: the upper-left hull meter takes on a warning color and gently pulses while hull is low.
- **B — meter plus screen-edge tint**: use the same meter warning and add a faint red tint around the screen edges while hull is low.

Recommendation accepted: A because the warning stays at the existing hull indicator and preserves the playfield's colors for hazards and following range. This is visual feedback only, preserving the accepted continuous meter without numeric durability and the existing damage rules. Exact low-hull threshold, colors, pulse timing, and intensity remain open. This was a text-only question.

## Question 38: celebrating a successful catch

Accepted user alternative: **full-screen cutscene, then award dialog**. The user's instruction is: "Play a full screen cut scene animation, then show the award dialog." A successful catch ends active play and presents a full-screen portrait catch cutscene, then opens the award dialog. This supersedes both the proposed brief in-scene animation and the direct transition to rewards.

Original options:

- **A — brief catch animation**: as the successful encounter finishes, reel the creature into the submarine's hatch and show a brief Caught! stamp. Then open the accepted recipe reveal for a first catch, or results for a repeat catch. No additional tap or control is required for this animation.
- **B — straight to rewards**: after the successful encounter finishes, go directly to the recipe reveal for a first catch, or results for a repeat catch.

Original recommendation: A for a visible payoff to the pursuit. The user chose a full-screen cutscene instead. The catch and its recipe or repeat-catch salvage reward are earned when resistance reaches zero; watching the cutscene does not gate retention. It accompanies the accepted automatic journey finish, with no active hazards behind it or added protection during ongoing play. The first-catch award dialog retains the accepted recipe facts and Continue-to-results flow; repeat catches retain their results flow without a new-recipe reveal. The proposed hatch-reeling composition and Caught! stamp are not accepted by this alternative. Question 39 sets a few-second cutscene with no skipping. Exact content, artwork, and timing within that short duration remain open. This was a text-only question.

## Question 39: skipping the catch cutscene

Accepted: **B — always play through**, with the user's short-duration constraint: the full-screen cutscene lasts only a few seconds, so no skipping is needed. It plays automatically without a Skip button, then opens the award dialog automatically.

- **A — Skip button available**: play the cutscene by default, with an explicit Skip button. Either finishing or skipping opens the same award dialog with the already-earned rewards.
- **B — always play through**: show the full cutscene every time, then open the award dialog automatically.

Original recommendation: A to allow players to move on quickly during repeated play. The user instead specified a very quick cutscene of a few seconds and no skipping. Watching still does not gate reward retention; rewards are already earned at capture. Exact timing within the few-second target and animation content remain open. No specific second count has been fixed. This was a text-only question.

## Question 40: salvage detail on expedition results

Accepted: **A — breakdown plus total**. Results list salvage pickups, a repeat-catch bonus when earned, and the completion bonus, followed by a prominent total earned. Failure or early return shows a zero completion bonus with a short explanation.

- **A — breakdown plus total**: list salvage pickups, a repeat-catch bonus when earned, and the completion bonus, followed by a prominent total earned. Show the completion bonus as zero when the expedition failed or ended early, with a short explanation.
- **B — total only**: show one prominent total earned, including any bonuses, without separate receipt lines.

Recommendation accepted: A because it makes the completion and repeat-catch bonuses visible and explains the value of finishing the route. The receipt concerns salvage earned this expedition, not the banked balance or an earning rate. It retains collected rewards on failure and early return, the first-catch recipe reveal, and the single Restaurant continuation. Question 41 accepts outcome-specific titles and backgrounds; Question 42 accepts receipt-only results after the dedicated recipe award dialog. Exact receipt styling remains open. This was a text-only question.

## Question 41: identifying the expedition outcome

Accepted: **A — outcome-specific title**, with the user's addition: "Make sure to have different background(image gen) for different outcome." Use Expedition complete for a finished route, Returned early for a voluntary return, and Hull depleted when the hull reaches zero. Each outcome has a different image-generated background behind the consistent receipt and Restaurant action.

- **A — outcome-specific title**: use Expedition complete for a finished route, Returned early for a voluntary return, and Hull depleted when the hull reaches zero.
- **B — one consistent title**: use Expedition results for all outcomes, with the accepted salvage receipt and completion-bonus explanation conveying the rewards.

Recommendation accepted: A because the heading makes the reason the expedition ended clear. The accepted outcomes use the same receipt structure and single Restaurant continuation. These are presentation labels and backgrounds, not new failure penalties, rescue mechanics, or changes to reward retention. A creature escaping still allows route completion and its completion bonus if the submarine survives. The user explicitly requested image generation for these backgrounds. Question 42 subsequently accepts receipt-only results; exact visual styling remains open.

Generated result-screen studies: [Expedition complete](../design/ui/41a-results-complete.png), [Returned early](../design/ui/41b-results-returned-early.png), and [Hull depleted](../design/ui/41c-results-hull-depleted.png). [Exact prompts and output record](../design/ui/41-results-background-prompts.md) are saved alongside them. The distinct illustrated backgrounds sit behind matching receipts; the 72/18/90 example amounts are not balance decisions. These are static full-screen UI mockups, not isolated runtime background layers or cutscene animation assets. The omitted recipe recaps now match the receipt-only results accepted in Question 42.

## Question 42: recipe recap on results

Accepted: **A — receipt only**. Results show the outcome title, salvage receipt, and Restaurant action. The dedicated first-catch recipe award dialog already shows the recipe and its accepted facts, so results omit a recipe recap.

- **A — receipt only**: results show the outcome title, salvage receipt, and Restaurant action. The dedicated recipe award dialog already shows the recipe and its accepted facts.
- **B — compact recipe recap**: add the new recipe's thumbnail and name beneath the salvage total, before Restaurant. Show this recap only when a new recipe was earned; omit it on repeats or runs without a new recipe.

Recommendation accepted: A because the separate recipe award dialog already celebrates the discovery, keeping the following results compact. The recipe's art, name, fixed price, base preparation time, and minimum chef quality remain in the dedicated award dialog. Continue opens the salvage results, followed by Restaurant. Immediate recipe ownership remains unchanged, without automatic chef assignment or another reward claim. Exact receipt styling remains open. This was a text-only question.

## Question 43: readiness feedback at the dock

Accepted: **B — submarine animation**. When the submarine is fully charged, the dock's battery stays visibly full and the submarine's headlight gently pulses to signal readiness. No ready badge is added.

- **A — ready badge**: the dock's full-battery icon gains a checkmark and a gentle pulse while the submarine is ready.
- **B — submarine animation**: the dock's battery stays visibly full, and the submarine's headlight gently pulses to signal readiness instead of adding a badge.

Original recommendation: A for an explicit phone-size readiness symbol. The user selected B, putting the changing cue into the submarine's scene animation. Feedback stays local to the visible dock. The full battery and headlight cue reflect readiness until departure; opening and leaving preparation does not consume charge. The accepted dock-to-start-screen flow remains, with Start consuming readiness. Exact colors and animation timing remain open. This was a text-only question.

## Question 44: time remaining in the charging message

Accepted: **A — status and time remaining**. Tapping the submarine while charging shows a brief local message with Charging and the time remaining until a full battery. The player stays in the restaurant.

- **A — status and time remaining**: show a brief local message such as Charging — 1:24 left when the dock is tapped.
- **B — status only**: keep the brief local Charging message, with the battery fill conveying progress.

Recommendation accepted: A because on-demand time remaining helps the player decide whether to keep arranging the restaurant or return later. The message stays at the dock, without a persistent HUD timer or change to the fixed charge rate. The example time is illustrative; exact wording and message duration remain open. This was a text-only question.

## Question 45: returning from the Workshop

Accepted: **A — scene doorway**. The Workshop has a visible doorway with the sushi curtain and Sushi Bar sign. Tapping it returns to the existing restaurant with purchased upgrades retained.

- **A — scene doorway**: tap a visible doorway with the sushi curtain and Sushi Bar sign to return to the restaurant.
- **B — back arrow**: tap a compact upper-left back-arrow button to return to the restaurant.

Recommendation accepted: A because it follows the scene-entrance navigation already accepted for the expedition preparation screen. The doorway serves as the Workshop exit rather than a back-arrow button. Question 46 subsequently accepts continuing restaurant service while the Workshop is open; Question 47 accepts recentering on the restaurant floor on return. Exact doorway placement and tap area remain open. This was a text-only question.

## Question 46: restaurant service while the Workshop is open

Accepted: **A — keep service running**. Chefs, belts, and customers continue operating and earning restaurant coins while the player inspects or purchases Workshop upgrades. Passive ship charging continues at its accepted fixed rate, capped at one full battery.

- **A — keep service running**: chefs, belts, and customers continue operating, earning restaurant coins while the player inspects or purchases upgrades.
- **B — freeze service**: pause chefs, belts, and customers until the player returns, preserving their positions and service state.

Recommendation accepted: A because spending time planning upgrades should support the idle loop. The restaurant continues with its committed layout; customer and dish activity can advance before the player returns. The accepted edit-mode pause, expedition charging rules, and offline-income rules remain unchanged. Returning through the Workshop doorway restores the live restaurant with its current savings. This was a text-only question.

## Question 47: restaurant view after leaving the Workshop

Accepted: **B — recenter the floor**. Leaving the Workshop centers the view on the cleared restaurant floor each time. The restaurant shows its current live service and savings at the accepted fixed camera scale.

- **A — restore the previous view**: return to the same camera position the player had before entering the Workshop.
- **B — recenter the floor**: center the view on the cleared restaurant floor each time the player returns.

Original recommendation: A to preserve the player's previous camera position. The user selected B, making the restaurant floor the focus of each Workshop return. Normal swipe panning remains available afterward. Recentering does not restore earlier customer positions, pause service, or change camera scale. Question 48 subsequently accepts the same floor framing for returns from expedition screens. This was a text-only question.

## Question 48: restaurant view after returning from expedition screens

Accepted: **A — recenter the floor**. Both the expedition preparation screen's Sushi Bar doorway and the results' Restaurant action center the restaurant view on the cleared floor, matching the accepted Workshop return.

- **A — recenter the floor**: center the cleared restaurant floor, matching the accepted Workshop return.
- **B — show the dock**: center the dock and submarine so the player immediately sees the charge state.

Recommendation accepted: A because it consistently returns attention to restaurant customers and layout. The accepted fixed camera scale and normal swipe panning remain. Returning before departure still preserves readiness; returning after a run retains the accepted night-recharge flow and earned rewards. This resolves framing for both expedition return paths without changing their different departure/charge states. This was a text-only question.

## Question 49: marking newly discovered recipes in the chef's recipe picker

Accepted: **A — NEW marker**. A newly unlocked recipe has a small NEW badge in the chef's recipe picker until the player inspects that recipe in the restaurant. The expedition award dialog does not clear this restaurant marker.

- **A — NEW marker**: show a small NEW badge on the newly unlocked recipe until the player inspects it.
- **B — ordinary entry**: show it as a normal unlocked recipe; the dedicated award dialog already announces the discovery.

Recommendation accepted: A because it helps the player find the discovery as the recipe collection grows. The restaurant view and current chef assignments remain intact on return; the cue appears when the player opens recipe selection. Inspection clears the marker without requiring recipe selection or cooking. The marker does not override chef quality requirements or automatically choose a chef's recipe. Question 50 subsequently accepts tapping to inspect, followed by a separate action, renamed Prepare in Question 54; exact picker layout remains open. This was a text-only question.

## Question 50: inspecting and assigning a recipe

Accepted: **A — inspect, then Prepare**, with the action renamed in Question 54. Tapping a recipe entry opens a compact preview showing its fixed price, preparation time, and required chef quality. Question 52 subsequently refines the time field to show only the duration adjusted for this chef's speed when eligible, superseding the original base-time proposal for the chef preview. A separate Prepare action applies the recipe to the selected chef when eligible. Inspection alone clears the NEW marker and leaves the chef's current recipe intact.

- **A — inspect, then Assign**: open a compact preview of the recipe's price, base preparation time, and required chef quality. A separate Assign action applies it to the selected chef.
- **B — assign directly**: tapping an eligible recipe entry applies it immediately. A separate information icon opens its details for inspection.

Recommendation accepted: A because recipe changes reset unfinished preparation and replace a held dish, so players should be able to inspect alternatives before committing. Service continues while inspecting. Prepare applies an eligible recipe with the accepted live-change effects; simply inspecting does not reset preparation or replace a held dish. Question 51 subsequently accepts keeping unlocked recipes above the selected chef's quality visible and inspectable, with Prepare disabled. Question 52 accepts adjusted preparation time only for cookable recipes. Question 54 accepts closing the picker and briefly shaking the updated blackboard after Prepare. Exact picker/preview layout and feedback timing remain open. This was a text-only question.

## Question 51: unlocked recipes above the chef's quality

Accepted: **A — visible and inspectable**. Unlocked recipes above the selected chef's quality remain in the picker with their required quality displayed. Tapping opens the recipe preview, with Prepare disabled while the chef is ineligible. Inspection still clears a NEW marker. The action is renamed from Assign in Question 54.

- **A — visible and inspectable**: show them with their required quality. Tapping still opens their recipe preview, with Assign disabled while the chef is ineligible.
- **B — hide from this picker**: show only recipes this chef is qualified to cook; higher-quality unlocked recipes appear once the chef meets their requirement.

Recommendation accepted: A because discoveries remain visible and explain why developing or hiring a stronger chef matters. This applies to already-unlocked recipes, without exposing unknown expedition rewards. Viewing an ineligible recipe does not change chef quality, current preparation, or the chosen recipe. The accepted quality gate still controls Prepare. Exact picker layout and disabled-action styling remain open. This was a text-only question.

## Question 52: preparation time for the selected chef

Accepted: **user alternative — adjusted time only**. The user specified: "Just show the adjusted time. No need to show base." For recipes the selected chef can cook, the preview shows one preparation duration adjusted for that chef's current speed, alongside fixed price and required quality. Omit the base-time value from the chef preview.

- **A — base and chef-adjusted time**: show both, for example Base 10 s and This chef 6 s, alongside price and required quality.
- **B — base time only**: keep the recipe's base preparation time; the chef's speed is inspected through their own controls.

Original recommendation: A to compare base and adjusted preparation times. The user chose a single adjusted value, keeping the chef preview compact and relevant to the selected chef. Effective preparation time excludes waiting to load onto a blocked belt and is not an earning rate. Example seconds remain illustrative; exact values, calculations, labels, and layout remain open. Question 53 subsequently accepts a dash for the time field of ineligible recipes, replacing the original proposed base-time fallback. This choice concerns the chef preview, while the separate expedition award retains its accepted base-time fact. This was a text-only question.

## Question 53: preparation-time field for an ineligible recipe

Accepted: **A — unavailable**. When the selected chef does not meet a recipe's quality requirement, show a dash (—) for preparation time. Keep the fixed price and required quality visible, with Prepare disabled. The action is renamed from Assign in Question 54.

- **A — unavailable**: show a dash for preparation time, keeping price and the required quality visible with Assign disabled.
- **B — current-speed estimate**: show an estimated duration adjusted for this chef's current speed, clearly marked as an estimate, while Assign remains disabled.

Recommendation accepted: A because the chef cannot prepare the recipe yet, and gaining quality also changes speed. The preview gives no hypothetical cooking-time estimate or base-time fallback for an ineligible chef. The recipe remains inspectable, and inspection still clears its NEW marker. Exact field labeling and preview layout remain open. This was a text-only question.

## Question 54: presentation after assigning a recipe

Accepted: **A — return to live restaurant**, with the user's additions: call the recipe action **Prepare**, and briefly shake the chef's blackboard on returning to show the update. Prepare applies the eligible chosen recipe, closes the recipe preview and picker, and reveals live service. The blackboard updates immediately and briefly shakes when the restaurant is shown.

- **A — return to live restaurant**: close the recipe preview and picker so the player sees the chef's updated blackboard and live service.
- **B — keep the picker open**: update it to identify the newly assigned recipe and let the player continue browsing before closing it themselves.

Recommendation accepted: A because the payoff is seeing the new dish enter the belt and customers react. Prepare chooses the chef's ongoing recipe rather than ordering one manually cooked dish. Actual recipe changes retain the accepted preparation/held-dish effects, with service continuing throughout. The brief shake is confined to the updated blackboard and signals the change; it does not move the chef's grid position or delay cooking. Exact shake timing, amplitude, and picker-close transition remain open. This was a text-only question.

## Question 55: recipe-picker presentation on a phone

Superseded by the later large-dialog revision. The picker remains portrait and restaurant service continues while it is open.

- **A — bottom sheet**: browse recipes and inspect a recipe within a panel over the lower part of the restaurant, keeping some live restaurant activity visible above it. Prepare closes the sheet and reveals the blackboard update.
- **B — full-screen picker**: use the whole screen for recipe browsing and inspection. Prepare returns to the restaurant and reveals the same blackboard update.

Original decision: B for a full-screen picker. The user later revised this to a large dialog, superseding only the full-screen presentation. The inspect-then-Prepare interaction, quality gate, adjusted-time-only display, scrolling catalog, fixed lower preview, and two-column cards remain. Exact dialog dimensions and insets remain open.

## Question 56: recipe browsing and selected-recipe preview

Accepted: **A — catalog with a fixed preview**. Scroll recipes in the upper area of the large dialog. Tapping one updates a fixed lower preview with its artwork, facts, and Prepare action. Another recipe can be inspected without leaving the catalog; scrolling does not move the preview.

- **A — catalog with a fixed preview**: scroll recipes in the upper area. Tapping one updates a fixed lower preview with its artwork, facts, and Prepare action, so another recipe can be inspected without leaving the catalog.
- **B — separate detail view**: browsing uses the full screen. Tapping a recipe opens its detail view; return to the catalog to inspect another recipe, or tap Prepare to return to the restaurant.

Recommendation accepted: A because it makes comparing recipes quick and keeps Prepare within thumb reach. Selecting a recipe updates only the preview and clears its NEW marker; the chef keeps preparing the current recipe until Prepare is chosen. Service continues while browsing, and the existing eligibility/time-field rules remain. Question 57 subsequently accepts two-column recipe cards. Exact preview size and device insets remain open. This was a text-only question.

## Question 57: recipe-catalog format

Accepted: **A — two-column cards**. The upper catalog is a scrolling two-column grid of illustrated recipe cards. Each card shows larger dish artwork, the recipe name, and required quality, with a NEW marker where applicable.

- **A — two-column cards**: show larger dish artwork, recipe names, and required quality in a scrolling two-column grid.
- **B — single-column rows**: show smaller dish artwork beside names and required quality in a scrolling list.

Recommendation accepted: A because illustrated dishes can be recognized quickly and feel like a growing collection. The fixed lower preview and Prepare action remain. Every unlocked recipe stays inspectable regardless of the selected chef's quality; the existing quality gate still controls Prepare. Exact card dimensions and artwork remain open. This was a text-only question.

## Question 58: preview when the recipe picker opens

Accepted: **A — current recipe**. When the picker opens, its fixed lower recipe details panel initially shows the selected chef's current recipe and preparation time adjusted for that chef. Opening the picker leaves live service and the chef's recipe intact.

- **A — current recipe**: initially show the recipe the selected chef is already preparing, providing a baseline for comparing alternatives.
- **B — wait for selection**: show a Choose a recipe hint and leave Prepare disabled until the player taps a recipe card.

Recommendation accepted: A because the player immediately sees the current dish and its preparation time for this chef, providing a baseline for comparing alternatives. Tapping another card updates the details panel; Prepare remains the action for changing the chef's recipe. Exact initial-selection styling remains open. Question 59 reviews the action state while the current recipe is selected. This was a text-only question.

## Question 59: action state for the current recipe

Accepted: **A — Preparing status**. When the selected recipe is already the chef's current recipe, show a noninteractive Preparing status in place of the Prepare action. Selecting a different eligible recipe restores Prepare.

- **A — Preparing status**: replace the action with a noninteractive Preparing status. Selecting a different eligible recipe restores Prepare.
- **B — Prepare remains active**: tapping Prepare for the current recipe simply closes the picker without changing preparation progress or a held dish. The blackboard does not shake because no recipe update occurred.

Recommendation accepted: A because it clearly identifies the dish already in production and reserves Prepare for a change. Selecting or viewing the current recipe does not restart cooking. The Preparing status is separate from the disabled Prepare action for an ineligible recipe. This was a text-only question.

## Question 60: leaving the recipe picker without changing a recipe

Accepted: **both A and B**. Provide an icon-only close control in the picker header and support the phone's system back gesture. Either returns to the restaurant with the chef's current recipe, preparation, and held dish unchanged.

- **A — visible close icon**: show an icon-only close control in the picker header. Tapping it returns to the restaurant with the chef's current recipe unchanged.
- **B — system back gesture**: rely on the phone's back gesture to leave the picker, with no close control in the game UI.

Recommendation accepted in part: A makes the exit discoverable across phones, and the user also wants the system back gesture supported. Both exits leave cooking and service unchanged; Prepare remains the separate action for applying a different eligible recipe. This was a text-only question.

## Question 61: marking the current recipe in the catalog

Accepted with the user's refinement: outline the chef's current recipe card instead of adding a badge. Give the card currently selected for inspection a different outline. If both states apply to one card, keep the outlines distinguishable.

- **A — small icon badge**: add a compact, distinctive icon to the current recipe card, visible while that card is in the catalog.
- **B — details panel only**: leave all cards alike; the fixed panel's Preparing status identifies the current recipe when selected.

Recommendation accepted with the user's refinement: outlining the current recipe keeps it identifiable without another badge. Use a different outline for the card selected for inspection, preserving both cues when they apply to the same card. Keep the current-recipe outline distinct from the NEW badge. This was a text-only question.

## Question 62: recipe-card order

Accepted with the user's refinement. Use named recipe-quality tiers in this order: Wood, Steel, Copper, Silver, Gold. Reaching designated chef levels unlocks whole tiers, and each recipe tile is rendered as a board made from its tier's material. Arrange this chef's catalog in three groups: recipes they can cook, from highest to lowest tier; discovered recipes above their highest tier, also from highest to lowest and shown in muted color; then undiscovered recipes shown as silhouettes engraved on their tier boards.

- **A — by required quality**: keep recipes in a stable progression from lowest to highest quality, with NEW markers identifying recent discoveries.
- **B — newest discoveries first**: put recently unlocked recipes at the start, followed by older recipes.

The user's tiered grouping supersedes the original ascending-order options and fine-grained recipe quality grades. Discovered recipes above this chef's tier remain inspectable under the existing rule; undiscovered entries stay unidentified until discovered. Question 63 refines each tier's visual identity to a material board, with unknown dishes engraved as silhouettes on their board. This was a text-only question.

## Question 63: material treatment for undiscovered recipes

Accepted with the user's refinement: recipe tiles use a board made from their tier's material, such as wood or silver. An undiscovered dish appears as a silhouette engraved on its board, revealing the material tier while keeping the dish identity hidden.

- **A — tier color visible**: keep the dish as a silhouette but use its tier color as the card background.
- **B — neutral silhouette**: keep the background neutral so the undiscovered recipe's tier stays hidden.

The user clarified that the material itself forms the board and the silhouette is engraved into it. This communicates the tier while preserving the unknown dish identity. The exact materials and their visual treatment remain art-direction work. This was a text-only question.

## Question 64: tier-unlock levels across chefs

Accepted: **A — shared thresholds**. Every chef unlocks each quality tier at the same chef level. Candidate growth speed and maximum level can still differ.

- **A — shared thresholds**: every chef reaches each tier at the same level; candidate growth and level caps still differ.
- **B — chef-specific thresholds**: each chef's attributes determine the level at which they reach each tier.

Recommendation accepted: A because tier requirements are easier to understand and compare across chefs. Growth speed and capability ceilings still differentiate candidates. This was a text-only question.

## Question 65: capability ceiling and recipe tiers

Accepted: **A — ceiling limits tiers**. A chef whose maximum level is below a shared tier threshold can never unlock that tier.

- **A — ceiling limits tiers**: a chef whose maximum level is below a shared tier threshold can never unlock that tier.
- **B — all chefs reach Gold**: every chef can unlock every tier; their maximum level limits other development but not access to Gold.

Recommendation accepted: A because it makes the capability ceiling meaningful for recipe access and gives hiring choices a clear long-term consequence. This was a text-only question.

## Question 66: showing a chef's tier ceiling in applications

Accepted: **A — show both**. Each job application shows the chef's maximum level and the highest recipe tier reachable at that level.

- **A — show both**: list the maximum level and the highest tier reachable at that level.
- **B — show maximum level only**: let the player infer the reachable tier from the shared thresholds.

Recommendation accepted: A because it makes the long-term value of an applicant clear at a glance, especially when comparing growth speed and level caps. This was a text-only question.

## Question 67: shared level milestones for quality tiers

Accepted: **B — later tiers farther apart**. Use these shared starting thresholds: Wood at Level 1, Steel at Level 3, Copper at Level 5, Silver at Level 8, and Gold at Level 12. They are progression targets for later balance tuning.

- **A — evenly spaced**: Wood at Level 1, Steel at Level 3, Copper at Level 5, Silver at Level 7, Gold at Level 9.
- **B — later tiers farther apart**: Wood at Level 1, Steel at Level 3, Copper at Level 5, Silver at Level 8, Gold at Level 12.

Recommendation accepted: B because the first upgrades broaden the menu quickly while the final tiers remain long-term hiring and development goals. This was a text-only question.

## Question 68: making recipe-board materials distinct

Accepted: **A — color and texture**. Give each tier board a distinct material color and surface texture; players should recognize the tier without relying on a text label.

- **A — color and texture**: give each tier a visibly different material color and grain or surface texture, without relying on a text label.
- **B — shared board with tier label**: keep board appearance mostly uniform and print the tier name prominently on each tile.

Recommendation accepted: A because the material carries the tier identity while texture helps distinguish tiers beyond color alone. This was a text-only question.

## Question 69: discovered dish art on its tier board

Accepted: **A — full-color dish illustration**. Show the recognizable prepared dish in color against the tier-material board; undiscovered dishes remain engraved silhouettes.

- **A — full-color dish illustration**: show the recognizable prepared dish in color against the tier-material board; keep undiscovered dishes as engraved silhouettes.
- **B — engraved dish relief**: reveal the recognizable dish as a detailed engraving in the board material, without separate food colors.

Recommendation accepted: A because colorful plated food makes the recipe collection appetizing and gives a clear visual payoff when a silhouette is discovered. This was a text-only question.

## Question 70: economic promise of higher recipe tiers

Accepted: **A — higher tiers promise higher prices**. Every recipe in a higher tier has a higher fixed selling price than every recipe in lower tiers. Preparation time can still vary and affect throughput.

- **A — higher tiers promise higher prices**: every tier's recipes have higher fixed prices than recipes in lower tiers; preparation times can still vary and affect throughput.
- **B — prices overlap**: a lower-tier recipe may sell for more than a higher-tier recipe, so players compare each recipe's price and preparation time.

Recommendation accepted: A because a newly reached tier gives a clear income-progression reward while preparation time and customer preferences preserve menu choices. This was a text-only question.

## Question 71: preparation time across recipe tiers

Accepted: **B — overlapping prep times**. Preparation time varies independently of tier, so a high-tier recipe can be quick and a lower-tier recipe can be slow. Higher tiers still have higher fixed price bands.

- **A — longer prep bands**: set higher tiers to longer preparation-time ranges, while recipes still vary within each tier.
- **B — overlapping prep times**: let preparation time vary independently of tier, so some high-tier recipes can be quick and some lower-tier recipes slow.

The user chose B to keep preparation time independent of tier. This preserves tier-based price progression while letting recipes vary in production time. This was a text-only question.

## Question 72: price and preparation time within a tier

Accepted: **B — independent within each tier**. Recipe price and preparation time vary separately, so players compare each recipe's combination. The higher-tier price bands remain guaranteed.

- **A — linked within each tier**: slower recipes have higher fixed prices than faster recipes of the same tier.
- **B — independent within each tier**: price and preparation time vary separately, so players compare each recipe's combination.

Recommendation accepted: B because it supports varied restaurant strategies while tier price bands already make progression clear. This was a text-only question.

## Question 73: quality-tier pacing for new expedition catches

Accepted: **A — tier progression**. As expeditions progress, newly caught creatures unlock recipes in tier order, moving from Wood toward Gold. Each expedition still guarantees a new catch until the collection is complete; the exact point when the available tier advances remains open.

- **A — tier progression**: reveal recipes in tier order, beginning with Wood and moving to higher tiers as expedition progress advances.
- **B — mixed-tier discoveries**: any expedition may reveal a recipe from any undiscovered tier, including one the restaurant's chefs cannot yet cook.

Recommendation accepted: A because recipe discoveries stay aligned with chef progression while every expedition still guarantees a new catch. The reward remains unknown before departure. This was a text-only question.

## Question 74: advancing to the next discovery tier

Accepted: **B — expedition milestones**. The discovery pool begins including higher tiers after set numbers of expeditions, even if recipes in the current tier remain undiscovered. The milestone cadence remains open.

- **A — complete the current tier**: reveal recipes from the next tier only after all recipes in the current tier have been caught.
- **B — expedition milestones**: begin revealing the next tier after a set number of expeditions, even if the current tier still has undiscovered recipes.

The user chose B so higher tiers can enter the discovery pool on a schedule without requiring full completion of every lower tier first. The previously accepted expedition rule keeps uncaught species eligible after new species enter the pool, so earlier-tier recipes remain eligible. This was a text-only question.

## Question 75: spacing between tier milestones

Accepted with the user's correction: tier advancement is random, with a one-in-three chance per expedition of adding recipes from the next tier to the catch pool. This uses the pacing of option B without advancing on a fixed three-expedition schedule. Uncaught recipes from earlier tiers remain eligible, and each expedition still guarantees a new creature.

- **A — every two expeditions**: add the next tier after each pair of completed expeditions.
- **B — every three expeditions**: add the next tier after each set of three completed expeditions.

The user clarified that the cadence should be random while retaining option B's one-in-three pacing. This was a text-only question.

## Question 76: handling a long wait for the next tier

Accepted: **B — rising odds**. If the one-in-three roll misses, the chance increases on subsequent expeditions and guarantees the next tier after three consecutive missed rolls.

- **A — independent odds**: keep the chance at one in three every expedition, regardless of previous rolls.
- **B — rising odds**: increase the chance after each miss and guarantee the next tier after three misses.

Recommendation accepted: B because it keeps early progression random while preventing a long unlucky stretch. The exact intermediate odds remain a balance value. This was a text-only question.

## Question 77: which expedition outcomes count for tier rolls

Accepted: **A — every ended expedition**. Completion, early return, and hull depletion each count as one tier-roll attempt.

- **A — every ended expedition**: count the tier roll after completion, early return, or hull depletion.
- **B — completed expeditions only**: early returns and hull depletion do not advance tier odds.

Recommendation accepted: A because an unsuccessful run still counts toward the cycle and does not slow recipe progression further. This was a text-only question.

## Question 78: revealing a newly available recipe tier

Accepted: **A — results notice**. When a tier-roll succeeds, show a brief notice on the expedition results screen that recipes from the new tier can now appear in future expeditions.

- **A — results notice**: add a brief tier-unlocked notice to the expedition results after the run ends.
- **B — restaurant collection only**: add its silhouettes to the recipe collection after returning, without a separate results notice.

Recommendation accepted: A because it makes the random progression event clear while revealing nothing before departure. This was a text-only question.

## Question 79: presenting a tier unlock on expedition results

Accepted: **A — inline notice**. Put the brief tier-unlocked notice on the normal expedition results screen, using its ordinary Continue action.

- **A — inline notice**: show a compact tier-unlocked panel as part of the normal results screen, with the ordinary Continue action.
- **B — separate reveal**: show a dedicated tier-unlock screen that the player must Continue past before seeing expedition results.

Recommendation accepted: A because it communicates the unlock without adding another mandatory tap to the expedition loop. This was a text-only question.

## Question 80: information in the tier-unlock notice

Accepted: **A — tier identity only**. The inline notice shows the tier name and its material-board icon, with a short note that recipes from the tier can now appear on expeditions.

- **A — tier identity only**: show the tier name and its material-board icon, with a short note that its recipes can now be found on expeditions.
- **B — collection preview**: also show the newly available recipe silhouettes in the notice.

Recommendation accepted: A because it makes the progression legible while leaving the collection itself as the place to browse recipes. This was a text-only question.

## Question 81: choosing among eligible uncaught creatures

Accepted: **A — equal chance per creature**. Every eligible uncaught creature across all introduced tiers has the same chance of appearing as the expedition's guaranteed new discovery.

- **A — equal chance per creature**: every eligible uncaught creature, across all introduced tiers, has the same chance.
- **B — equal chance per tier**: choose an introduced tier first, then choose an eligible uncaught creature from that tier.

Recommendation accepted: A because it keeps selection simple and makes every still-eligible recipe feel possible. This was a text-only question.

## Question 82: no uncaught creatures left in the open tiers

Accepted: **A — unlock the next tier**. If the player catches every creature in the currently available tiers before a tier roll succeeds, add the next tier before the next expedition so its new-creature guarantee holds.

- **A — unlock the next tier**: automatically add the next tier before that expedition, bypassing a missed roll if needed.
- **B — allow a repeat encounter**: let the expedition feature a familiar creature until the next tier enters the pool through its normal roll.

Recommendation accepted: A because every expedition is meant to offer a new recipe until the collection is complete. This was a text-only question.

## Question 83: tier rolls after an empty-pool unlock

Accepted: **B — count the fallback as the roll**. An automatic empty-pool unlock replaces that cycle's normal tier roll, keeping it to at most one newly opened tier.

- **A — keep the normal roll**: the expedition can unlock the following tier too if its roll succeeds.
- **B — count the fallback as the roll**: skip that expedition's normal roll so at most one tier opens in this cycle.

Recommendation accepted: B because it prevents one expedition from adding two tiers at once and keeps each new tier's entry into the pool distinct. This was a text-only question.

## Question 84: visual feedback for a satisfied customer preference

Accepted: **A — transform the bubble**. When a customer receives their preferred dish, their thought bubble briefly becomes a positive visual cue and then fades away.

- **A — transform the bubble**: turn it briefly into a clear positive cue, then fade it away.
- **B — show a separate cue**: leave the bubble and show a separate sparkle or approval icon beside it.

Recommendation accepted: A because it confirms the preference match in one compact spot, without adding another persistent element above the customer. This was a text-only question.

## Question 85: visual feedback for each sale

Accepted: **A — local coin pop**. When a customer finishes a dish, show a small coin animation near the customer or dish and update the cash balance.

- **A — local coin pop**: briefly show a small coin animation near the customer or dish as it is consumed; keep the cash balance updated.
- **B — balance tick only**: update the cash balance without a separate sale animation.

Recommendation accepted: A because it makes the customer's behavior and the income event feel connected, without introducing an earning-rate display. This was a text-only question.

## Question 86: amount shown in the sale pop

Accepted: **B — icon only**. The local coin pop is visual feedback; the cash balance communicates the amount earned.

- **A — show the amount**: pair the coin animation with the sale's fixed coin value.
- **B — icon only**: keep the local feedback visual and let the cash balance communicate the amount.

Recommendation accepted: B because repeated sale numbers could clutter a busy restaurant scene, while recipe prices and the balance still show the economic result. This was a text-only question.

## Question 87: size of the chef application set

Accepted: **A — three candidates**. Show three chef applications at once, including each candidate's visible attributes and hiring cost.

- **A — three candidates**: show a small roster of three applicants with their visible attributes and hiring costs.
- **B — two candidates**: keep the choice simpler with only two applicants at a time.

Recommendation accepted: A because comparing three distinct candidates makes their strengths, growth, capability ceilings, and costs meaningfully strategic without presenting a large catalogue. This was a text-only question.

## Question 88: keeping applicants during a refresh

Accepted: **A — replace all three**. Refreshing replaces the complete three-candidate set. Applicants remain available until the player chooses to refresh; none are pinned across refreshes.

- **A — replace all three**: a refresh replaces the entire set; applicants stay available until the player chooses to refresh.
- **B — keep one applicant**: let the player pin one candidate while refreshing the other two.

The user chose A. This was a text-only question.

## Question 89: confirming an applicant refresh

Accepted: **A — refresh immediately**. Tapping the available free Refresh action replaces all three candidates and starts the cooldown, without an extra confirmation.

- **A — refresh immediately**: replace all three candidates on tap and begin the cooldown.
- **B — confirm first**: show a confirmation because the current applications will be lost.

Recommendation accepted: A because refresh is a deliberate player action, the applications do not expire on their own, and an extra confirmation would slow down browsing. This was a text-only question.

## Question 90: placing a newly hired chef

Accepted: **A — add to roster**. Hiring adds the chef as unassigned staff; the player can place them on a floor cell later in edit mode.

- **A — add to roster**: hire the chef as unassigned staff, then let the player place them later in edit mode.
- **B — hire and place**: immediately enter placement so the player chooses a floor cell for the new chef.

Recommendation accepted: A because players can hire even when they do not want to interrupt the restaurant layout, and then place the chef when ready. This was a text-only question.

## Question 91: selecting an unassigned chef for placement

Accepted: **A — drag from People tray**, with the user's additions. The player can drag an unassigned chef from the People layer in either live or edit mode, but can only drop them onto a floor cell next to a belt. Placing the chef immediately opens dish selection. Closing the picker leaves the chef idle.

- **A — drag from People tray**: show unassigned chef portraits in the People layer tray, and let the player drag one onto an empty floor cell.
- **B — choose after tapping a cell**: tap an empty floor cell, then pick a chef from a roster list.

Recommendation accepted: A because it fits the accepted direct-drag editing controls and makes the chef's destination visible before placement. The user specified that placement works in live and edit mode, is restricted to cells next to the belt, and opens dish selection immediately; closing that picker leaves the chef idle. This was a text-only question.

## Question 92: initial dish selection for a newly placed chef

Accepted: **B — no dish selected**. A newly placed chef's dish picker opens without a selected recipe. The player must choose a cookable recipe before Prepare becomes available; closing the picker leaves the chef idle.

- **A — preselect a cookable dish**: highlight the highest-tier recipe this chef can cook; the player still taps Prepare to start cooking.
- **B — no dish selected**: require the player to tap a recipe before Prepare becomes available.

Recommendation accepted: B because a new chef should not appear to have a strategy chosen before the player makes that choice. This was a text-only question.

## Question 93: confirming a permanent firing action

Accepted: **A — confirmation dialog**. Tapping Fire opens a confirmation that names the chef before permanently removing them without a refund.

- **A — confirmation dialog**: tapping Fire opens a clear confirmation naming the chef before removal.
- **B — immediate firing**: tapping Fire removes the chef at once.

Recommendation accepted: A because firing is permanent and nonrefundable, so one confirmation protects against a costly mis-tap. This was a text-only question.

## Question 94: opening staff management

Accepted with the user's direction: tapping the chef button opens the chef panel, where the player can access their roster and job applications. The button's exact placement remains open.

- **A — People control**: use an icon-only People button on the restaurant HUD to open staff management.
- **B — hiring board**: tap a physical job board in the restaurant scene to open staff management.

The user specified a chef button that opens a chef panel. This supersedes the two proposed entry points. This was a text-only question.

## Question 95: opening applicant applications from the chef panel

Accepted with the user's direction: the chef panel has no tabs; a button in it opens a separate popup for job applicants.

- **A — two tabs**: switch between Roster and Applications within the chef panel.
- **B — one scrolling panel**: show the roster and application cards together in one vertical list.

The user specified a button that opens another popup for applicants, with no tabs. This was a text-only question.

## Question 96: replenishing the application set after hiring

Accepted: **A — leave it empty**. Hiring removes that applicant from the set; the remaining two stay available until the player refreshes, with no automatic replacement.

- **A — leave it empty**: the set shows only the remaining two applicants until the player refreshes.
- **B — refill it**: immediately generate a new applicant so three candidates remain available.

Recommendation accepted: A because candidates stay until the player refreshes, and only an explicit refresh should reroll the set. This was a text-only question.

## Question 97: applicants popup after hiring

Accepted: **A — keep it open**. After hiring, keep the applicants popup open with the remaining candidates.

- **A — keep it open**: update it to show the remaining candidates and their current states.
- **B — return to chef panel**: close the applicants popup after hiring.

Recommendation accepted: A because it lets the player compare or hire another remaining candidate without reopening the popup. This was a text-only question.

## Question 98: confirming a chef hire

Accepted: **A — hire immediately**. Tapping Hire deducts the visible cost, adds the chef to the roster as unassigned staff, and removes their application.

- **A — hire immediately**: deduct the shown cost, add the chef to the roster, and remove their application.
- **B — confirm first**: show a confirmation with the chef's cost before hiring.

Recommendation accepted: A because the cost is already shown beside the deliberate Hire action, and a second confirmation adds friction to recruitment. This was a text-only question.

## Question 99: hiring at the staff limit

Accepted: **A — disable hiring**. When the roster is full, show that status and disable Hire until the player expands or fires a chef.

- **A — disable hiring**: show that the roster is full and disable Hire until the player expands or fires a chef.
- **B — replace a chef**: allow hiring only as part of a flow that fires an existing chef.

Recommendation accepted: A because it keeps hiring and firing as separate deliberate actions, especially since firing is permanent and nonrefundable. This was a text-only question.

## Question 100: hiring without enough coins

Accepted: **A — disabled Hire**. Keep the applicant's cost visible and disable Hire until the player has enough coins.

- **A — disabled Hire**: keep the cost visible and disable Hire until the player has enough coins.
- **B — shortage message**: allow a tap on Hire to explain how many coins are missing.

Recommendation accepted: A because it matches the clear disabled-purchase behavior accepted for Workshop upgrades and avoids an extra message in the applicants popup. This was a text-only question.

## Question 101: generating the three applicants

Accepted: **B — deliberately varied set**. Generate each application set so candidates offer noticeably different tradeoffs across strengths, growth, capability ceiling, and cost.

- **A — fully random set**: generate each candidate independently, allowing any mix of strengths, growth, capability ceilings, and costs.
- **B — deliberately varied set**: ensure each set offers noticeably different tradeoffs, such as a fast grower, a low-cost hire, and a high-ceiling chef.

Recommendation accepted: B because each refresh then offers a real comparison across the chef traits that define long-term strategy. This was a text-only question.

## Question 102: showing staff capacity in the chef panel

Accepted: **A — persistent count**. Show the current and maximum staff count in both the chef panel and applicants popup.

- **A — persistent count**: show the current and maximum staff count in the chef panel and applicants popup.
- **B — full-only notice**: show a capacity message only when the player reaches the limit.

Recommendation accepted: A because capacity affects hiring and restaurant expansion, so players can plan before the roster is full. This was a text-only question.

## Question 103: roster information at a glance

Accepted: **A — compact summary**. Each chef row shows the chef's portrait, level, and whether they are assigned or unassigned.

- **A — compact summary**: show the chef portrait, level, and whether they are assigned or unassigned.
- **B — full profile**: show their full attributes, current dish, and capability ceiling in the roster itself.

Recommendation accepted: A because the panel stays scannable as the roster grows, while the detailed traits can appear after selecting a chef. This was a text-only question.

## Question 104: opening a chef's details

Accepted: **A — detail popup**. Selecting a roster chef opens a separate detail popup with their level, attributes, recipe, and management actions.

- **A — detail popup**: open a separate popup with that chef's level, attributes, recipe, and management actions.
- **B — expand the row**: reveal those details inline inside the roster panel.

Recommendation accepted: A because it keeps the roster compact while giving one selected chef room for useful details and actions. This was a text-only question.

## Question 105: placing the chef's Level Up action

Accepted: **A — in the detail popup**. Show the chef's Level Up action beside their level, growth, and next cost.

- **A — in the detail popup**: show that chef's Level Up action beside their level, growth, and next cost.
- **B — in the roster row**: place a Level Up button directly on each chef's summary row.

Recommendation accepted: A because it keeps a roster row compact and puts the cost and level benefit together where the player can review them. This was a text-only question.

## Question 106: confirming a chef Level Up

Accepted: **A — level up immediately**. When affordable, tapping Level Up deducts the visible cost and updates the chef's level and stats without confirmation.

- **A — level up immediately**: deduct the visible cost and update the chef's level and stats on tap.
- **B — confirm first**: show a confirmation with the cost and resulting level before buying.

Recommendation accepted: A because the cost is visible and this matches the direct purchase behavior accepted for Workshop upgrades and chef hiring. This was a text-only question.

## Question 107: chef at their capability ceiling

Accepted: **A — show MAX**. At the chef's maximum level, keep their final level and stats visible, and replace Level Up and its cost with a noninteractive MAX status.

- **A — show MAX**: keep the final level and stats visible, replace Level Up and cost with a noninteractive MAX status.
- **B — remove the action**: hide Level Up and its cost from the popup.

Recommendation accepted: A because it explains that the chef has reached their ceiling instead of making the action appear missing. This was a text-only question.

## Question 108: previewing the next chef level

Accepted: **A — next-level preview**. Show the current-to-next cooking-speed change and note if the level unlocks a recipe tier.

- **A — next-level preview**: show the current-to-next cooking-speed change and note if the level unlocks a recipe tier.
- **B — level and cost only**: show the next level and its cost; let the player infer the speed benefit from the chef's growth attribute.

Recommendation accepted: A because the player can judge the immediate value of a paid upgrade before spending coins. This was a text-only question.

## Question 109: Level Up without enough coins

Accepted: **A — disabled action**. Keep the next-level preview and cost visible, but disable Level Up until the player can afford it.

- **A — disabled action**: keep the next-level preview and cost visible, but disable Level Up until affordable.
- **B — shortage message**: allow a tap on Level Up to explain how many coins are missing.

Recommendation accepted: A because it matches the accepted hiring and Workshop purchase states, while keeping the level-up preview available for planning. This was a text-only question.

## Question 110: placing an object where a customer stands

Revised by the user: **A — block placement** when no empty cell is available to push the customer into. Do not place an object on a customer, which could create an overlap glitch. Customers may still become trapped because of the surrounding layout and show the accepted panic behavior.

- **A — block placement**: keep the object as an invalid placement until a free cell is available.
- **B — allow the trap**: place the object, leaving the customer to react to being trapped until a route or seat opens.

The user first chose B, then corrected this rule to A to prevent object/customer overlap. Trapping through the surrounding layout remains allowed. This was a text-only question.

## Question 111: recovery from a trapped layout

Accepted: **A — wait for the player**. A trapped customer remains in the panic behavior until the player edits the layout or drags them to safety.

- **A — wait for the player**: keep the customer in the panic behavior until the player edits the layout or drags them to safety.
- **B — eventually leave**: after a long wait, let the customer depart even if the layout remains blocked.

Recommendation accepted: A because the trapped customer visibly signals a layout problem and remains available for the player's direct-drag rescue. This was a text-only question.

## Question 112: preserving progress when dragging a customer

Accepted: **A — preserve progress**. Directly dragging a customer moves them while keeping their visit, preference, and eating progress.

- **A — preserve progress**: move the customer but keep their visit, preference, and eating progress.
- **B — reset the visit**: treat the move as a new visit with fresh preference and meal state.

Recommendation accepted: A because direct manipulation should solve a layout problem without erasing the customer's progress. This was a text-only question.

## Question 113: dropping a customer onto a free seat

Accepted: **A — allow direct seating**. Dropping a dragged customer onto an unoccupied seat places them there and resumes their existing visit.

- **A — allow direct seating**: dropping onto a free seat places the customer there and resumes their existing visit.
- **B — floor cells only**: accept drops only on empty floor; the customer must find a seat through normal movement.

Recommendation accepted: A because direct dragging gives the player a clear rescue action while preserving the customer's existing progress. This was a text-only question.

## Question 114: choosing a push destination

Accepted: **A — nearest empty cell**, with the user's exception. Otherwise move the customer to the nearest valid empty cell with a short pushed animation. If the new object is a seat or similar furniture the customer can sit on, seat them on it immediately.

- **A — nearest empty cell**: move them to the closest valid empty cell, using a short pushed animation.
- **B — random empty cell**: choose a random valid empty cell so displacement feels less predictable.

Recommendation accepted: A because the movement remains easy to understand and doesn't send a customer across the restaurant unexpectedly. The user added that placing a seat or other sit-on object under a standing customer seats them immediately. This was a text-only question.

## Question 115: range for direct customer dragging

Accepted: **A — any valid cell**. In the People layer, the player can drop a customer onto any empty floor cell or free seat, even if they could not walk there themselves.

- **A — any valid cell**: allow dropping on any empty floor cell or free seat, even if the customer could not walk there on their own.
- **B — reachable cells only**: restrict drops to cells the customer can reach through the current layout.

Recommendation accepted: A because direct dragging is an accepted rescue tool for customers trapped by their layout. This was a text-only question.

## Question 116: keeping an object selected after moving it

Accepted: **A — keep selected**. After a move, retain the object's selection and local controls so the player can rotate or reposition it again.

- **A — keep selected**: retain the selection and local controls so the player can rotate or reposition it again.
- **B — deselect on release**: clear selection after each move; the player taps again before another adjustment.

Recommendation accepted: A because it supports quick placement corrections without another tap, while the player can still tap another object to change selection. This was a text-only question.

## Question 117: clearing an object selection

Accepted: **A — swipe outside the selection**, with the user's correction. A swipe that starts outside the selected object clears selection and pans in the same gesture; the player does not need a separate tap first.

- **A — tap empty floor**: tap an empty cell to deselect, then swipe to pan.
- **B — tap the object again**: tap the selected object to deselect it, then swipe to pan.

The user refined the interaction: swiping outside the selection deselects and pans at once. This was a text-only question.

## Question 118: repeated placement control

Superseded by the user's new inventory and belt-path placement design. The earlier type-selected tray and repeated-cell-tap proposal is no longer active.

The user specified a shop with stable essentials (including belt tiles and normal chairs) plus changing random goods. Purchased goods enter inventory. In edit mode, a paginated bottom inventory panel lets the player drag items into the scene. Dragging a belt tile places one tile, then its four surrounding cells light and blink slowly; tapping a highlighted neighbor places or connects the next tile and continues the path. The bottom panel then shows rotate and delete controls for the latest belt tile, plus an X to return to inventory and end path placement. Tapping outside the highlighted neighbors ends the current path and returns the bottom panel to inventory, as resolved in Question 119.

For an existing neighboring belt, tapping it during path placement takes that segment into the new path and reorients it, potentially breaking the prior route. Belt direction follows the path through tile center points. A tile can be turned from a left-to-down route into left-to-right only by tapping the right neighbor again.

## Question 119: after tapping outside a belt path

Accepted: **B — return to inventory**. Tapping outside the four highlighted neighboring cells stops the current path and switches the bottom panel back to paginated inventory.

- **A — retain the latest tile controls**: stop path extension but keep the latest belt selected with rotate, delete, and the X to return to inventory.
- **B — return to inventory**: stop path extension and switch the bottom panel back to the paginated inventory.

The user chose B. This was a text-only question.

## Question 120: removing an item from the layout

Accepted: **A — return the item**. Removing a purchased object returns it to inventory without a coin refund. This replaces the earlier full purchase-cost refund rule.

- **A — return the item**: put the object back into inventory, without a coin refund.
- **B — refund the purchase**: keep the earlier full-cost coin refund; the object does not return to inventory.

Recommendation accepted: A because removal returns the purchased good to the same inventory system it came from, without duplicating its value. This was a text-only question.

## Question 121: inventory cost of extending a belt path

Accepted: **A — one item per tile**. Each newly placed tile consumes one belt tile from inventory, and the remaining count is shown. Reusing an existing neighboring belt does not place a new item.

- **A — one item per tile**: place the next tile only when the player has another belt tile in inventory; show the remaining count.
- **B — one item starts a path**: dragging a belt tile starts a path, and connected tiles can be placed without consuming additional inventory items.

Recommendation accepted: A because it makes each newly placed grid cell correspond to a purchased item and keeps belt expansion tied to the inventory economy. This was a text-only question.

## Question 122: running out of belt tiles mid-path

Accepted: **A — keep path mode open**. Show zero belt tiles and disable extensions into empty cells, while still allowing the player to reuse an existing neighboring belt, rotate or delete the latest tile, or exit to inventory.

- **A — keep path mode open**: show zero tiles and disable empty-cell extensions, while still allowing the player to reuse an existing neighboring belt, rotate or delete the latest tile, or exit to inventory.
- **B — return to inventory**: automatically end path placement and switch the bottom panel back to inventory as soon as the last tile is used.

Recommendation accepted: A because it preserves access to the latest tile controls and existing-belt routing. This was a text-only question.

## Question 123: opening the shop while editing

Accepted: **scene entrance in both modes**. The shop entrance is part of the restaurant scene and can be entered in live or edit mode. Returning from the shop preserves the current restaurant and edit state.

The user selected a scene entrance rather than an inventory button or requiring the player to leave edit mode. This was a text-only decision.

## Question 124: refresh timing for changing shop goods

Accepted: **A — after each expedition**. Stable essentials remain available, while the shop's changing goods rotate once per expedition cycle.

- **A — after each expedition**: stable essentials remain available; changing goods refresh once per expedition cycle.
- **B — real-time timer**: changing goods refresh independently of expeditions.

Recommendation accepted: A because it ties the shop's changing offers to the game's main activity cycle. This was a text-only question.

## Question 125: whether edits need to be saved

Accepted with the user's refinement: all edit-mode changes take effect and persist immediately. There is no Save button or separate Done/Cancel transaction. NPCs and the belt remain paused until the player exits edit mode; placement, removal, movement, inventory changes, and purchases are already in effect.

This replaces the earlier provisional Done/Cancel model. The user noted that purchased items already reside in inventory, so placement needs no separate save step. This was a text-only decision.

## Question 126: exiting immediate edit mode

Accepted: **A — explicit Live control**. A play/Live control in the edit toolbar exits editing and resumes NPCs and the belt.

- **A — explicit Live control**: show a play/Live control in the edit toolbar; tapping it exits editing and resumes NPCs and the belt.
- **B — mode toggle**: keep one control that switches between Edit and Live, changing its icon or label with the mode.

Recommendation accepted: A because a clear Live action communicates that exiting resumes the paused restaurant without suggesting that it saves or discards changes. This was a text-only question.

## Question 127: undoing an immediate edit

Accepted: **B — no Undo control**. Edits persist immediately; players correct mistakes with another edit or by returning removed goods from inventory.

- **A — one-step Undo**: show an Undo control after each successful layout action; it reverses only the most recent action and restores its inventory or currency effects.
- **B — no Undo control**: edits remain immediate; the player corrects mistakes by moving objects again or returning removed items from inventory.

The user chose B. This was a text-only question.

## Question 128: dropping an item in an invalid spot

Accepted: **A — snap back**. Return the item to its original position and briefly indicate why the drop was rejected.

- **A — snap back**: return the item to its original position in the inventory or scene and briefly show why the spot is invalid.
- **B — keep holding it**: leave the item attached to the drag until the player finds a valid spot or cancels the drag.

Recommendation accepted: A because it resolves invalid drops immediately and keeps the scene state clear, especially with no Undo control. This was a text-only question.

## Question 129: buying an item without enough coins

Accepted: **A — disable purchase**. The item and price remain visible, but its purchase control is disabled until the player has enough coins.

- **A — disable purchase**: keep the item and its price visible, but disable its purchase control until the player has enough coins.
- **B — allow a failed attempt**: keep the purchase control active; tapping it gives a brief not-enough-coins message without buying the item.

Recommendation accepted: A because it communicates affordability before the player acts and matches the established hiring flow. This was a text-only question.

## Question 130: quantity limits for rotating goods

Accepted: **A — limited stock**. Each rotating offer shows its remaining quantity; purchases reduce that stock until it refreshes after the next expedition.

- **A — limited stock**: each rotating offer has a displayed quantity; buying one reduces stock until the next expedition refresh.
- **B — unlimited stock**: each rotating offer can be purchased as many times as the player can afford before it refreshes.

Recommendation accepted: A because limited copies make each refresh create a clear layout choice, while stable essentials remain available for basic expansion. This was a text-only question.

## Question 131: gameplay effects on rotating furniture

Accepted with the user's refinement: most furniture is appearance-only, while a smaller subset has functional benefits. Those benefits do not change customer patience or preferences; the specific effects are deferred.

- **A — functional variants**: special furniture provides limited gameplay effects or tradeoffs.
- **B — appearance-only variants**: furniture affects customers only through its placement and connection to the belt; special goods change the restaurant's look.

The user chose a mix weighted toward appearance-only items, with a functional subset, and explicitly deferred defining the benefits. This was a text-only decision.

## Question 132: stock limits for stable essentials

Accepted: **A — unlimited essentials**. Belt tiles and normal chairs remain purchasable in any quantity; only rotating goods have stock limits.

- **A — unlimited essentials**: stable essentials stay purchasable in any quantity; only rotating goods have stock limits.
- **B — limited essentials**: stable essentials also have displayed quantities that deplete when bought and refresh after an expedition.

Recommendation accepted: A because essentials remain dependable for basic layout changes, while scarcity stays focused on rotating offers. This was a text-only question.

## Question 133: returning from the shop

Accepted: **A — restaurant doorway**. Show a clear entrance back to the restaurant in the shop scene.

- **A — restaurant doorway**: show a clear entrance back to the restaurant in the shop scene.
- **B — back control**: use a conventional back arrow or button to return to the restaurant.

Recommendation accepted: A because the game's other destination scenes use a visible in-world entrance to return to the Sushi Bar. This was a text-only question.

## Question 134: restaurant service while shopping

Accepted: **A — continue service**. When the player enters the shop from live mode, restaurant NPCs, chefs, belts, and earnings continue. Entering from edit mode preserves the paused edit state.

- **A — continue service**: keep NPCs, chefs, belts, and earnings running while the player shops; edit mode remains paused when returning from an edit-mode visit.
- **B — pause service**: pause restaurant activity for the duration of any shop visit, then resume when the player returns.

Recommendation accepted: A because the shop is part of the idle-management loop, and the restaurant already continues while players manage upgrades and recipes. The user generalized this as a default rule: scene transitions through in-world entrances and non-full-screen popups keep the current simulation running. Explicit Pause and edit mode override the default. This was a text-only decision.

## Recipe-picker presentation revision

The user revised Question 55: present the recipe picker as a large portrait dialog over the restaurant rather than a full-screen picker. Preserve the scrolling two-column catalog, fixed lower preview, Prepare action, close icon, and system back gesture. Restaurant service continues while the dialog is open; exact margins and dimensions remain open.

## Question 135: showing restaurant earnings after an expedition

Accepted: **A — return popup**, refined by the user into a nonmodal text popup. After returning to the restaurant, briefly show the total coins earned while away; the text fades out automatically and requires no dismissal.

- **A — return popup**: after choosing Restaurant from expedition results, show an earnings notice over the live restaurant.
- **B — expedition receipt**: add the restaurant coin total as a separate row on the expedition results receipt, beside the salvage total, before the player returns.

The user chose A, with the refinement that it is a fading text notice rather than a dialog. Show only the total earned during that expedition, never an earning-rate metric. This was a text-only decision.

## Question 136: placement of the away-earnings notice

Accepted: **A — beside the cash balance**. Show a small coin icon and the amount near the restaurant's cash display.

- **A — beside the cash balance**: show a small coin icon and +amount near the restaurant's cash display.
- **B — scene toast**: show a short “While away: +amount” message near the top-center of the restaurant view.

Recommendation accepted: A because it connects the amount directly to the currency balance while keeping the restaurant playfield clear. The notice fades automatically and does not pause service. This was a text-only question.

## Question 137: zero away earnings

Accepted: **A — suppress zero**. Show the away-earnings notice only when the restaurant earned coins during the expedition.

- **A — suppress zero**: show the notice only when the player earned coins, avoiding an unhelpful +0 message.
- **B — always show a notice**: display +0 when no coins were earned so the return feedback is consistent after every expedition.

Recommendation accepted: A because an empty notice adds no useful information, while the normal cash balance remains visible. This was a text-only question.

## Question 138: when away earnings enter the balance

Accepted: **B — add on return**. Restaurant coins earned during an expedition stay pending and are credited when the player returns. The brief away-earnings notice beside the cash balance shows the amount credited.

- **A — add as earned**: increase the balance during the expedition; on return, show how much was added during that run.
- **B — add on return**: hold the earnings separately during the expedition and credit them when the player returns to the restaurant.

The user chose B. This was a text-only question.

## Question 139: closing a belt loop during path placement

Accepted with the user's refinement: existing neighboring belts are reused and reoriented during path placement; tapping the path's starting tile closes the loop.

- **A — close the loop**: connect the new route back to its starting belt when the connection is valid, preserve the closed loop, and end path placement.
- **B — reuse it normally**: treat the starting tile like any other neighboring belt, reorienting it into the active path.

The user chose the existing-belt reuse behavior, with the starting tile acting as the loop-closing point; Question 140 resolves that closure ends path placement. This was a text-only decision.

## Question 140: after closing a belt loop

Accepted: **A — end path placement**. Closing the loop returns the bottom panel to inventory.

- **A — end path placement**: close the loop and return the bottom panel to inventory.
- **B — stay in path placement**: keep the latest tile controls open so the player can keep adjusting the connected belt arrangement.

Recommendation accepted: A because the route is complete, and an automatic end avoids accidental extra connections after the loop closes. This was a text-only question.

## Question 141: tiles left behind when a belt is reused

Accepted: **A — leave them in place**. Other tiles from the old route remain as separate open paths or disconnected segments.

- **A — leave them in place**: remaining belt tiles stay on the floor as separate open paths or disconnected segments.
- **B — remove the disconnected tail**: remove tiles that no longer connect to the original route and return them to inventory.

Recommendation accepted: A because the player chose to move and reorient only the tapped segment; automatically removing additional purchased tiles would be surprising. This was a text-only question.

## Question 142: confirming permanent floor expansion

Accepted: **B — confirmation card**. Tapping a garbage patch opens a small card with its price and a Clear button; confirming spends the visible cost and clears the patch immediately. Unaffordable patches keep their price visible and have a disabled Clear action.

- **A — immediate purchase**: show the patch's price on the scene; tapping an affordable patch clears it immediately.
- **B — confirmation card**: tapping a patch opens a small card with its price and a Clear button; confirming clears it immediately.

Recommendation accepted: B because expansion is permanent and cannot be refunded, and there is no Undo control. This was a text-only question.

## Question 143: tapping outside the recipe dialog

Accepted: **A — outside taps do nothing**. Use the dialog's close icon or the phone's system back gesture to leave; outside taps neither dismiss the picker nor trigger restaurant actions.

- **A — outside taps do nothing**: keep the dialog open; use its close icon or the system back gesture to leave.
- **B — outside taps close it**: tapping the dimmed or visible area outside the dialog dismisses it.

Recommendation accepted: A because it prevents an accidental tap on the live restaurant from closing the picker or triggering an underlying action. This was a text-only question.

## Question 144: restaurant visibility behind the recipe dialog

Accepted: **A — light scrim**. Gently dim the restaurant while keeping customer and belt animations visible.

- **A — light scrim**: gently dim the restaurant so the recipe dialog stands out, while customer and belt animations remain visible.
- **B — full brightness**: leave the restaurant at normal brightness around the dialog, with no dimming layer.

Recommendation accepted: A because it preserves the live scene as readable context while keeping recipe names, prices, and actions easy to focus on. This was a text-only question.

## Question 145: dismissing the expansion price card

Accepted: **A — explicit Cancel**. Provide a Cancel or close control; outside taps leave the card open.

- **A — explicit Cancel**: provide a Cancel or close control; taps outside leave the card open.
- **B — outside tap cancels**: tapping outside the card closes it without clearing the patch.

Recommendation accepted: A because it keeps the permanent-purchase decision deliberate and follows the recipe dialog's explicit dismissal rule. This was a text-only question.

## Question 146: previewing an expansion patch

Accepted: **A — highlight the footprint**, with the user's placement refinement. The selected patch is highlighted and centered in the scene; its price card sits in the bottom half of the screen.

- **A — highlight the footprint**: keep the patch outlined or lit on the restaurant grid while the card shows its price.
- **B — price only**: show the price and action without highlighting the cells; the patch remains identifiable by its scene appearance.

Recommendation accepted: A because the player can verify which cells the permanent purchase affects before confirming. The user added that the card belongs in the bottom half and the scene pans to center the patch. This was a text-only decision.

## Question 147: camera position after the expansion card closes

Accepted: **A — stay on the patch**. Whether the player confirms or cancels, keep the selected area centered.

- **A — stay on the patch**: keep the selected area centered so the player can inspect the cleared floor or continue nearby work.
- **B — restore the prior view**: return to the pan position from before the card opened.

Recommendation accepted: A because the selected expansion remains the active area of work, especially after new cells are added. This was a text-only question.

## Question 148: showing expansion prices before selection

Accepted: **B — show price after selection**. Unselected patches show no prices; tapping one highlights it and opens the bottom-half card with its cost.

- **A — price tags on patches**: show each neighboring patch's cost on the scene before the player taps it.
- **B — show price after selection**: keep the scene clear until a patch is tapped; then show its cost in the highlighted bottom-half card.

Recommendation accepted: B because the confirmation card reveals the selected patch's cost and keeps the floor view uncluttered while the player compares areas. This was a text-only question.

## Question 149: pricing cosmetic floor styles

Accepted: **A — purchase styles**. Alternate floor styles cost restaurant coins.

- **A — purchase styles**: charge restaurant coins for cosmetic floor styles, using the shop or a style catalog.
- **B — free selection**: let the player choose unlocked floor styles without spending restaurant coins.

Accepted: A. Alternate floor styles are purchased with restaurant coins. This is a text-only decision.

## Question 150: where floor styles are sold

Accepted: **B — rotating shop goods**, with the user's clarification that buying a style unlocks it for unlimited floor tiles. The player buys each style once; applying it does not consume a tile item.

- **A — permanent style catalog**: open a floor-style catalog from the Floor layer; styles stay available until purchased.
- **B — rotating shop goods**: include styles in the shop's changing selection, so availability varies between expeditions.

Accepted: B. Floor styles appear in the rotating shop. Each purchase unlocks that style for unlimited floor tiles. This is a text-only decision.

## Question 151: applying an owned floor style

Accepted: **A — paintbrush drag**. In the Floor layer, the player chooses an owned style and drags across floor cells to paint them.

- **A — paintbrush drag**: choose an owned style, then drag across floor cells to paint multiple tiles in one gesture.
- **B — tile-by-tile picker**: tap a floor tile and choose an owned style from its local controls.

Accepted: A because it makes large floor areas quick to decorate on a phone while keeping each tile independently customizable. This was a text-only decision.

## Question 152: painting beneath objects

Accepted: **A — paint beneath objects**. The Floor layer changes the floor cell even when a belt tile, chair, or other placed object sits on top.

- **A — paint beneath objects**: the Floor layer edits the floor cell even when a placed object sits on top.
- **B — empty cells only**: skip cells occupied by objects so the player cannot change hidden floor tiles.

Accepted: A because the layer selector already lets players target the floor independently of layout objects, and it supports continuous patterns beneath furniture. This was a text-only decision.

## Question 153: restoring the default floor

Accepted: **A — default floor in the palette**. Include the original floor appearance as a free style that can be painted over any cells.

- **A — default floor in the palette**: include the original floor appearance as a free style that the player can paint over any cells.
- **B — separate reset action**: provide a reset control that restores selected cells to the original floor.

Accepted: A because it keeps all floor appearances in one consistent palette and lets the same brush paint any style. This was a text-only decision.

## Question 154: brush persistence after a stroke

Accepted: **A — keep the brush active**. Leave the selected style ready for additional strokes until the player changes or exits the floor-painting interaction.

- **A — keep the brush active**: leave the style selected so the player can make several strokes without selecting it again.
- **B — clear after each stroke**: return to style selection after every drag.

Accepted: A because it reduces repeated taps when decorating a larger area while preserving an explicit way to switch styles. This was a text-only decision.

## Question 155: painting one cell

Accepted: **A — tap paints one cell**. A tap applies the active brush to one cell; dragging paints each cell crossed.

- **A — tap paints one cell**: a tap applies the active brush to one cell; dragging paints each cell crossed.
- **B — drag only**: require a drag even when painting a single cell.

Accepted: A because it makes precise one-cell edits easy while retaining fast multi-cell strokes. This was a text-only decision.

## Question 156: exiting floor-painting mode

Accepted: **B — dedicated pan control**. Provide a separate pan icon; using it lets the player pan the scene while keeping the selected floor style ready to paint again.

- **A — tap the selected style again**: deselect the brush and return to the normal floor-layer interaction, where a drag pans the scene.
- **B — dedicated pan control**: keep the brush active and add a separate hand/pan icon to temporarily pan the scene.

Accepted: B. The Floor layer has a dedicated pan control, and the selected style remains ready for the next paint stroke. This is a text-only decision.

## Question 157: using the pan control

Resolved by user clarification: use directional carets at the sides of the screen instead of a toggle or press-and-hold pan icon. Tapping or holding a caret moves the scene in that direction; releasing it resumes painting. A top X exits painting.

- **A — tap to toggle**: tap the pan icon to pan; tap the brush icon to resume painting. Keep the selected style remembered.
- **B — press and hold**: hold the pan icon while dragging, then release to return to painting.

The earlier A/B proposals below are superseded by this clarification.

## Question 158: distance moved by a caret tap

Accepted: **B — larger pan step**. A single tap moves the scene by a larger fixed amount; holding the caret continues moving. The exact distance remains undecided.

- **A — one-cell nudge**: move the camera by one grid cell in that direction; holding the caret continues moving.
- **B — larger pan step**: move the camera by a larger fixed amount per tap; holding continues moving.

Accepted: B. The exact pan distance remains a tuning detail. This was a text-only decision.

## Question 159: carets at the scene boundary

Accepted: **A — hide unavailable directions**. Show only carets for directions where more of the restaurant can be revealed.

- **A — hide unavailable directions**: show carets only for directions where more of the restaurant can be revealed.
- **B — keep all carets visible**: leave each caret in place and show unavailable directions as disabled at the scene boundary.

Accepted: A because it keeps the controls focused on valid movement and avoids an extra disabled-state treatment. This was a text-only decision.

## Question 160: size of a pan step

Accepted custom value: **four grid tiles in the caret's direction**. Holding a caret continues panning in that direction.

- **A — about half a screen**: move far enough to reveal new space while keeping some of the previous view visible as a landmark.
- **B — a full screen**: move by roughly one viewport so the player can cross the restaurant faster.

The offered half-screen and full-screen options were superseded by the user's four-tile value. This was a text-only decision.

## Question 161: motion of a four-tile pan

Accepted: **A — smooth pan**. Glide across the four-tile distance so the scene remains readable while it moves.

- **A — smooth pan**: glide across the four-tile distance, keeping the scene readable while it moves.
- **B — snap pan**: jump directly to the new camera position after the tap.

Accepted: A because a short glide helps preserve spatial orientation without changing the four-tile distance. The exact motion duration remains tuning work. This was a text-only decision.

## Question 162: visibility of the selected floor style

Accepted: **A — keep the palette visible**. Show the selected style and other owned styles in the bottom panel while painting.

- **A — keep the palette visible**: show the selected style and other owned styles in the bottom panel while painting.
- **B — compact brush chip**: collapse the palette to a small selected-style chip, opening the full palette only when tapped.

Accepted: A because the player can switch styles quickly without another panel transition, and the paint surface is still the main focus. This was a text-only decision.

## Question 163: after purchasing a floor style

Accepted: **B — stay in the shop**. The new style joins the owned Floor palette for later use; buying it does not interrupt shopping.

- **A — open the Floor layer**: return to the restaurant, enter edit mode if needed, and open the Floor layer with the new style selected.
- **B — stay in the shop**: add the style to the owned palette and let the player continue shopping or return when ready.

Accepted: B because it preserves the player's shopping flow and treats a style unlock like other purchases; they can apply it later from the Floor layer. This was a text-only decision.

## Question 164: a shop offer for an owned floor style

Accepted: **B — hide owned styles**. Already-owned styles are excluded from later rotating shop selections.

- **A — show as owned**: keep the offer visible with an Owned state and disable its purchase action.
- **B — hide owned styles**: omit already-owned styles from the rotating shop selection.

Accepted: B because a purchased style has no duplicate value, and hiding it keeps the rotating selection focused on available goods. This was a text-only decision.

## Question 165: browsing owned floor styles

Accepted: **A — paginated swatch grid**. Show several style previews at once and use the existing bottom-panel pagination as the collection grows.

- **A — paginated swatch grid**: show several style previews at once and move between pages using the existing bottom-panel pagination.
- **B — horizontal strip**: keep one row of style previews that the player scrolls sideways.

Accepted: A because it reuses the established paginated inventory panel and gives each texture enough room to be recognizable. This was a text-only decision.

## Question 166: order of floor styles

Accepted: **B — newest first**. Put the most recently purchased style first and keep the original floor style at the end.

- **A — default first**: keep the original floor style in the first slot, followed by purchased styles in acquisition order.
- **B — newest first**: put the most recently purchased style first, with the original floor style at the end.

Accepted: B. The newest purchased style appears first, and the original floor style appears last. This was a text-only decision.

## Question 167: entering the Floor layer

Accepted: **A — no brush selected**. Show the palette and wait for the player to choose a style before painting.

- **A — no brush selected**: show the palette and wait for the player to choose a style before painting.
- **B — restore last brush**: automatically select the style used most recently.

Accepted: A because it prevents an unintended paint stroke while the player is first navigating the floor layer. This was a text-only decision.

## Question 168: selecting a style swatch

Accepted: **A — select and paint**. One tap selects the style and immediately activates painting.

- **A — select and paint**: one tap selects the style and activates painting immediately.
- **B — preview first**: one tap previews the style; a separate action confirms it as the active brush.

Accepted: A because the player has already entered the Floor layer and intentionally tapped a style, so another confirmation would slow down a simple action. This was a text-only decision.

## Question 169: destination after exiting painting

Accepted: **A — stay in the Floor layer**. The top X clears the active brush and keeps the style palette open; the player remains in floor editing.

- **A — stay in the Floor layer**: clear the active brush and keep the style palette open, with painting ended.
- **B — return to general edit view**: close the Floor layer and return to the main edit scene.

Accepted: A because it exits the painting action without taking the player away from the floor tools they were using. This was a text-only decision.

## Question 170: floor style in the shop

Accepted: **A — large style preview**. Show a generous sample of the floor pattern with its name and restaurant-coin price.

- **A — large style preview**: show a generous sample of the floor pattern with its name and restaurant-coin price.
- **B — standard goods card**: use the same compact item card as furniture, with a small floor swatch and price.

Accepted: A because the pattern is the product, so a larger preview helps the player judge what they are buying. This was a text-only decision.

## Question 171: pattern scale in the shop preview

Accepted: **A — repeated tile sample**. Show the pattern repeated across several cells so the player can judge how it looks as a floor.

- **A — repeated tile sample**: show a small patch of the pattern repeated across several cells so the player can judge how it looks as a floor.
- **B — single-tile close-up**: use one enlarged tile so the material and detail are easy to inspect.

Accepted: A because a multi-tile sample reveals the pattern's seams, rhythm, and repeat at a glance. This was a text-only decision.

## Question 172: variation between matching floor tiles

Accepted: **A — subtle variations**, with the user's art direction: matching painted tiles should support a shared shader effect that can span across multiple cells, such as one continuous flare across tiles of the same type.

- **A — subtle variations**: use a few compatible tile variants so a large painted area feels less stamped.
- **B — identical tiles**: repeat the same artwork in every cell for a consistent grid pattern.

Accepted: A because small variations suit the doodle art direction and make broad painted areas feel more natural. The user also expects a shared shader treatment across same-type painted tiles, such as a continuous multi-tile flare. This was a text-only decision.

## Question 173: timing of the shared floor effect

Accepted: **A — slow ambient sweep**. Use a subtle continuous flare that moves across matching floor tiles.

- **A — slow ambient sweep**: let a subtle flare move across matching floor tiles as a continuous background effect.
- **B — brief paint response**: show a short flare only when the player paints or changes those tiles.

Accepted: A because a restrained slow sweep can show the material's shared surface treatment without adding another required interaction. Exact speed and intensity remain art-tuning work. This was a text-only decision.

## Question 174: confirming a floor-style purchase

Accepted: **A — buy immediately**. Tapping the purchase action spends the shown price and unlocks the style without a second confirmation.

- **A — buy immediately**: tapping the purchase action spends the shown price and unlocks the style.
- **B — confirm purchase**: show a second confirmation with the style preview and price before spending coins.

Accepted: A because the large preview and visible price already make the purchase clear, and an extra step slows down rotating-shop browsing. This was a text-only decision.

## Question 175: feedback after buying a floor style

Accepted: **A — brief unlock toast**. Show a small message that the style was added to the Floor palette, then fade it out.

- **A — brief unlock toast**: show a small message that the style was added to the Floor palette, then fade it out.
- **B — owned state on the offer**: keep the current offer visible and change it to an Owned state until the shop refreshes.

Accepted: A because it confirms what was unlocked without leaving an owned style in the rotating selection. This was a text-only decision.

## Question 176: placement of the floor-style unlock toast

Accepted: **A — beside the coin balance**. Place the unlock toast near the restaurant-coin balance so the player sees the purchase and updated balance together.

- **A — beside the coin balance**: place it near the restaurant-coin balance so the player sees both the purchase and the new unlock.
- **B — over the offer area**: place it where the purchased style appeared so the feedback is tied to that item.

Accepted: A because the coin balance updates at the same moment, and existing reward feedback uses that area. This was a text-only decision.

## Question 177: unlock toast content

Accepted: **A — name the style**. Show the style name with an unlocked cue, such as “Blue Wave unlocked.”

- **A — name the style**: show the style name with an unlocked cue, such as “Blue Wave unlocked.”
- **B — generic confirmation**: show a short message such as “Floor style unlocked.”

Accepted: A because the player can immediately identify which style entered the palette. This was a text-only decision.

## Question 178: visual cue in the unlock toast

Accepted: **B — text only**. Show the style name and unlocked cue without a pattern image.

- **A — include a swatch**: show a tiny sample of the style beside its name.
- **B — text only**: show the style name and the unlocked cue without a pattern image.

Accepted: B. Keep the unlock toast text-only; the named style is already shown in the purchase preview. This was a text-only decision.

## Question 179: price position for floor styles

Accepted: **B — premium collectibles**. Price floor styles closer to major furniture or expansion purchases so each rotating offer presents a meaningful spending choice. Exact prices remain balance work.

- **A — low-cost customization**: keep styles relatively affordable so players can personalize the restaurant without delaying core upgrades.
- **B — premium collectibles**: price styles closer to major furniture or expansion purchases so each rotating offer is a meaningful spending choice.

Accepted: B. Floor styles are premium collectibles; exact prices remain balance work. This was a text-only decision.

## Question 180: number of floor-style offers per rotation

Accepted: **A — one style at most**. Reserve no more than one rotating slot for a floor style during each shop refresh.

- **A — one style at most**: reserve no more than one rotating slot for a floor style during each shop refresh.
- **B — multiple styles**: allow several floor styles to appear together if the random selection offers them.

Accepted: A because each style is a premium purchase and a single offer leaves room for furniture and other rotating goods. This was a text-only decision.

## Question 181: frequency of floor-style offers

Accepted: **B — optional offer**. A shop refresh may show no floor style even if the player still has styles to unlock; each rotation shows at most one.

- **A — guaranteed offer**: show one unowned floor style every time the shop rotates until all are collected.
- **B — optional offer**: treat floor styles as one possible rotating slot; a refresh may show none.

Accepted: B because rotating the style offer alongside other goods keeps the shop varied and preserves its surprise. This was a text-only decision.

## Question 182: repeating a floor-style offer

Accepted: **A — any unowned style can return**. An unpurchased style may be offered again on the next rotation; there is no recent-offer protection.

- **A — any unowned style can return**: choose from all unowned styles each time a style offer appears.
- **B — avoid recent repeats**: temporarily favor unowned styles that have not appeared in recent rotations.

Accepted: A. Any unowned style remains eligible on each rotation, including the immediately following one. Exact selection odds remain balance work. This was a text-only decision.

## Question 183: price range across floor styles

Accepted: **B — varied prices**. Use different price levels to make some floor styles feel rarer or more premium. Exact prices remain balance work.

- **A — one shared price**: give all floor styles the same restaurant-coin price.
- **B — varied prices**: use different price tiers to make some styles feel rarer or more premium.

Accepted: B. Floor styles may have different price levels reflecting rarity or premium appeal; exact prices remain balance work. This was a text-only decision.

## Question 184: showing floor-style rarity

Accepted: **B — price only**. Show the pattern, name, and coin price without a separate rarity label.

- **A — show a tier marker**: add a small rarity cue to each style offer so players understand why prices vary.
- **B — price only**: show the pattern, name, and coin price without a separate rarity label.

Accepted: B. The shop shows the price without a separate rarity marker. This was a text-only decision.

## Question 185: appearance odds for higher-priced styles

Accepted: **B — price-weighted odds**. Higher-priced floor styles are less likely to appear than lower-priced styles; exact probabilities remain balance work.

- **A — equal chance**: each unowned floor style has the same chance to fill the optional style slot.
- **B — price-weighted odds**: make higher-priced styles less likely to appear than lower-priced styles.

Accepted: B. Higher-priced styles appear less often; exact odds remain balance work. This was a text-only decision.

## Question 186: number of floor-style price bands

Accepted: **B — three bands**. Use low, middle, and high price levels to give the collection more range. Exact prices remain balance work.

- **A — two bands**: distinguish lower-priced styles from premium styles.
- **B — three bands**: use low, middle, and high price levels to give the collection more range.

Accepted: B. Use three internal price levels—low, middle, and high—without a separate rarity badge. Exact values remain balance work. This was a text-only decision.

## Question 187: availability of premium styles

Accepted: **A — available from the beginning**. Any unowned style can enter the rotating shop pool immediately; price and appearance odds establish its rarity.

- **A — available from the beginning**: any unowned style can enter the rotating shop pool immediately, with price and appearance odds setting its rarity.
- **B — progression-gated**: keep some higher-priced styles out of the pool until the restaurant reaches later expansion or level milestones.

Accepted: A because rare, expensive offers can serve as long-term goals without adding another unlock system. This was a text-only decision.

## Question 188: shop slot for a floor style

Accepted: **A — use a rotating slot**. A floor style replaces one of the usual limited rotating goods for that refresh.

- **A — use a rotating slot**: a floor style replaces one of the usual limited rotating goods for that refresh.
- **B — add a separate slot**: keep the normal rotating goods unchanged and show a dedicated floor-style offer as an extra item.

Accepted: A because it preserves the shop's established size and makes a premium cosmetic compete for the same attention as other rotating purchases. This was a text-only decision.

## Question 189: shop slot after buying a floor style

Accepted: **C — mark it owned**. Keep the purchased style's offer visible as Owned until the next shop refresh; exclude it from future selections.

- **A — leave it empty**: remove the offer and keep one fewer rotating good visible until the next refresh.
- **B — refill the slot**: show another random rotating good so the shop stays at its usual item count.
- **C — mark it owned**: keep the offer visible as Owned until the next refresh, while excluding it from future selections.

Accepted: C. The current offer remains in place as Owned until refresh, while later shop selections omit it. This was a text-only decision.

## Question 190: owned style card details

Accepted: **A — replace both with Owned**. Keep the offer preview and name, but replace the price and purchase action with the Owned state.

- **A — replace both with Owned**: hide the price and purchase action, showing only the owned state.
- **B — keep price visible**: leave the price as context, but disable the purchase action and mark the style Owned.

Accepted: A because the player already completed the purchase, so the card can focus on ownership rather than a spent price. This was a text-only decision.

## Question 191: shop refresh after returning from an expedition

Accepted: **A — refresh on return**. Update rotating shop goods as soon as the player returns from the expedition; the refreshed selection is ready the next time they enter the shop.

- **A — refresh on return**: update the shop's rotating selection as soon as the player returns from the expedition.
- **B — refresh on re-entry**: keep the old selection until the player exits the shop and opens it again.

Accepted: A because the shop's rotation is tied to expedition completion, so returning should show the new goods consistently. This was a text-only decision.

## Question 192: signaling refreshed shop goods

Accepted: **A — show a small badge** on the shop entrance until the player opens the refreshed shop.

- **A — show a small badge**: add a compact visual marker to the shop entrance until the player opens the refreshed shop.
- **B — no badge**: let the player discover the new selection by entering the shop.

Accepted: A because the refresh is tied to expedition return, and the entrance can quietly signal that the shop changed. This was a text-only decision.

## Question 193: visual form of the new-goods badge

Accepted: **A — sparkle marker**. Use a small, nonverbal sparkle or glow on the shop entrance to signal new stock.

- **A — sparkle marker**: use a small, nonverbal sparkle or glow to signal new stock.
- **B — item count**: show a number for how many rotating goods changed.

Accepted: A because it signals a change without adding another count for the player to interpret. This was a text-only decision.

## Question 194: when the shop badge clears

Accepted: **A — on shop entry**. Clear the badge as soon as the player opens the refreshed shop.

- **A — on shop entry**: clear the badge as soon as the player opens the refreshed shop.
- **B — after browsing**: keep the badge until the player views each rotating-goods page.

Accepted: A because the shop has been opened and the player can see that its selection changed. This was a text-only decision.

## Question 195: collecting offline restaurant earnings

Resolved by user direction: auto-credit offline earnings when the game reopens. Show only the total in a top toast, then fade it out. Animate the coin count rolling up to the new balance like a slot machine.

- **A — auto-credit and notify**: add the total to restaurant coins immediately and show a brief amount-only message beside the balance.
- **B — claim dialog**: show a return dialog with the amount and require the player to tap Claim.

The earlier A/B presentation options are superseded by this direction. Offline earnings are credited automatically, with a top total toast and a slot-machine-style rolling coin counter. This was a text-only decision.

## Question 196: calculating earnings while the game is closed

Accepted: **A — throughput calculation**. Estimate earnings from the committed layout's production and customer throughput over the elapsed time, without simulating each individual visit.

- **A — throughput calculation**: estimate earnings from the committed layout's production and customer throughput over the elapsed time, without simulating each individual visit.
- **B — catch-up simulation**: advance customer, chef, and belt events through the absence so the restaurant state continues evolving.

Accepted: A because it keeps offline progress predictable and avoids customers losing patience or creating a bad state while the player is away. This was a text-only decision.

## Question 197: customer flow in the offline estimate

Accepted: **A — ongoing customer flow**. Assume new customers continue arriving and filling reachable seats while the player is away.

- **A — ongoing customer flow**: use the restaurant's reachable seating and serving throughput as if customers continue arriving over the absence.
- **B — last-visit customers only**: calculate earnings only from customers who were already in the restaurant when the player left.

Accepted: A because the restaurant's layout and production should continue determining its idle income, without requiring individual customer simulation. This was a text-only decision.

## Question 198: recipe production in the offline estimate

Accepted: **A — use current assignments**. Calculate output from each connected chef's assigned recipe, price, quality, and preparation time.

- **A — use current assignments**: calculate output from each connected chef's assigned recipe, price, quality, and preparation time.
- **B — use average production**: ignore specific dishes and use a general output value per reachable chef and seat.

Accepted: A because recipe and chef choices are central parts of the player's strategy and should matter while idle too. This was a text-only decision.

## Question 199: belt congestion in the offline estimate

Accepted: **A — preserve belt bottlenecks**. Calculate delivery throughput from the actual belt paths, loading points, and customer access.

- **A — preserve belt bottlenecks**: calculate delivery throughput from the actual belt paths, loading points, and customer access.
- **B — idealize belt delivery**: assume dishes reach customers efficiently and calculate mainly from chef output.

Accepted: A because the conveyor design is a core strategy surface, and offline earnings should reward the same effective layout. This was a text-only decision.

## Question 200: customer preferences in the offline estimate

Accepted: **A — include average demand**. Use the recipe mix and average preference demand to estimate how quickly dishes are taken, without simulating individual customers.

- **A — include average demand**: use the restaurant's recipe mix and average preference demand to estimate how quickly dishes are taken.
- **B — treat dishes equally**: assume any dish delivered to a reachable customer is taken at the same rate.

Accepted: A because customer reactions to the menu are part of the player's strategy, while an average demand model avoids simulating individual customers. This was a text-only decision.

## Question 201: transient scene state after offline earnings

Accepted: **A — restore the saved scene**. Keep the last saved customer positions, meal progress, and belt dishes, then resume live simulation after crediting the aggregate offline earnings.

- **A — restore the saved scene**: keep the last saved customer positions, meal progress, and belt dishes, then resume live simulation.
- **B — start a fresh live state**: keep the restaurant layout and staff but reset temporary customers and belt dishes into a clean service state.

Accepted: A. Restore temporary customer and belt state from the latest saved scene; the offline earnings calculation does not individually advance those states. This was a text-only decision.

## Question 202: visual feedback for a satisfied customer preference

Accepted: **A — happy face**. The thought bubble briefly becomes a happy face, then fades.

- **A — happy face**: the bubble becomes a happy-face cue, then fades.
- **B — sparkle or star**: the bubble becomes a compact sparkle cue, then fades.

Accepted: A. Use the happy-face cue inside the existing bubble. This was a text-only decision.

## Question 203: customer animation with the satisfaction cue

Accepted: **A — animate the customer**. Pair the happy-face bubble cue with a short customer reaction.

- **A — animate the customer**: pair the bubble cue with a short smile, bounce, or celebratory gesture.
- **B — bubble only**: leave the customer's body animation unchanged and keep the feedback confined to the bubble.

Accepted: A because the customer is a small pseudo-AI character, and a distinct reaction makes the preference outcome feel more personal. This was a text-only decision.

## Question 204: form of the happy customer animation

Accepted: **A — body bounce**. Give the customer a small celebratory bounce or bob.

- **A — body bounce**: give the customer a small celebratory bounce or bob.
- **B — expression change**: keep their body still and change only their face or eyes to a happy expression.

Accepted: A because it reads clearly at small character scale and gives the preferred-dish moment a satisfying response. This was a text-only decision.

## Question 205: applicant-refresh cooldown while away

Accepted: **A — real-time cooldown**. Let the timer continue while the player is away; exact duration remains balance work.

- **A — real-time cooldown**: let the timer continue while the player is away.
- **B — active-play cooldown**: reduce the timer only while the game is open.

Accepted: A because the cooldown is a limit on repeated refreshes, not a reason to require the player to stay in the game. This was a text-only decision; exact duration remains balance work.

## Question 206: showing the applicant-refresh cooldown

Deferred when the user asked to wrap up the grilling session. No option is selected. The accepted rule is that the free refresh cooldown continues in real time while the app is closed; whether the disabled button displays a countdown remains open.

- **A — countdown on the button**: disable Refresh and show the remaining time directly on the button.
- **B — disabled button only**: keep Refresh disabled and show no remaining-time value.

Recommendation: A because it tells the player when the action will return without making them guess or reopen the panel later. This is a text-only question.

## Wrap-up status

The user wrapped the grilling session after Question 205. The accepted restaurant gameplay, expedition loop, art direction, and UI decisions are consolidated in [gameplay-and-controls.md](./gameplay-and-controls.md), [expedition-gameplay-and-controls.md](./expedition-gameplay-and-controls.md), [art-direction.md](./art-direction.md), and the corresponding interview record. Question 206 is deferred as the only unanswered interview choice. Remaining work is design and balance refinement for prototyping, not a claim that every implementation detail is settled.

## Restaurant HUD revision — 2026-10-09

The user supplied a top-of-screen layout reference and explicitly replaced the physical Shop entrance with a floating button. The current wireframe places the coin count at the upper-left of the viewport and the floating Shop button directly below it. Both remain fixed while the restaurant pans; Shop has no physical corner entrance or floor footprint. This supersedes the Shop entrance placement in Question 123 and the location of the stock cue in Questions 192–193. Those historical answers remain above as the discussion record.

Shop remains accessible in both live and edit mode. Returning preserves the originating restaurant mode and camera panel; the restaurant doorway inside Shop remains unchanged. The small new-stock sparkle moves to the floating Shop button and still clears when Shop opens, as accepted in Question 194. Button press feedback is proposed at 0.97 scale for 70 ms, followed by the existing 200 ms scene crossfade; reduced motion uses a fade without travel.

The earlier direction for styled coin numerals and transparent HUD controls remains current: the supplied layout does not establish cream/yellow backing containers. The physical Workshop hut stays beside the submarine in the middle panel. The reference's other controls do not establish new accepted game systems or navigation.
