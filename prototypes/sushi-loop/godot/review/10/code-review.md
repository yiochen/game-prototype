# Ticket #10 review

## Doodle and animation revision

Pinned base: `9551cb225210e4cfc3f98f25f3c4de922a71b35c`. Two independent reviewers examined `9551cb2...c5776d8`, with particular attention to the visual revision `fd6db2d...c5776d8`. Sources were `AGENTS.md`, issue #10, the parent specification, the supplied `doodle.png` reference and the user's corrections. The target remains Godot Android. This revision does not implement later tickets.

### Standards

No documented standards violations or actionable baseline smells found. The prototype remains independent, content tuning stays separate from rules, and ArtBook and the renderer centralize sprite registration and presentation. Tests use isolated storage; signing material is ignored. Validation is appropriate to the native artwork and renderer changes.

Standards findings: **0**.

### Spec

The new artwork follows the compact chibi proportions, rounded ink, elevated front/top shading and quiet floor of the supplied doodle catalog. Feet register at tile centers with a fixed scale across clips. Fifteen character clips each contain six different drawings at least 445 native pixels tall.

The connected conveyor has four equal 502 × 460 cuts with six synchronized phases. Rails stay fixed while slats and dishes move. Actual runtime recording shows broad belts, continuous joins and sushi above the belt pass. The HUD and square grid remain intact on portrait screens. No later-ticket feature work was introduced; the full inventory requested by issue #33 remains separate from this authorized correction.

Spec findings: **0**.

The reviewers also identified publication evidence that needed refreshing: the production README, Android captures and release links. Those documents are updated with the revised build before publishing; these were documentation follow-ups, not code findings.

Total findings in this revision: Standards **0**; Spec **0**.

## Original implementation review

Pinned base: `9551cb225210e4cfc3f98f25f3c4de922a71b35c` (`origin/main`). Independent parallel reviews examined the committed native change against `AGENTS.md`, issue #10 and the parent specification. Runtime target is the user-confirmed Godot Android adaptation.

## Standards

No hard documented-standard violations. Two optional judgment findings:

- Possible Shotgun Surgery: renderer cell count and input camera extent repeated 9/18 while content defined the floor. Resolution: derive visible columns and camera extent from public floor content, preserving square fixed-scale geometry.
- Possible Duplicated Code: game and renderer repeated font construction. Resolution: both use one `typography.gd` factory with the same readable weight.

## Spec

Two visual findings:

- Parent story 4 asks for a clear square grid. Material grain alone did not show both cell axes. Resolution: add restrained, independent grid marks aligned to simulation coordinates.
- The touched entrance was a flat proxy. Issue #10 requires finished catalog-style artwork. Resolution: author a fresh dimensional entrance asset and reuse it in the actual room and native gallery.

No additional gameplay, persistence or unauthorized-scope finding. Automatic production, held food, belt capacity, fixed-price sales and transient restoration were found coherent.

Findings: Standards 0 hard / 2 optional; Spec 2 visual. All four are addressed before the review build is published.

Both independent reviewers subsequently inspected the final fixes. Standards confirmed the content-derived camera geometry and shared typography factory. Spec confirmed the readable cell grid and matching dimensional entrance in the actual phone, wide and Shared gallery captures. Neither reviewer found a remaining material defect in that focused verification.
