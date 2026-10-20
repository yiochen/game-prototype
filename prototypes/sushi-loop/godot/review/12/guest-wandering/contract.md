# Issue 12 — guest wandering after a route is blocked

Recorded 2026-10-20 for the current restaurant-editor slice and PR #36. This follows the [sprite-selection correction](../sprite-selection/contract.md); the approved v8 UI, artwork and visible-sprite selection remain unchanged.

- Accept a layout edit when it occupies otherwise valid empty floor even if that edit disconnects a guest's route. Keep direct overlap with a guest, busy-seat protection, occupied cells and the entrance guard unchanged.
- A walking or leaving guest whose goal cannot be reached wanders indefinitely over available free floor with the existing walk animation. A blocked route is not a visit failure, timeout, disappearance, teleport or forced rescue.
- Retain the original destination and visit/meal state while wandering. Retry the goal route and resume it automatically when layout changes make it reachable again. Do not introduce a new player action or customer-rescue system.
- Seated guests remain seated when routes become blocked. Preserve their seat assignment, position, meals, visit state and normal service progress. Entering Edit still pauses every simulation clock and RNG draw.
- Save and restore wandering mode, actual position, route origin/progress, retry clock and cursor, including a fractional position on an active segment. Reopening must not reroll a visit, duplicate a meal, change the customer identity or move the guest discontinuously.
- Add `customer_navigation_version = 1`. Validate legacy navigation-version-0 saves before migration, then add neutral navigation fields and missing navigation tuning without advancing time or RNG. Retain all legacy coins, objects, inventory, guest positions, meal/visit state and service progress; only documented navigation defaults and seated path bookkeeping may change.

The next review build is **0.4.6 / code 46**. Android package names, `SushiLoopTickets` save identity and the pinned release signer remain unchanged. The actual normal 0.4.5 → 0.4.6 upgrade must preserve primary and backup byte for byte before first launch. No new artwork, UI layout, change to existing service/economy balance or full #14 customer-rescue ticket is included. New wandering speed/retry tuning lives separately in content. Preserve all earlier review evidence. Issue #12 and PR #36 remain open for user verification.
