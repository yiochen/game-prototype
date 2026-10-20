# Sushi Loop implementation

- The game target is **Godot Android**. The wireframe site is a design/reference surface and does not replace the native implementation.
- Work one authorized GitHub implementation ticket at a time and stop for user verification before starting the next ticket.
- For every ticket touching UI, read the [Restaurant UI & item catalog](design/art-directions/restaurant-item-catalog.png), relevant current wireframe scenes/components and [ART-10 UI workflow](design/art-directions/README.md#ui-reference-workflow-art-10-approved-2026-10-19) before implementation. Expedition UI also checks its underwater catalog and concept.
- Reuse approved UI assets; create corresponding missing or substantially revised UI artwork through ImageGen with those references. Retain source output, exact prompt, reference hashes and provenance. Keep dynamic text/counts out of baked art.
- Catalog visual finish must fit the wireframe's existing behavior, layout and control set. Illustrative catalog controls, sample names/values and junctions add no requirements. Preserve the transparent restaurant HUD.
- Reuse native UI presentation between gameplay and the Shared component/gallery. Verify relevant normal/pressed/disabled/selected and specified NEW/MAX states on a narrow phone and wider portrait-contained window, with accessible names, system Back/focus and at least 44 px touch targets.
- Preserve the approved [projection, proportions, lighting and material decisions](design/art-directions/decisions.md); keep production sources editable and gameplay/balance independent.
