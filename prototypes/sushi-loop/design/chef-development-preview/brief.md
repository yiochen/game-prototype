# Issue 17 · composition and surface map

Review milestone: an interactive browser draft; Godot integration follows approval.

Reference inspection: current #16 native recipe-direct captures (320×720 and wide), native chef details, #15 MapleRecipePanel and plate-color contract; accepted B composition; restaurant catalog sections 5 (press/disabled), 8 (popup/confirmation), 9 (same chef identity), with 3 (coins), 13 (plates) and 14 (quiet feedback). The current continuous maple dock, illustrated headshots and independently framed photos supersede historical doodle materials and a separate Live Staff panel.

Complete composition: a portrait-contained restaurant, existing upper HUD, square cells and registered world snapshots, continuous Edit/People dock with its category tabs. Photos open Recipes directly. The level line and Manage chef shortcut are replaced by Recipes and Manage tabs. A single fixed portrait/header and popup frame owns two persistent content pages. Switching tabs slides the track left/right over 260ms with an interruptible CSS transform; the hidden page is inert and excluded from accessibility. Arrow keys select and focus the tabs. Recipe inspection and catalog scroll survive switching. Development has the same overflowing headshot anchored to its header separator, text directly on continuous wood grain, current level/cap, speed, growth, accessible plate tier, next-level speed and any unlock, a full-width coin purchase, and Unassign/Place and Fire actions. The Recipes tab returns to the same inspected dish. Fire slides up that chef’s application with the same headshot, background and current stats. Cancel returns to the unchanged Manage tab. Confirm removes the chef immediately, then lands the existing physical hiring stamp and reveals a separate live Fired imprint inside the original ink frame. The application stays open until explicitly closed; there is no firing toast or paper fly-out. No extra Live Staff shortcut.

| Layer | Source | Content / bounds / resize |
| --- | --- | --- |
| Restaurant and chefs | Existing #16 world crops and wood dock background | Existing registered sprites, bottom centered; uniform contain; square cells |
| HUD, category tabs, actions | Approved HTML maple dock / #16 control family | Live DOM text, CSS fixed radius and rim; repeating grain, never whole-image stretching; >=44px hit targets |
| Portrait | Existing ImageGen chef-headshots/v1 | Independent headshot; same identity in photo, recipes, stats and confirmation; chest ends at separator, overflow above header |
| Roster photo | Existing people-photos/v2 derived assets in #16 | Paper, inner photo, portrait, name, Assigned stamp independent; designed aspect preserved |
| Popup, stats, next-level and confirmation interior | Existing #15 maple shell and clipped pale cream catalog | CSS geometry and existing repeating wood-grain asset; same fixed corner/edge thickness. Manage has no light backing; Recipes retains its clipped cream catalog and wood details. Firing reuses the independently sliced #16 résumé paper |
| Plate tiers | Existing #15 ImageGen plate atlas | Independent five colored patterned plates; aspect preserved; accessible tier/level text. No new tier art |
| Purchase feedback | Same cream inner surface with live text | Inline level/tier outcome, no new raster surface; no experience or price multiplier |

All required artwork already exists in the accepted family; no new artwork or unrelated surfaces are needed. Provenance remains with the source assets; no temporary image paths are consumed.

States: assigned and unassigned; affordable normal and pressed; insufficient with next benefits and readable cost; MAX with final stats and no cost; tier threshold unlock; named fire/cancel; empty roster; valid/invalid/cancelled keyboard and drag placement; direct recipe inspection with no Prepare while unassigned. Shared components renders the same Development and Confirmation components as the scene.

Review-only tuning: additive starting speed + growth × (level−1), upgrade cost 60 × current level, starter Lena level 2/8, and all four sample recipes discovered. These are fixture values, not approval of production balance or discoveries. Selection, levels, assignments, coins and dismissal persist in an isolated issue17 browser key; native saves are never read/written. Each upgrade carries the previewed level and commits synchronously; repeat inputs cannot charge that level again. Placement opens an idle recipe picker; only explicit Prepare chooses work. The browser room is a static stage; no actual native production-speed integration is claimed.

## Tabs and firing revision · 2026-10-27

User feedback authorizes the new tab composition and wood-only Manage content. The physical stamp and paper are reused unchanged from #16; see source-assets.json and the original hiring stamp provenance. Application entrance is 340ms upward; stamp/contact/imprint sequence is 1100ms. The final ink persists. Paper entrance, contact scaling, prop and ink use independent layers. State commits before animation and remains valid on early close/reload. Reduced motion removes horizontal/upward/prop motion and uses a short opacity reveal. Shared components includes a replayable Fired state. Earlier prototype captures and source snapshot remain in review/17/prototype; this revision uses review/17/tabs-fired.

## Manage separator alignment

The Manage tab retains a full-width 1px warm separator with its highlight at the exact header lower edge. The existing cropped portrait ends at that same edge, so its visible chest touches the line. The separator is outside the sliding content track and adds no layout height. Recipes retains its prior catalog edge. The alignment check measures both DOM edges and verifies opaque portrait pixels at the crop bottom on all four review sizes. Evidence: review/17/header-separator/.
