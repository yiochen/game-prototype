# Issue 12 — restore the previous curtains

Recorded 2026-10-20 for the existing restaurant-editor slice and PR #36. This corrects the v7 interpretation following review of 0.4.3 and supersedes the floating rail/open-ring treatment in the [alignment amendment](../alignment-revision/contract.md).

- Restore the exact previous **v6 curtains**. Do not regenerate or repaint their artwork. Their registered source generation, crop rectangles and runtime crop pixels must match the pinned v6 provenance.
- Position the straps slightly lower so the existing cloth attaches convincingly to the rod. The wooden rod remains visible across the full screen width, edge to edge.
- Restore one overall **beige backdrop behind the category rail and the goods down to the footer**. This supersedes the v7 removal of the overall rail backing; do not add a separate decorative frame around the category row.
- Preserve the tightened goods cards, bare paging chevrons with generous hit areas, bottom padding, thicker dock, monochrome icons and separate Blender merchandise previews.
- Preserve native face/ink alignment and the rounded controls' 100-logical-unit minimum height. Labels, counts and accessible names remain dynamic native text; surface separation continues to use soft shadows.

The v8 record inherits the three unchanged v6 ImageGen sheets and their full-screen provenance through the pinned parent record. Exact source-crop and pixel checks replace the v7 requirement for newly generated transparent loop openings. Preserve all v5/v6/v7 originals, prompts, source records and review evidence as historical files.

This remains issue #12 only. Placement, drag, rotation, Return-to-storage, category/paging, stock, edit pause, autosave/recovery and system Back keep their existing behavior. Do not add Save/Done/Cancel/Undo/page numbers or start a later implementation ticket.

The next review build is **0.4.4 / code 44**. Android packages, save identity and the pinned release signer remain unchanged. Issue #12 and PR #36 remain open for user verification; packaging checks and screenshots do not replace final visual approval.
