# Chef development · issue 17 UI review

Review draft: [Open the Manage separator revision](https://6ae0bf11157df44a2e1926a3--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/chef-development-preview/?state=develop).

Open `/prototypes/sushi-loop/design/chef-development-preview/`.

A review-only HTML/CSS/React prototype for leveling, unassignment, reassignment and named dismissal. Uses the accepted continuous maple/cream family and existing ImageGen headshots, photos, plate atlas and wood textures. No new generated artwork or new game dependencies. See [composition and asset map](brief.md).

Photos in Edit → People still open Recipes directly. The recipe header now has **Recipes** and **Manage** tabs instead of the level line and Manage chef button. The portrait and popup shell stay fixed while content slides horizontally. Recipe selection and scroll persist, and keyboard arrows select tabs. Manage text sits directly on continuous wood grain. Buy one level, inspect the new cooking speed and Yellow unlock, browse recipes, unassign, and place the chef again. Placement accepts an empty cell orthogonally beside a belt, opens an idle picker, and waits for explicit Prepare. Unassigned chefs can inspect recipes without a Prepare button. Fire slides up the chef’s application; Cancel leaves all state intact. Confirm removes the chef before playing the physical stamp animation, which leaves a live **Fired** imprint on the application until it is closed. No toast appears. Closing or reloading during the stamp cannot restore the chef. Escape cancels placement, returns from the confirmation or closes the popup. Photos, HUD and category tabs regain input after closing. There is no Live Staff button.

The review selector resets mock data to affordable, insufficient, MAX, near-MAX, unassigned, fire, recipes, People and Shared states. Reset restores the selected fixture. Shared renders the same tabbed popup in normal, pressed, disabled and MAX states, plus the confirmation application and replayable Fired stamp. Narrow portrait and wide windows retain the portrait scene; short landscape uses a two-column preview so benefits stay visible by the purchase.

The prototype stores levels, coins, retained growth/caps, recipes, assignment and dismissal in `sushi-loop-issue17-ui-review-v1`. It does not access native saves. Synchronous commands carry the previewed level; replaying it is a no-op. Purchase geometry remains stable across tier unlocks, and a repeated click cannot activate a neighboring action. Illustrative upgrade costs and plate thresholds live in `balance.js`; sample starting staff live in `model.js`; they do not set production balance. The room remains a static stage: native preparation-speed integration and production save migration await design approval.

## Verification

- Build passes with the repository's existing large-chunk warning.
- 16 feature browser checks: purchases, duplicate input, tier eligibility, persisted progress, cap/MAX, poor preview, unassignment/reassignment, explicit Prepare, named fire/cancel, keyboard focus, Escape, real touch gestures, invalid/cancelled drops and layout checks at 320×720, 390×844, 1440×1000 and 844×390. Shared states captured on phone and wide.
- 20 existing hiring prototype browser checks pass with the optional shared recipe-panel extensions. Their historical screenshot files are preserved unchanged after the regression run.
- `npm test`: 200 passed, 2 existing failures in unchanged `refinement-rollout.test.js`. Missing source evidence: `belt-straight-n/candidates/round-09/consumer/.godot/.gdignore` and `coin-pop/final/original-catalog-object.json`. Same baseline failures recorded by #16. No native sources or historical artifacts were changed to bypass them.
- Current full-scene, Shared, contact-frame and retained Fired captures are in `../../review/17/tabs-fired/`; the earlier prototype and its source snapshot remain in `../../review/17/prototype/`. Inspected portrait crop/baseline, cream corner clipping, readable costs, disabled contrast, patterned plate proportions, stable purchase position and visible landscape benefits. Remote results and deployed URL are recorded in `../../review/17/tabs-fired/verification.json`.

The game-ui-prototype skill requires approval of the deployed prototype before game implementation. Issue #17 remains open pending approval and native implementation/verification.

Latest refinement: Manage keeps a full-width separator directly at the cropped headshot’s lower edge. See `../../review/17/header-separator/verification.json` and its phone/landscape captures. Build and 16 feature checks passed; four deployed layout checks verify the exact baseline, including opaque pixels at the crop edge.

## Native handoff approved

The user approved the separator-aligned tabbed prototype and requested Godot implementation. Native integration, command/save migration, shared gallery, signed Android release and device-verification limits are recorded in `../../review/17/native/`. The earlier prototype approval gate has been satisfied; historical draft evidence remains unchanged.
