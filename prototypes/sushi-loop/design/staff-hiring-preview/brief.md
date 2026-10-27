# Issue 16 — applicant / roster composition

Review milestone: interactive HTML prototype only; Godot integration awaits approval.

References inspected: restaurant-item-catalog sections 5 (button states), 8 (popup surfaces), 9 (chef identities), plus 3 (coins), 13 (colored dish plates), 14 (quiet notification); restaurant world concept; accepted B composition; current #12 wood dock and #15 illustrated headshots/photo frames, recipe picker and colored plates. Relevant wireframes: staff-roster, staff-applicants, staff-full, component-applicant-resume, component-roster-tray, recipe-idle.

## Complete screen

The room/HUD remain visible behind a centered maple applicant panel. Header: Applicants, current/maximum staff and close. A custom transform-driven horizontal scroll view extends beyond both popup sides to the edges of the contained game screen. The centered application is upright; neighboring applications are slanted and slightly lowered like a hand of cards. There is no visible scrollbar, page indicator, caret or swipe instruction. Arrow keys, pointer drag, touch and wheel browse; only the centered application is actionable/accessibility-visible. Independent portrait at upper left, full name and former occupation at right; background and three raw stats (cooking speed, growth per level, maximum level) follow. No strength summary, reachable-tier field or initial-level/assignment caption appears on the application. Explicit vermilion Hire includes the cost. A full roster makes the header’s Roster full text red; insufficient coins change the disabled button to current / required coins with the required amount red. There is no above-Hire error row. Footer: free Refresh, replacement text and live cooldown. No vertical scrolling on any reviewed layout, including short landscape; the latter uses a compact two-column application. No Back to staff footer.

Motion: one shared live presentation position; direct drag with a shallow magnetic well at each card, progressive end resistance, projected release velocity, and an interruptible spring (stiffness 240, damping 27). Nearby cards rotate up to 14°, lowering by up to 20px, at a 0.88-card pitch. Reduced motion snaps statically and removes tilt/scale/depth. Paper corners and portraits keep their existing independent calibration.

Staff (Live) and People (Edit) share a compact horizontal instant-photo roster with an Assigned stamp. Staff capacity and Applicants sit above the photos. Tapping a photo opens separate maple details; closing restores its originating tray and mode. Unassigned photos support sideways browsing and upward placement onto empty square cells beside the belt. Valid placement opens the existing idle recipe picker; closing it preserves idle assignment. Prepare explicitly starts a chosen eligible recipe.

## Surface and state inventory / asset map

| Piece | Source | Independent content / anchors / resizing |
| --- | --- | --- |
| Restaurant/HUD, maple dock and waves | Existing wood dock source and production world assets | Scene remains independent; square placement cells, bottom-centered scene sprites |
| Modal and detail maple panels | Existing wood-grain; accurate HTML/CSS frame | Live labels; fixed corner radii, repeated texture, separate overflow-visible carousel and maple frame |
| Resume paper | New ImageGen paper, referenced to complete composition above + catalog + current instant photo | No baked text/portrait; nine-slice calibrated after inspection; safe equal content insets |
| Chef identities | Existing eight ImageGen headshots | Uniform 25:32 chest crop; no stretch; same portrait in resume, roster, details |
| Instant photo / Assigned stamp | Existing independently generated v2 outer/inner paper and stamp | Uniform fitting of source bounds; separate caption and stamp text; chest aligned to frame bottom |
| Tier plates / idle recipe picker | Existing #15 plate family and shared React picker | Color + rim + accessible tier/required level; thresholds 1/3/5/8/12 |
| Hire / refresh / close controls | Existing maple/vermilion CSS vocabulary | Normal/pressed/disabled/focus; minimum 44px targets |
| Toast | Maple family, HTML/CSS | Live announcement; no input obstruction |

Review fixtures: available (2/4), full (4/4), unaffordable, remaining pool/empty, real-time refresh deadline, Staff/People roster, chef details, placement, idle picker and Shared gallery. Mock data/state persist in isolated browser storage, never the game save. Cooldown is a tunable five minutes. Review fixtures reset only through the explicit review controls.


## Application presence

Keyed paper visual layers provide 280ms entrance, 210ms exit, a 190ms replacement entrance delay and short per-card stagger. Survivors animate from measured current transforms. The fan’s gesture position remains independent. Reduced motion uses 80ms fades. Applicant panel dismissal has a 170ms exit with the background still input-shielded. User decision: no timed replacement. Offers persist until Hire or explicit Refresh. Cooldown expiry only re-enables Refresh; it does not replace offers or advance the visible application.

## Hired confirmation revision

The unchanged central paper expands uniformly by 4.5%. A separate rubber-stamp prop drops from above, makes a small impact/rebound and lifts away. Its contact reveals the existing independently generated red ink frame with live Hired text, angled across the quiet middle of the paper. The marked application holds briefly, then flies out. Neighboring offers stay in their fan and flow into place afterward. Physical prop, paper, ink frame and text are independent layers. Reduced motion keeps the Hired confirmation with a short fade and no falling/expanding travel. Payment and recruitment commit once before the visual sequence, so interruption or closing cannot recruit twice or undo a hire.

No hire toast. Newly hired staff carry a persisted unread flag displayed as a small red dot on the inventory photo. A dot is marked seen only after the corresponding photo is at least 85% visible for 1.4 uninterrupted seconds with no modal covering the tray and the document visible. Details/placement also acknowledge that chef immediately. Offscreen, covered and backgrounded photos retain their dots.
