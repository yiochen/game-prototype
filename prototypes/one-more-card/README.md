# One More Card — Suit sequences (v23)

Run `npm run dev` from the repository root, then open `/prototypes/one-more-card/`. This game is self-contained in this directory, with a separate engine, UI, balance configuration, and tests.

Imported from `life-sim/experiment` at v23. The previous deployment remains at https://midnight-noodle-yiochen.netlify.app/experiment/; it is not connected to this new repository.

## Tuning

**Edit [`balance.js`](balance.js)** for starting cash, offer size, suits, family and card-type weights, prices, fixed link values, Mystery outcomes and odds, Growth strengths, upgrade prices and total level effects, and Wealth parameters. `engine.js` owns rules, not balance tables. The in-game Rules & balance table is generated from this same data, so changing a number updates gameplay and its reference together.

Weights are relative. An offer slot rolls an eligible family, then a type within that family, then an eligible suit uniformly. Removing a tier or unlocking another does not add weight to a family. Ineligible categories are renormalized; within an offer, exact card IDs cannot repeat. Consequently displayed weights are not unconditional final per-card probabilities.

Reactor `values` arrays describe total strength at each level, not increments. `prices` are the additional price paid to buy each level. For Stabilizer, `outcomesByLevel` defines a complete outcome distribution at each level instead of a numeric strength. Keep either level array the same length as `prices`. Prices must be positive integers; link strengths nonnegative integers; each nonempty weighted pool must have positive weights. Suits can be renamed through their metadata. Introducing a new effect *type* requires rule code; tuning existing effects does not.

## Loop

One run starts with the configured cash budget. Buy one of three offers, discard the rest, resolve the purchase, then reveal fresh offers. No skipping, ranks, Star, Echo, automatic expansion, or turn limit. Chain length is the single reward. Power cards add no link of their own. Purchased base cards and inert generated links are the only sources of length.

If every offered card is unaffordable, replace the first slot with the cheapest eligible card. A run ends only when no eligible card can be bought. Full prices must be affordable upfront, before any refund. Purchases always reduce cash, even when Rebate applies, so runs cannot self-fund forever.

## Cards and interactions

The chain is an ordered array of individual suited links. Sun, Moon, and Wave links are shown in one continuous sequence, read left to right across rows. Adjacent links of the same suit form one segment, regardless of which purchase created them. Buying upgrades or other powers that add no links does not create a separator. Only another suit breaks a segment.

Fixed and Mystery base cards append links of their printed suit. Stabilizer selects an explicit Mystery outcome distribution. Mystery draws once from that table before applying suit Reactor. New links never activate automatic expansions.

Growth actions are repeatable:

- **Recall [suit]** appends matching-suit links. Each existing segment contributes `min(segment.length, linksPerSegmentCap) * multiplier`. The initial cap is three. Six consecutive Sun links pay three, while Sun×3 / Moon×1 / Sun×3 pays six. The payout is computed once before new links arrive. Those links are normal suited links and can contribute to *future* Growth. Consecutive Recall purchases extend the same tail segment, so they cannot create endlessly multiplying segments by themselves.
- **Polish [suit]** inserts `linksPerSegment` matching links at the end of every existing segment of that suit. The original segment boundaries are preserved. A one-link segment becomes two and pays more next time Recall is purchased; a segment already at the Recall cap adds length without increasing that segment's payout.
- **Overgrow** automatically extends the longest segment by `floor(length / linksPerBonus)`, clamped between the configured minimum and maximum. Starting values: one bonus per two existing links, minimum one, maximum eight. Ties select the earliest segment. There is no targeting step. Examples: length 4 gains 2, length 10 gains 5, length 16 gains 8. This rewards long runs alongside Recall's reward for multiple separate runs.

- Growth is eligible only if a matching segment exists. All existing links are eligible, including links made by earlier Growth or Vault purchases. No actions trigger themselves recursively.

Reactor upgrades persist for the run:

- **[Suit] Reactor** adds links to future base purchases of that suit.
- **Assembler** adds links to future Fixed base purchases of any suit. It stacks with suit Reactor, but does not affect Mystery.
- **Stabilizer** changes future Mystery probabilities using `outcomesByLevel`. The current weights for 1 / 3 / 8 links are 36 / 45 / 19 at Lv1, 21.6 / 51.3 / 27.1 at Lv2, and 12.96 / 52.65 / 34.39 at Lv3. These are equivalent in distribution to the previous best-of-2/3/4 system, but each purchase now makes exactly one draw. Tune the tables directly.
- Each level replaces the old effect. Only the next level is eligible, with the line disappearing at maximum level. Existing links are not retroactively modified, and Reactor does not trigger again during Growth.

Wealth actions are repeatable:

- **Vault** adds one link per configured cash amount remaining after its own payment. It is excluded if its payout would be zero. Its links use the current tail suit, or the configured `openingSuit` on an empty chain. Vault therefore extends a run instead of adding an arbitrary separator.
- **Rebate** refunds the configured amount on the next configured number of base purchases. It cannot stack or be refreshed while active. Non-base purchases neither consume nor benefit from it. A base's refund is capped so that its net cash cost is at least $1, even if prices are tuned downward. Refunds are tracked separately from gross spending, and offers preview cash after the refund.

## State and presentation

The engine commits a whole purchase synchronously. The interface briefly shows the previous collection while revealing the result; cash is charged immediately and further purchases are blocked. Mystery has a short suspense delay. Reveal result now skips the delay without rerolling. A final purchase is settled only after reveal, preserving its full output before the run ends.

Segments affected by Growth flash together, along with the new links. Reduced motion reveals immediately without flashing. Replay and New game cancel pending reveal timers. The same seed and purchase choices reproduce offers and Mystery results; they use independent RNG streams, and previews never roll.

The game retains its viewport-height layout with score, cash, offers, and run controls on screen. Every link appears directly in the chain with a suit symbol and color; there are no purchase boxes and no chain pagination. Link size adapts to available space so the entire sequence fits. Suit segment counts stay visible below the sequence. The Engine tab lists installed upgrades, with pagination when needed. Rules and the balance table open in a modal that blocks game shortcuts and restores focus when closed. Landscape phones use two columns.

## Verification

- `node --test prototypes/one-more-card/tests/engine.test.js`
- `npm run build`
- `npx playwright test prototypes/one-more-card/tests/game.spec.js`

Engine checks cover table-driven values, weighted outcomes, segment merging and splitting, capped Recall snapshots, automatic longest-segment selection and in-place insertion, upgrade progression, combined bonuses, explicit probability tables and single-draw RNG, refund accounting, affordability, atomic transactions, and deterministic full runs. Browser checks compare the actual rendered suit sequence against the engine, verify automatic Overgrow selection, reveal/skip/replay behavior, upgrade levels, refunds, complete runs, and one-screen layouts.

Initial balance remains a playtest starting point. Growth's per-segment cap and all other effect strengths are editable in the balance file.
