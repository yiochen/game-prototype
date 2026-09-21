# One More Card — Suit sequences (v23)

Run `npm run dev` from the repository root, then open `/prototypes/one-more-card/`. This game is self-contained in this directory, with a separate engine, UI, balance configuration, and tests.

Imported from `life-sim/experiment` at v23. Play the current prototype at https://game-prototypes-yiochen.netlify.app/prototypes/one-more-card/. The previous deployment remains at https://midnight-noodle-yiochen.netlify.app/experiment/; it is not connected to this new repository.

## Tuning

**Edit [`balance.js`](balance.js)** for starting cash, offer size, suits, family and card-type weights, prices, fixed link values, Mystery outcomes and odds, Growth strengths, upgrade prices and total level effects, Wealth parameters, Mosaic patterns, Foundation bonus steps, and Attunement duration. `engine.js` owns rules, not balance tables. The in-game Rules & balance table is generated from this same data, so changing a number updates gameplay and its reference together.

Weights are relative. An offer slot rolls an eligible family, then a type within that family, then an eligible card variant uniformly. Mosaic variants are explicit suit sequences; their count does not increase the Mosaic type weight. Attunement filters out other suits and mixed sequences before drawing. Removing a tier or unlocking another does not add weight to a family. Ineligible categories are renormalized; within an offer, exact card IDs cannot repeat. Consequently displayed weights are not unconditional final per-card probabilities.

Reactor `values` arrays describe total strength at each level, not increments. `prices` are the additional price paid to buy each level. For Stabilizer, `outcomesByLevel` defines a complete outcome distribution at each level instead of a numeric strength. Keep either level array the same length as `prices`. Prices must be positive integers; link strengths nonnegative integers; each nonempty weighted pool must have positive weights. Suits can be renamed through their metadata. Introducing a new effect *type* requires rule code; tuning existing effects does not.

## Loop

One run starts with the configured cash budget. Buy one of three offers, discard the rest, resolve the purchase, then reveal fresh offers. No skipping, ranks, Star, Echo, automatic expansion, or turn limit. Chain length is the single reward. Power cards add no incidental link, but suited powers can earn a Foundation bonus. Purchased base cards and inert generated links are the only sources of length.

If every offered card is unaffordable, replace the first slot with the cheapest eligible card. A run ends only when no eligible card can be bought. Full prices must be affordable upfront, before any refund. Purchases always reduce cash, even when Rebate applies, so runs cannot self-fund forever.

## Cards and interactions

The chain is an ordered array of individual suited links. Sun, Moon, and Wave links are shown in one continuous sequence, read left to right across rows. Adjacent links of the same suit form one segment, regardless of which purchase created them. Buying upgrades or other powers that add no links does not create a separator. Only another suit breaks a segment. All new links append at the end; existing links are never moved or changed.

Fixed and Mystery base cards append links of their printed suit. Stabilizer selects an explicit Mystery outcome distribution. Mystery draws once from that table before applying suit Reactor. New links never activate automatic expansions.

New base variations:

- **Choice 1** costs $4 (regular Fixed 1 costs $3). Choose its suit in a cancellable picker before payment. The selected suit receives Reactor bonuses; Assembler, Rebate and Foundation also apply. During Attunement the only available choice is its locked suit.
- **Mosaic** costs $6 and appends exactly its printed three-link sequence. Variants include all different suits (ABC), a sandwich (ABA), and a pair at either end (AAB / ABB), across all suit permutations: 24 distinct sequences with the current suits. Order is fixed when offered, shown left to right, and never rerolled. The first link can merge with the existing tail. Mosaic is a base purchase for Rebate, but its exact pattern receives no Reactor or Assembler bonus. It ends Foundation.

Strategy powers are repeatable after their active effect ends:

- **Foundation** costs $7. The next suited purchase establishes a suit and appends +1 bonus link; each subsequent purchase of that suit appends +2, +3, and so on. This includes Recall, chosen-suit Choice 1, and suited upgrades or Attunement. A different suited purchase or any Mosaic ends the effect before awarding a bonus. Suitless purchases (including Overgrow and Vault) leave it unchanged. The bonus is appended after the purchase's normal output, once, without altering its snapshot calculation. No refresh or stacking while active.
- **Attunement [suit]** costs $6. All suited offers in the next three shops use that suit. Its installation does not consume a shop; each following purchase does, including suitless purchases. The third shop remains locked until a card is bought; the fourth is unrestricted. Choice 1 is restricted to the attuned suit and mixed-suit Mosaics are temporarily excluded. Suitless powers remain available and keep their normal effects. It does not reroll Mystery results or affect their odds. No refresh or stacking while active.

Growth actions are repeatable:

- **Recall [suit]** appends one matching-suit link per existing matching segment (`segment count × linksPerSegment`, initially one). Six consecutive Sun links pay one, while Sun×3 / Moon×1 / Sun×3 pays two. Segment length does not affect the payout. Recall replaces the former Recall and Polish actions, retaining the $7 price and combining their offer weights. The payout is computed once before new links arrive. Those links can contribute to future Growth. Consecutive Recall purchases extend the same tail segment without creating additional segments.

- **Overgrow** automatically appends links of the longest segment’s suit at the end. Its payout is `floor(length / linksPerBonus)`, clamped between the configured minimum and maximum. Starting values: one bonus per two existing links, minimum one, maximum eight. Ties select the earliest segment. There is no targeting step. Examples: source length 4 yields 2, length 10 yields 5, length 16 yields 8. The source is measured before appending; an earlier source segment stays unchanged. If its suit matches the tail, the new links merge with that tail. This rewards long runs alongside Recall's reward for multiple separate runs.

- Growth is eligible only if a matching segment exists. All existing links are eligible, including links made by earlier Growth or Vault purchases. No actions trigger themselves recursively.

Reactor upgrades persist for the run:

- **[Suit] Reactor** adds links to future base purchases of that suit.
- **Assembler** adds links to future Fixed base purchases of any suit. It stacks with suit Reactor and applies to Choice 1, but does not affect Mystery or Mosaic.
- **Stabilizer** changes future Mystery probabilities using `outcomesByLevel`. The current weights for 1 / 3 / 8 links are 36 / 45 / 19 at Lv1, 21.6 / 51.3 / 27.1 at Lv2, and 12.96 / 52.65 / 34.39 at Lv3. These are equivalent in distribution to the previous best-of-2/3/4 system, but each purchase now makes exactly one draw. Tune the tables directly.
- Each level replaces the old effect. Only the next level is eligible, with the line disappearing at maximum level. Existing links are not retroactively modified, and Reactor does not trigger again during Growth.

Wealth actions are repeatable:

- **Vault** adds one link per configured cash amount remaining after its own payment. It is excluded if its payout would be zero. Its links use the current tail suit, or the configured `openingSuit` on an empty chain. Vault therefore extends a run instead of adding an arbitrary separator.
- **Rebate** refunds the configured amount on the next configured number of base purchases. It cannot stack or be refreshed while active. Non-base purchases neither consume nor benefit from it. A base's refund is capped so that its net cash cost is at least $1, even if prices are tuned downward. Refunds are tracked separately from gross spending, and offers preview cash after the refund.

## State and presentation

The engine commits a whole purchase synchronously. The interface briefly shows the previous collection while revealing the result; cash is charged immediately and further purchases are blocked. Mystery has a short suspense delay. Reveal result now skips the delay without rerolling. A final purchase is settled only after reveal, preserving its full output before the run ends.

Segments affected by Growth flash together, along with the new links. Reduced motion reveals immediately without flashing. Replay and New game cancel pending reveal timers. The same seed and purchase choices reproduce offers and Mystery results; they use independent RNG streams, and previews never roll.

The game retains its viewport-height layout with score, cash, offers, and run controls on screen. Every link appears directly in the chain with a suit symbol and color; there are no purchase boxes and no chain pagination. Link size adapts to available space so the entire sequence fits. Suit segment counts stay visible below the sequence. Foundation’s next bonus and Attunement’s remaining shops stay visible above the chain. The Engine tab lists installed upgrades and strategy effects, with pagination when needed. Choice 1 uses a modal suit picker with exact per-suit bonus previews, cancellation without spending, and keyboard focus restoration. Rules and the balance table open in a modal that blocks game shortcuts and restores focus when closed. Landscape phones use two columns.

## Verification

- `node --test prototypes/one-more-card/tests/engine.test.js`
- `npm run build`
- `npx playwright test prototypes/one-more-card/tests/game.spec.js`

Engine checks cover table-driven values, weighted outcomes, segment merging and splitting, segment-count Recall snapshots, automatic longest-segment selection and append-only output, upgrade progression, combined bonuses, explicit probability tables and single-draw RNG, refund accounting, affordability, atomic transactions, Choice validation and bonuses, all Mosaic variants, Foundation streaks and resets, Attunement expiry and offer filtering, and deterministic append-only full runs. Browser checks compare the actual rendered suit sequence against the engine, verify automatic Overgrow selection, reveal/skip/replay behavior, upgrade levels, refunds, complete runs, and one-screen layouts.

Initial balance remains a playtest starting point. Growth's links per segment and all other effect strengths are editable in the balance file.
