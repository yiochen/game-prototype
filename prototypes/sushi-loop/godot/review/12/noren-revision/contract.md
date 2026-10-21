# Issue 12 — latest B amendment

Recorded 2026-10-19 for the existing restaurant-editor slice and PR #36. This refines the selected B direction after review of the 0.4.1 build. It is an implementation contract awaiting native visual review, not final visual approval.

- Make People, Layout and Floor independent hanging noren panels, attached to a visible rod. Preserve cream behind the seams between panels.
- Use a bottom dock. Reduce the goods and drawer height, showing four Layout goods per page; keep three People profiles per page and retain paging.
- Make paging surfaces narrower and the same height and material as the goods surfaces. Preserve generous native touch targets.
- Use subtle press-in feedback beginning at pointer down, with release/cancel restoring the visual. Native hit areas and existing actions retain their semantics.
- Use rounded capsules for Shop, Live, Editing and coins. Editing and coin displays have cream pill surfaces, superseding their older unbacked HUD labels. Pill surfaces have a minimum height of 100 logical units and cannot shrink below the complete source height at the uniformly calibrated corner scale; this keeps their sides rounded. Separate surfaces with soft shadows and remove dark surface borders.
- Use monochrome category icons. The existing Floor icon is already the accepted reference for that family.
- Render editor goods in native Blender through MCP using an editable three-quarter UI camera. Floor goods show real tile thickness. Technical PNG packing may preserve render pixels; it must not repaint the goods.

Retain the selected B composition, restaurant catalog and world references. The v6 source sheets and provenance implement this amendment; v5 raw source outputs, prompts, calibration, captures and build receipts remain unchanged historical evidence. Retain every full ImageGen output, exact prompt, reference/source hashes, exact unresized source crop pixels, transparent sampling gutters and uniform nine-patch corner calibration. Native phone, wider portrait-contained and landscape views must still be checked for seams, layering, shadow/material coherence, touch feedback and readable hierarchy.

The runtime remains the existing editor: placement, drag, rotation, Return-to-storage, category/paging behavior, stock, pause, autosave/recovery and system Back remain intact. Do not add Save/Done/Cancel/Undo/page numbers or start another implementation ticket. Keep the Android package, save identity and pinned signer unchanged; the next build identity is 0.4.2 / code 42.

The [0.4.1 review](../ui-revision/README.md) remains available as historical evidence. The amendment alone does not establish acceptance of any generated v6 output or a new APK.
