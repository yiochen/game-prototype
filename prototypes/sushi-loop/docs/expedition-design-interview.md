# Expedition design interview

Status: core expedition checkpoint accepted by the user on 2026-10-05. The interview is complete through Question 56; unresolved balance, content, and presentation details remain recorded for prototyping.

## Direction accepted before the interview

- A separate submarine expedition mode discovers recipes for the restaurant.
- Forward travel is automatic, up the screen, along a descending ocean-bed canyon viewed from above.
- Lateral movement is freeform, controlled by touching anywhere in the playfield and dragging left or right.
- The environment fills the screen. No dedicated control footer or movement buttons. Destructive firing is deferred; the later creature-capture decision introduces a harpoon interaction whose input is still being resolved.
- Departure does not preview rewards or select a target recipe. Recipes are discovered during expeditions.
- Salvage is the normal expedition reward, including runs without recipe discoveries, and funds submarine improvements.
- Restaurant coins fund restaurant progression. Recipes connect the separate economies; no currency exchange in the accepted direction.
- Doodle is the selected art direction for both modes; see [art-direction.md](./art-direction.md).

## Encounter candidates

The user welcomed varied encounters. Portals, boosts, currents, moving creatures, gates, whirlpools, wreck passages, protection bubbles, and collapsing passages are candidates. Their exact rules and inclusion are not settled. Following a creature is now the accepted recipe-acquisition interaction described below.

## Question 1: lateral steering

Accepted: **A — direct relative drag steering**. The submarine moves sideways with the player's drag and stops its own sideways motion on release; automatic forward travel continues. Touching again starts a new relative drag without snapping the submarine to the finger. Steering does not create residual lateral momentum.

Sensitivity and smoothing remain to be tested. Environmental forces, including possible currents, are separate encounter rules and remain unresolved.

## Question 2: expedition structure

Accepted: **A — finite journey**. Each expedition has a beginning and an extraction point that completes the run. It does not continue indefinitely. Journey length, failure conditions, and any future option to extend a completed journey remain unresolved.

## Question 3: obstacle collisions

Accepted: **A — hull damage**. Damaging collisions consume hull durability while the expedition continues. The run ends in failure when durability reaches zero. Brief protection after a hit prevents one collision from dealing repeated damage. Exact starting durability, damage values, protection duration, and collision recovery remain unresolved.

## Question 4: rewards on failure

Accepted: **A — keep everything collected**. A failed expedition retains collected salvage and earned recipes. The earlier recipe-item wording is superseded by creature capture: catching a creature earns its recipe. Failure stops further collection rather than erasing earned progress. An unfinished pursuit is not yet a catch; treatment of unfinished pursuits remains unresolved.

## Question 5: successful extraction reward

Accepted: **A — completion bonus**. Reaching extraction grants extra salvage in addition to collected rewards. Extraction itself does not award a recipe; recipes are earned through creature capture. Bonus amount and calculation remain unresolved.

## Question 6: repeated expedition routes

Accepted: **A — varied routes**. Familiar, deliberately designed encounter sections appear in different combinations, with changing obstacle and pickup placements. Route construction should preserve readable, navigable paths rather than scatter obstacles arbitrarily. Route length, section selection, difficulty progression, and reward placement remain unresolved.

## Question 7: recipe identity during collection

Superseded by the user's creature-capture design; there is no recipe-item set to reveal or complete.

## Accepted recipe acquisition: creature capture

- Each distinct creature species corresponds to a distinct recipe. Catching a previously uncaught species earns that recipe for the restaurant.
- The player shoots a harpoon, then follows the creature for a while to catch it. Exact aiming, pursuit requirements, duration, feedback, and escape conditions are unresolved.
- Every expedition is guaranteed to contain a creature the player has not caught before while uncaught species remain in the finite catalog. Its appearance is guaranteed; successful capture still requires the player's interaction. The collection-completion exception is accepted in Question 19.
- No recipe-item sets are required. The earlier fragment/item-collection candidate is superseded.
- Departure still does not preview the reward. Encounter timing and repeated-species rewards remain unresolved. After catalog completion, expeditions continue to earn salvage; replay encounter details remain unresolved.

## Question 8: harpoon input

Accepted: **A — contextual floating button**. A small floating harpoon button appears when a catchable creature is nearby. The player can continue drag steering while pressing it. The scene remains full-screen without a dedicated control footer. Button placement, appearance timing, and touch handling remain to be tested.

## Question 9: harpoon aiming

Accepted: **A — straight ahead**. The harpoon fires toward the top of the screen from the submarine's current lateral position. The player steers into alignment and chooses when to shoot. It does not automatically aim toward an off-axis creature. Hit width, shot speed, creature movement, and retry rules remain unresolved.

## Question 10: pursuit requirement

Accepted: **A — stay within following range**. Staying in a forgiving area behind the harpooned creature for enough time completes its catch. The player has room to avoid nearby hazards without precisely matching the creature's lateral path. Range geometry, required duration, and progress feedback remain unresolved.

## Question 11: leaving following range

Accepted: **A — pause with a grace period**. Leaving following range pauses capture progress and starts a brief return window. Returning in time resumes from the accumulated progress; remaining outside too long lets the creature escape. Grace duration and reset behavior across repeated departures remain unresolved. Cable break and retry rules are resolved below.

## Question 12: harpoon shot resources

Accepted: **A — free shots with a short cooldown**, rather than consumable ammunition. The user also specified one chance to capture the creature: if the harpoon cable breaks, it escapes and awards no recipe. A broken-cable pursuit cannot simply resume. This does not remove already collected salvage or previously earned recipes.

Cooldown duration and the boundary of the one-chance rule remain unresolved. The relationship between grace-period expiry, cable breakage, and other possible break causes must be defined separately.

## Question 13: when the capture chance begins

Accepted: **A — on the first successful hit**. Missed shots can be retried after cooldown while the creature remains available. A successful harpoon hit starts that creature's single pursuit attempt. If the cable breaks, that encounter ends without a recipe and the creature cannot simply be hooked again to retry the pursuit.

The initial shooting opportunity is time-limited, as resolved below. Whether the uncaught species returns in a later expedition remains unresolved.

## Question 14: cable break causes

Accepted: **A — separate consequences**, with the user's addition that collisions also set capture progress back a little. A damaging collision reduces hull durability and capture progress but does not directly break the cable. Remaining outside following range beyond the grace period breaks the cable and loses the creature. Hull depletion still ends the expedition. Exact progress loss and collision recovery remain unresolved.

## Accepted addition: limited shooting window

A creature that has not been harpooned swims away after some time, whether the player keeps missing or does not shoot. Misses can be retried after cooldown during this window; the creature does not wait indefinitely. Landing a harpoon hit begins pursuit. Window duration, escape feedback, and encounter scheduling remain unresolved.

## Question 15: capture progress feedback

Accepted user alternative: **a boss-style bar at the top of the screen, accompanied by the creature's name**. This replaces the recommended creature-attached circular cue. The bar communicates the capture state during the encounter. Exact appearance, when it first appears, and its direction remain unresolved.

## Question 16: capture bar direction

Accepted: **A — drain toward capture**. The top boss-style bar displays the creature's remaining resistance. Staying within following range drains it; leaving range pauses it; damaging collisions restore a little resistance, corresponding to the accepted capture-progress setback. An empty bar completes the catch. Exact values and visual treatment remain unresolved.

## Question 17: cable-break warning

Accepted: **A — cable warning**. Outside following range, the cable becomes taut, changes color, and visibly starts fraying as the grace period runs out. Returning to range clears this warning. Grace-period expiry breaks the cable and loses the creature. No separate explicit countdown is selected for this warning. Exact appearance remains to be tested.

## Question 18: creature encounters per expedition

Accepted: **A — one main creature**. Each expedition has one main capture encounter with a previously uncaught species. The rest of the journey focuses on hazards, salvage, and extraction. There are no additional capture attempts against different creatures within the same run. Missed harpoon shots against the main creature remain retryable within its shooting window; its pursuit remains a single attempt.

Encounter timing and the creature catalog's completion behavior remain unresolved.

## Question 19: creature catalog completion

Accepted: **A — finite collection**. Species and associated recipes form a finite catalog. Expeditions guarantee an uncaught creature while any remain; after completing the collection, players can still run expeditions for salvage. This is the explicit exception to the new-creature guarantee. Repeat-species capture encounters after completion are resolved in Question 52.

## Question 20: target expedition duration

Accepted: **A — about one to two minutes** for a normal completed expedition, including navigation, one creature encounter, and extraction. This is the initial playtest target, not a fixed countdown or exact balance constant. Exact timing and the effect of boosts remain unresolved.

## Question 21: creature encounter timing

Accepted: **B — near the end**. The creature is the final major encounter, followed shortly by the end of the expedition. Ordinary navigation and salvage encounters precede it. Exact encounter position, post-encounter route length, and handling an unfinished pursuit at the route end remain unresolved.

The user asked what extraction means: it is the existing label for reaching the route's successful finish and earning the completion bonus. No special return maneuver or extraction animation has been agreed. Already collected salvage and earned recipes do not depend on reaching this point.

## Question 22: journey finish interaction

Accepted: **A — automatic finish**. Reaching the route end completes the expedition automatically; the player does not need to steer into a return beacon. The final creature encounter is followed by a clear completion and reward screen. Visual return presentation and treatment of an unfinished pursuit remain unresolved.

## Question 23: unfinished pursuit at the route end

Accepted: **A — let the encounter resolve**. The final section continues until the creature is caught, escapes, or hull depletion ends the expedition. A surviving submarine then finishes automatically. Forward navigation continues during pursuit; the route end does not cut off a still-valid catch attempt. The one-to-two-minute duration is a target rather than a hard cutoff. Exact section scheduling and any encounter upper limit remain unresolved.

## Question 24: species selection and progression

Accepted: **A — progression-based pool**. Additional species become available as expedition progression advances, introducing harder pursuits and more advanced recipes. The guaranteed creature is selected from eligible uncaught species, and its identity remains unknown before departure. The progression gate, selection weights, and behavior when the currently available pool is fully caught remain unresolved; these must preserve the accepted guarantee until the finite catalog is complete.

## Question 25: unlocking additional species

Accepted: **A — capture milestones**. Catching new species gradually unlocks additional species. Milestones must open the next pool before eligible uncaught species run out, preserving the new-creature guarantee until catalog completion. Submarine upgrades help the player handle harder encounters rather than gating species availability through purchases. Exact milestone thresholds and upgrade effects remain unresolved.

## Question 26: submarine upgrade structure

Accepted: **A — separate permanent upgrade tracks**. Players choose which submarine capabilities to improve with salvage rather than purchasing one level that increases everything together. Survival, capture, and salvage collection are the intended competing priorities. Hull, harpoon, and collection equipment are candidate tracks; exact effects, costs, and caps remain unresolved.

## Question 27: hull condition between expeditions

Accepted: **A — fresh start**. Every expedition begins at full upgraded hull durability without a repair charge. Hull damage does not carry over between expeditions. Salvage is available for permanent improvements rather than mandatory repairs. Exact hull capacity and upgrade gains remain unresolved.

## Question 28: main harpoon upgrade effect

Accepted: **A — reeling strength**. Harpoon upgrades drain creature resistance faster while the submarine remains within following range, shortening the pursuit. They do not imply an increased hit area or automatic aiming. Exact drain rates, costs, and caps remain unresolved.

## Question 29: collection equipment effect

Accepted: **A — attraction range**. Collection equipment increases the distance from which nearby salvage pickups are pulled toward the submarine. The range should have a modest cap that preserves steering and route choices. This does not imply multiplying each pickup's value. Exact range, costs, caps, and interaction with temporary power-ups remain unresolved.

## Question 30: boost behavior

Accepted: **A — protected boost**. A boost temporarily increases forward speed and prevents collision damage while the player can still steer and collect salvage. Duration, activation, and interaction with creature encounters remain unresolved.

## Question 31: boosts during pursuit

Accepted: **A — travel only**. Boost encounters belong to ordinary travel and their effects end before the creature encounter begins. They do not apply during aiming or pursuit. This supersedes the recommendation to accelerate the submarine and creature together. Exact boost duration and placement remain unresolved.

## Question 32: portal behavior

Accepted: **B — separate bonus passage**, with the user's addition that a strong current pushes the submarine through it without requiring maneuvering. The player watches the ship collect salvage along the way, then it rejoins the main route. This replaces the same-route paired-exit recommendation. Passage length, steering override, collision treatment, and availability during creature encounters remain unresolved.

## Question 33: portal entry choice

Accepted: **A — optional entry by steering**. The player chooses to reach a visible portal entrance, then watches the current carry the submarine through its bonus passage. Entry is not an unavoidable scripted transition. Portal placement and competing route rewards remain unresolved.

## Question 34: portals during creature encounters

Accepted: **A — travel only**. Portals and their bonus passages occur before the creature appears. They are not offered during aiming or pursuit, and do not provide an abandonment option within the final encounter. Passage safety and return placement remain unresolved.

## Question 35: bonus passage safety

Accepted: **A — safe ride**. The strong current carries the submarine through the bonus passage while it collects salvage without hull damage. Entry does not create a hull-for-salvage trade. Passage length, salvage amount, and return placement remain unresolved.

## Question 36: ordinary current behavior

Accepted: **A — sideways push**. Visibly flowing water causes lateral drift on the main route. The player can countersteer or ride the flow toward pickups. This is an environmental force separate from the submarine's direct drag steering and distinct from the automatic bonus-passage current. Current strength and duration remain unresolved. Creature-created currents during pursuit are accepted below; unrelated ambient current placement during pursuit remains unresolved.

## Question 37: pursuit variety between species

Accepted: **A — different movement patterns**, with species sharing reusable pattern families. Candidate movements include smooth weaving, short lateral dashes, and pausing before changing direction. Exact patterns and difficulty remain unresolved.

## Accepted addition: creature-generated hazards and attacks

Some species also create obstacles or attack during the encounter. User examples include breaking a large reef into smaller scattered obstacles, creating swirls or currents, and direct attacks such as an eel discharging electricity. These make species differ through both movement and encounter interactions. Exact behavior assignments, attack shapes, scheduling, and secondary effects remain unresolved. Damaging hits use the existing hull-loss and capture-setback rules; they do not imply a new automatic cable-break rule.

## Question 38: attack warning presentation

Accepted: **A — area warning plus animation**. Upcoming attacks show their affected area briefly before activation, alongside a readable creature or environmental windup. Examples include an eel charging before its discharge, reef cracking before fragments scatter, and a swirl forming before it pulls. Exact warning duration and visual language remain unresolved.

## Question 39: aimed attack target timing

Accepted user alternative: **no aiming at the submarine** for the proposed eel discharge. The creature selects a vertical strip, warns the player through the accepted affected-area cue and windup, then shoots along that strip. The player avoids the strip. It does not track the submarine. Strip selection, width, duration, and scheduling remain unresolved.

## Question 40: attack strip versus following range

Accepted: **A — safe dodge within following range** for the standard strip attack. The strip leaves a safe position in the following area, so the player can dodge while continuing to capture. Avoiding that strip alone does not require leaving range. Exact strip width, attack duration, and interaction with other hazards remain unresolved.

## Question 41: species selection after a failed catch

Accepted: **B — random uncaught species**. Each expedition selects from the eligible uncaught pool. A failed species remains eligible for a later encounter rather than forcing a guaranteed rematch or becoming permanently unavailable. The particular reward remains unknown before departure. Exact selection weights and any anti-repetition rules remain unresolved.

## Question 42: start of creature attacks

Accepted: **A — after being hooked**. Creature attacks and creature-generated hazards begin only after a successful harpoon hit starts pursuit. Before that, the player aligns and shoots within the limited shooting window. Ordinary route hazards may remain present during aiming. Initial creature movement and first-attack timing remain unresolved.

## Question 43: damaging-hit movement response

Accepted: **A — preserve control**. Damaging hits apply hull damage and capture setbacks with a hit animation and brief protection, without forced sideways knockback. Lateral steering remains responsive. Exact visual feedback and protection duration remain unresolved.

## Question 44: expedition launch availability

Accepted direction: **restaurant-gated launches**, superseding the free-launch recommendation. The user wants roughly one sushi-bar run followed by one expedition, so players engage with both modes instead of playing only the submarine game. The narrative explanation, meaning of a sushi-bar run, unlock condition, and ready-launch storage remain unresolved.

The restaurant is already defined as persistent. A restaurant run therefore needs a service-round definition; it must not silently introduce resets to the layout, staff, upgrades, or savings. Passive time or background sales alone may fail to achieve the user's desired alternation.

## Question 45: restaurant service round

Superseded by the user's day/night proposal. The crew-provisioning story is rejected: ordinary customers remain the restaurant's guests, and the restaurant owner operates the submarine. The desired cycle is sushi service at night and an expedition by day. The night session needs an ending condition that earns launch readiness without spending restaurant coins; every expedition must require another restaurant session afterward.

## Recharge-cycle candidate

The user proposed ship recharging as the reason for alternating sessions. A candidate story is a kitchen heat-recovery charger that refills the submarine's battery during night service. Restaurant coins remain available for restaurant development; charge is launch readiness rather than another upgrade currency.

Proposed flow, not yet fully accepted: night service fills one battery; a full battery completes the service goal and enables one day expedition; any expedition outcome returns the owner to night service with launch charge exhausted. No extra launches are stockpiled and charge is not earned while diving. Whether a full battery forces the night view to end, how offline charging works, and how this cycle preserves the accepted idle-income behavior remain unresolved. Day/night is proposed as an in-game phase presentation, not a real-world clock restriction.

## Question 46: source of ship charge

Accepted: **B — elapsed night-service time**. Ship charge fills at a fixed rate during night service, independently of restaurant sales or throughput. Restaurant coins are not spent on charging. This replaces the recommendation to generate charge from dishes sold. Exact recharge duration remains unresolved.

Dockside overnight charging is a candidate narrative that fits the fixed rate more directly than the earlier kitchen heat-recovery proposal. The mode cycle and charging's offline behavior still need to be resolved.

## Question 47: offline charging

Accepted: **A — offline night charging**. During offline absence in the night phase, charge advances up to one full battery. Additional time does not stockpile launches. The player can return to restaurant income and at most one ready expedition; every expedition requires another recharge afterward. Exact recharge duration and phase-transition rules remain unresolved. Charging during a suspended expedition has not been accepted.

## Question 48: full battery and mode transition

Accepted: **A — ready when the player chooses**. A full battery makes an expedition available, but the player can continue managing the restaurant and choose when to launch. Charging completion does not automatically switch modes or stop restaurant play. Each launched expedition still exhausts launch charge and requires another night recharge. Exact ready-state feedback remains unresolved.

## Question 49: interrupted expeditions

Accepted: **A — pause and preserve**. Closing or backgrounding the app preserves the current expedition for later resumption. Travel, attacks, shooting windows, pursuit grace, and capture state do not advance while suspended. Ship charging waits until the return to night service. Restaurant offline income continues independently. Exact resume presentation remains unresolved.

## Question 50: intentional early return

Accepted: **A — allow early return**. The player can deliberately end an expedition and return to night service, keeping earned salvage and recipes without receiving the completion bonus. An unfinished pursuit earns no recipe. Another launch requires a fresh recharge. This differs from backgrounding the app, which preserves the paused expedition. Exit presentation remains unresolved.

## Question 51: initial recharge duration

Accepted: **A — about two to three minutes** to refill an empty battery, as the initial playtest target. This pairs with the one-to-two-minute expedition target. Charging remains independent of restaurant performance and continues offline during night service up to one full battery. The exact duration remains balance work rather than a final constant.

## Question 52: encounters after catalog completion

Accepted: **A — repeat captures**. After every species has been caught, expeditions retain a final main encounter with a familiar species. Successful repeat catches award extra salvage instead of unlocking another recipe. This preserves the role of reeling upgrades and the expedition's climax. Species selection and catch-bonus amounts remain unresolved.

## Question 53: difficulty versus ship upgrades

Accepted: **A — upgrades make existing encounters easier**. Encounter difficulty does not automatically scale with ship strength. Better equipment improves survival, reeling, and collection against existing challenges; capture milestones introduce harder species and patterns. Exact species difficulty and travel-section tuning remain unresolved.

## Question 54: initial ship charge

Accepted: **A — full initial battery**, with a guided opening specified by the user. First guide the player through basic restaurant operation, then introduce the expedition. Full initial charge supports that sequence rather than replacing the restaurant introduction. Every launched expedition afterward requires the normal recharge. Exact tutorial steps remain unresolved.

## Guided opening candidate

Proposed sequence: observe a chef preparing sushi, a customer taking it, and the coin reward; perform a small layout edit and a restaurant upgrade; launch the first day expedition; learn drag steering, salvage collection, harpooning, and pursuit; return to night service and assign the newly unlocked recipe. These steps are a candidate outline rather than individually accepted requirements. The opening should demonstrate the connection between the two modes through play.

## Question 55: first expedition lesson protection

Accepted: **A — protected introduction**. The first expedition lesson pauses for explanations and allows recovery from mistakes so the player can complete the first catch while learning. The player still performs steering, aiming, and pursuit. The first creature is not permanently lost during instruction. Subsequent expeditions use the normal failure and one-chance capture rules. Exact tutorial protections and duration remain unresolved.

## Question 56: submarine upgrade caps

Accepted: **A — finite caps**. Every permanent submarine upgrade track has a maximum level, giving the player a fully equipped ship to work toward. Encounter difficulty remains independent of those upgrades. Exact caps, costs, and benefits remain balance work. Additional spending uses after all tracks are completed have not been defined.

## Core checkpoint review

The user accepted **A — accept the checkpoint** on 2026-10-05. The consolidated [expedition gameplay and controls](./expedition-gameplay-and-controls.md) document is now the agreed expedition baseline. Exact balance values and extra content details remain listed as open work rather than inferred rules.

## Remaining branches

The core checkpoint is accepted. Major loop, controls, capture, progression, replay, and interruption decisions are resolved above. Costs, durations, ranges, damage values, milestone thresholds, content patterns, and presentation details remain balance and playtest work, as listed in the consolidated document. Resolve any further decisions one at a time rather than treating that list as a questionnaire.


## Later revision: restaurant simulation during expeditions

The restaurant continues running in the background during an expedition, with customers, chefs, and belts progressing. Restaurant coins earned during the expedition stay pending and are credited when the player returns. The expedition Pause card freezes the dive itself, while restaurant service continues independently. Closing or backgrounding the app preserves the dive and uses the established offline-income rule for the restaurant. On return, the credited total appears beside the cash balance as a brief text notice that fades automatically; it is suppressed when the total is zero. This extends Question 49's earlier offline-income decision.
