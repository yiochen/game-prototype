# Plate-color tiers

This user-approved revision replaces the material-themed recipe tiers throughout Sushi Loop. It applies to recipe prices, chef eligibility, expedition discovery pools and their shared presentation.

## Order and progression

| Plate tier | Minimum chef level | Former name (migration reference only) |
| --- | --- | --- |
| White | 1 | Wood |
| Yellow | 3 | Steel |
| Red | 5 | Copper |
| Blue | 8 | Silver |
| Black | 12 | Gold |

The order is White → Yellow → Red → Blue → Black. These are this game's five tiers, inspired by Japanese kaitenzushi price plates; there is no claim that this exact palette or ordering is universal in Japan. Level thresholds remain balance inputs.

Each recipe retains a fixed coin price in its tier's price band. Every higher tier's price band is entirely above every lower tier's. Recipes within one tier may retain different exact prices: a color indicates the band, not one mandatory price shared by every dish. Exact prices remain visible wherever already specified. Chef development does not multiply dish prices, and preparation time remains independent of price/tier.

Chef levels, capability ceilings, eligibility checks, expedition introduction order, catch probabilities, guarantees, NEW clearing and explicit Prepare behavior retain their accepted rules. Only their tier names and visual identity change.

## Shared presentation

- A served dish sits on a ceramic plate with its tier's color and a distinct rim pattern. Reuse that identity on belts, in chef/guest dining presentations, blackboard/preference icons, recipe tiles, fixed details, discovery awards and tier-introduction notices wherever the dish/plate is shown.
- Each of the five tiers requires a different rim pattern as well as a different color. Rim detail must remain legible at phone scale; accessible descriptions name the plate tier and required level. Exact rim artwork is an art-design task.
- Recipe tiles are recipe cards containing the food and its colored plate, rather than boards made of tier-specific wood or metal. Unknown recipes use an unidentified dish silhouette on the known tier's plate and reveal no price.
- Keep the existing two-column picker, fixed details/Prepare area, current/inspected outlines, NEW badge, muted ineligible states and accepted B/maple UI family. Neutral shared panels remain coherent with that family; plate identity supplies the tier cue. Red plates must remain distinct from selection, rejection and disabled-state treatments.
- The recipe award uses the same plate artwork (the former Copper/Eel example is now Red). Tier introduction uses its colored-plate icon, name and future-availability copy inline in results.
- Colored plates do not introduce plate stacks, table clearing, extra billing interactions, recipe rarity, separate quality upgrades, sale multipliers or changes to floor-style cosmetics. A guest's empty-handed standing/walking behavior remains unchanged.

## Implementation handoff

Issue #15 owns the shared plate-tier presentation and integration into restaurant dish/recipe views. Issues #16–17 reuse it for reachable tiers and level-up unlocks; #24 and #27 reuse it for recipe awards and discovery progression. Existing material-tier identifiers in wireframes or saved data must map by ordinal rank without losing discoveries, chef progress/caps, assignments or fixed prices. Document legacy aliases only as migration details, never as current player-facing tier names. Historical approved artwork, generation provenance and review captures remain historical evidence; new implementations follow this contract.

## Research

Color-coded pricing is established in Japanese kaitenzushi: [Japan Guide](https://www.japan-guide.com/e/e2036_kaitenzushi.html). Sushiro's [official 2023 announcement](https://prtimes.jp/main/html/rd/p/000000399.000049164.html) describes price-coded plates and item-priced white plates. This inspires the visual language without importing a chain's exact pricing or colors.
