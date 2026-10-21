# Issue 12 — alignment and spacing amendment

Recorded 2026-10-19 after review of the 0.4.2 desktop mobile-portrait view. This refines the selected B direction for the existing restaurant-editor slice and PR #36. It is an implementation contract awaiting native visual review.

- Remove the visible background panel behind the category curtains. This supersedes the v6 requirement for a visible cream category backing; the curtains and their rod remain independently readable over the restaurant.
- Give the top coin count real left padding and align its content within the visible cream face. Align Live's icon and label vertically, and apply the same native font/ink alignment to other controls.
- Make the bottom dock visibly thicker. Add bottom padding beneath the inventory stock labels so text does not sit against the dock or card edge.
- Remove excessive empty space around the goods by narrowing their panels and tightening the drawer layout. Preserve four Layout goods per page, the existing three-quarter Blender renders and readable stock labels.
- Remove the paging caret background surfaces. Keep the chevrons quiet and retain generous native touch areas without introducing visible narrow cards behind them.
- Make the rod thicker and position it through the curtain loop holes. Preserve separate hanging panels and minor pointer-down press-in feedback.
- Keep rounded controls at least 100 logical units tall, with the complete source height at the uniform corner scale as an additional lower bound. Preserve soft shadow separation and the monochrome category icons.

The labels are dynamic native Godot text, separate from generated surface artwork. Generated alpha/shadow bounds can differ from the visible face, and a font's line rectangle can differ from its visible ink. Calibrate those bounds explicitly and verify native captures; rasterizing text in HTML would add another fixed resolution and would not fix runtime layout or accessibility.

Reuse the approved B family and record any changed source calibration in a new revision. Preserve v5/v6 raw outputs, prompts, hashes, .blend files and review evidence unchanged. If new artwork is required, retain its complete output and exact provenance against the full composition and restaurant catalog. Passing provenance checks alone does not establish visual acceptance.

Placement, drag, rotation, Return-to-storage, category/paging, stock, edit pause, autosave/recovery and system Back remain the existing editor. Do not add Save/Done/Cancel/Undo/page numbers or start a later ticket. The next review build is **0.4.3 / code 43**; retain the Android packages, save identity and pinned release signer.

The [0.4.2 review](../noren-revision/README.md) remains historical evidence. Issue #12 and PR #36 stay open for user verification.
