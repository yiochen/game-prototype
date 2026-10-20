# Art revision decisions — issue 33

Decision checkpoint: 2026-10-19. Status: the choices below are **locked and the user has explicitly authorized the full production asset revision**. The 2026-10-19 revamp request supersedes earlier study-only limits below. Issue 33 remains open until the user approves the game-scene assets.

## Four locked decisions

| ID | Decision | Exact meaning | Current implementation |
| --- | --- | --- | --- |
| ART-01 | **70% environment front/height** | Preserve square ground tiles and their X/depth pitch. Project vertical height at 0.70 of the earlier environment baseline: `screenX = anchorX + cellSize*x`; `screenY = anchorY + cellSize*depth - 0.70*cellSize*height`. This is a projection coefficient, not a 70° camera, changed tile aspect, reduced physical model height, or a squeeze of finished PNGs. | Verified in the frozen [projection study](../../assets/projection-study/README.md); Version 12 native rebuild and all 9,390 registered captures complete; awaiting user asset approval. |
| ART-02 | **125% character size** | Use a true uniform native root scale of 1.25 relative to the B/C study's 100% base. Do not interpret this as another 25% increase over an already enlarged sprite. Ground root, camera and logical pixels per tile stay fixed. | Selected in the [character study](../../assets/character-scale-study/README.md); the production cast and registered captures are published; awaiting user asset approval. |
| ART-03 | **C / Chunky character proportions and revised head** | Use C as the proportion reference: chubby body, short leg stubs, tiny unobtrusive feet, full side depth, softened cheeks/chin and a less cubic face. Use the revised rounded crown, overlapping curls and fuller temple/back/nape hair volume. B remains a comparison reference, not an alternate selected production shape. Preserve each character's identity, costume and hair type when translating the proportions to the cast. | Native C revision 3 at 125%, retained at commit `a3d2a2d4c147d1b6347635e520a5a8cc0a48af7a`, is the accepted shape/scale reference. All twelve production identities and their animations now use the selected proportions; user approval of the published captures remains pending. |
| ART-04 | **Layered, full-footprint tile decoration with varied heights** | Use continuous restaurant ground/floor tiles or ocean-bed tiles beneath separate decoration sprites. Each decoration tile must substantially occupy the full width and depth of its cell, with a broad readable mass rather than a small centered prop surrounded by padding. Keep tile-based assembly; vary the decoration silhouette, composition and height across neighboring cells. | Concept-specific full-cell pieces and bordered grounds are rebuilt; final scene-art approval remains pending. |

Reference: [live character study](https://deploy-preview-34--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?v=a3d2a2d&ntl-drawer-state=hidden#character-scale-study). At the selected scale, C is approximately **1.576 tiles tall including the hat**, with a conservative **0.814 × 0.814 tile turning envelope** across four cardinal views. Those are measurements of this chef reference, not required identical dimensions for every character or accessory.

## Existing constraints to carry forward

- **Characters keep the ordinary 35° orthographic camera**, with square pixels and no environment projection stretch. This is a retained camera constraint, not an additional character-size change.
- **One-cell character width and ground footprint.** Feet are anchored at the tile-center ground root. Head/hat may rise above the cell and overlap the row behind; horizontal extent and ground occupancy stay inside one cell. Keep collision, art bounds and support attachment points separate.
- **Minimal feet and short legs.** No return to the rejected bulky shoes. Preserve planted contacts when poses and animations are rebuilt.
- **Scene composition:** current restaurant and underwater review scenes use seven columns in portrait; preserve that review framing. The entrance is four tiles wide. Existing 2×4 and 3×3 cluster studies remain historical references, but large repeated decorated patches are not the primary continuity solution. ART-04 now governs decoration: continuous ground plus full-footprint tile-based objects. Optional larger compositions can reuse those pieces. These scene dimensions are existing composition choices, not new universal object-size rules.
- **Connected assets and layering:** conveyor pieces must join with matching decks/edges and supports under their actual shapes; demonstrate straight–corner connections and connected wall runs. Food rides above belt surfaces. Character seats, hands and food must match explicit support points after the projection/scale change.
- **Source and review workflow:** retain editable Blender projects and reproducible capture sources in the repo; use registered high-resolution transparent captures; keep the concept art visible as reference. Recheck all four directions, repeated tile arrangements, interacting neighbors and animations. Earlier animation request remains at least six distinct frames per animation; the established capture timing is 12 fps.

## Decoration design contract (ART-04)

- **Ground first:** floor/ground and ocean-bed tiles make a continuous foundation under decoration. Keep the ground layer independently reusable; do not bake an isolated rectangular platform into every rock, plant or coral sprite.
- **Fill the tile in both ground axes:** author the decoration's mass across its one-cell width and depth. Do not achieve a nominal one-cell measurement with a tiny extremity while the main shape remains sparse. This refers to the modeled footprint and coverage, not fitting a PNG's alpha bounds or making every silhouette a solid square. Natural contour notches and small gaps can reveal the continuous ground beneath.
- **Tile-based objects are the building blocks:** a tile can contain one broad rock formation or a deliberately composed grouping of coral/vegetation and supporting smaller forms. The grouping should read as a substantial decoration tile, not scattered miniature props. Small accent props can remain separate supplements; they do not substitute for full-footprint primary decoration.
- **Vary height as well as outline:** prepare low, medium and tall forms, with different top profiles and asymmetrical groupings. Exact heights, family counts and distribution are still review choices. Keep the 70% environment projection fixed so height variation comes from the authored geometry.
- **Connected without a repeated bundle:** neighbors share compatible ground/boundary joins, while silhouette, height and internal arrangement vary. Avoid reusing one complete garden at a fixed interval or synchronizing the same sequence on both sides. Do not require every adjacent top to have the same height to achieve continuity.
- **Preserve readability:** depth-sort above the common ground with registered roots; taller decoration may overlap scenery behind it. Keep gameplay lanes, interaction targets and the visible collision boundary readable. Ground coverage, artwork height and collision remain separate.
- **Approval views:** compare a dense 3×3 arrangement and a longer connected edge with a corner at phone size, including mixed heights and repeated source pieces. Judge coverage, seams, repetition and actor occlusion together. These views are the proposed validation for the next authorized study, not an instruction to start the full asset update now.

## Earlier review topics before the authorized full pass

These are review topics, not newly approved changes:

1. **Lighting and shadow treatment.** Working direction: keep floor-contact shadows and broad ambient lighting adjustable in Godot rather than permanently baking them into every color sprite; retain useful internal form shading. Exact shadow strength, softness, occluders and optional auxiliary maps are not locked. This does not assume a shader can infer full 3D ambient occlusion from a color sprite.
2. **Environment finish and scene coherence.** Review the 70% projection with representative furniture, conveyors, terrain and ART-04 layered decoration tiles together, including materials, color balance, height ranges and representative arrangements. The decoration architecture and full-footprint coverage are now locked; the individual designs remain subject to visual review. The projection choice alone does not approve every existing mesh or material.
3. **Interaction fit at the selected settings.** Validate C at 125% beside the 70% belt, seated on stools and next to counters/doorways before applying the change to every animation. Recalibrate deck, seat, hand and held-item attachments; do not inherit the old height offsets blindly.

The user subsequently authorized the full production update on 2026-10-19. The rollout section below supersedes these earlier study-only scope limits. Scope remains issue 33 and eventual Godot Android delivery; completing the native pass does not establish final scene-art approval.


## Decoration height experiment — pending review

After the full-tile density patch, the user requested taller decorations and specifically encouraged 3–4 tile projected heights. The decoration study now compares the original, a moderate 1–1.6 tile set, and a bold set: rock 1, coral 1.8, column 2.5, kelp 3, peaks 4 projected tiles. The 70% camera and one-cell X/Y footprints are retained. These numeric bands are experimental, not locked; full production remodeling still awaits the user's go-ahead. Review evidence: `../../review/33/decoration-study/heights/README.md`.


### Height construction correction

User feedback supersedes the stretched height experiment: raise the supporting rock base; keep coral, kelp and other decoration at their original proportions on top. Rock crowns should be broad and relatively flat, rather than pointed. The updated study keeps the previous total projected heights to isolate this construction change. The numeric heights are still pending approval. The current page compares corrected raised bases with the original low patch; previous stretched variants remain historical only. Evidence: `../../review/33/decoration-study/rock-bases/README.md`.


### Living ledges and camera hypothesis — pending visual review

Follow-up feedback clarifies the desired direction: broad but uneven rock crowns, compact kelp/coral distributed on lower, middle and upper ledges, varied coral colors, and dark lower rock faces graduating toward bright tops. The living-ledges study implements these traits in native geometry and materials.

The user hypothesized a lower camera for objects covering more than two vertical tiles. The study compares the same geometry in the established 70% oblique profile and ordinary 35° orthographic profile. Its experimental mixed rule uses the S-facing complete reference silhouette (>2 tile heights), with square floors and fixed world roots. This camera exception is not locked and does not supersede ART-01 for production. The preserved original concept is visual guidance, not proof of a specific camera or angle. Evidence: `../../review/33/decoration-study/living-ledges/README.md`.


### Compact organic revision — pending visual approval

Browser feedback sets a new study limit: every decoration's vertical rise stays below three tiles. Shape refinements use irregular shoulders and widths, compact branching coral and thick flared sponges. The gradient must not acquire a world light direction when facings vary: the study now uses emission materials, zero lights, and height/slope-driven rock tone.

To remove the front gap, the experimental 35° upper view now transitions to square projected footing near ground. This explicit native capture-space exception is documented and audited; it is not a pure ordinary orthographic view over the entire model and does not replace ART-01 for connected production terrain. Physical footprints and roots stay fixed. Evidence: `../../review/33/decoration-study/compact-organic/README.md`.


### Plant-led decoration — requested study, pending visual approval

Coral and kelp should sometimes be the primary mass and silhouette, rather than always being small accents on tall rocks. The new review study mixes low-support coral thickets and kelp groves with three rock-led families. Plants fill their own one-cell compositions at substantial scale, with varied heights and colors; rock-led examples retain ledge vegetation at larger proportions. The under-three-tile rise limit, full physical footprint, independent ocean bed and direction-free material tone remain in force. This is a limited comparison, not approval of all assets or authorization for production rollout. Evidence: `../../review/33/decoration-study/plant-led/README.md`.


### Concept-referenced decoration — requested review pass

The user rejects arbitrary/random compositions and requires underwater and restaurant decorations to follow the approved scene concepts. Use recognizable silhouettes, palette, materials and object groupings from those images. Each review object now carries a specific original concept crop. The twelve-piece native study replaces the exploratory patch on the live review page; it does not roll out all production art.

Carry the four rules forward: projection based on height; maximum three projected tiles; full width and depth of a ground cell with substantial mass; darker lower surfaces without a world lighting direction. In this pass the cap applies to the **complete projected silhouette**, including depth, in every facing and both capture profiles. By-height mode selects a 35° upper view/square footing when the largest complete 70% silhouette exceeds two tiles; smaller shapes keep 70% oblique. This updates the earlier S-only selection test and remains a camera experiment pending review. Original concepts remain unchanged; source models, measured captures and reference hashes are retained. See `../../review/33/concept-decoration/README.md`.


### Contrast trial — awaiting a choice

The user requests more contrast and asks whether to edit images or Blender lighting. The current capture has no directional illumination and uses emission materials; test global RGB contrast directly before changing source materials. The review page compares Original 100%, Punchier 118% and Strong 135% on the same sprites, with a selectable example and a shared display grade across both scene sets. These are reversible display previews, not new baked art, source-light changes or a locked grade. Selective lower-base/face contrast remains a material-ramp adjustment if a global grade is insufficient. Evidence: `../../review/33/decoration-contrast/README.md`.


### Selected contrast: 135%

The user selected **135%** as the preferred contrast. Retain that color direction for the next decoration revision; it supersedes the earlier 118% initial preview. The live review starts at 135%. An isolated native Blender proof applies the same sRGB contrast using a shared compositor group, preserving original alpha and direction-free lighting/materials. Four objects in four facings match the browser grade within 8-bit rounding. Do not apply the browser filter again to already baked sprites, and keep shared ground/reference images ungraded. This selects a grade, not all asset shapes or a full production rollout. Source/evidence: `../../assets/native-contrast/README.md` and `../../review/33/native-contrast135/README.md`.


## Authorized production rollout — 2026-10-19

The user approved the native 135% proof and requested all objects be revamped.
This section supersedes the earlier study-only/pending-camera wording wherever
it conflicts; historical experiments above remain evidence, not active rules.

- **ART-05 — every Blender object uses the native 135% sRGB contrast grade.**
  Apply `clamp((c − .5) × 1.35 + .5, 0, 1)` to straight RGB in the shared
  Blender compositor, preserve Render Layers alpha, then return to premultiplied
  scene-linear output. Standard view, no extra look/exposure/gamma or CSS grade.
  Production floors also use this export grade; unchanged concept reference
  images and historical comparison controls remain ungraded.
- **ART-06 — dark lower surfaces across the entire library.** Restaurant props,
  architecture, characters, conveyors and underwater assets all use a native
  world-height material ramp. Keep crown/upper surfaces brighter and preserve
  explicit material colors. Emission surfaces, zero world strength and zero light
  energy eliminate world directional illumination. A camera-symmetric absolute
  normal/view term adds form without a left/right light source. Ground-contact
  shadows stay a separate future Godot rendering layer.
- **ART-07 — height-dependent decoration projection and a three-tile cap.**
  Small decoration uses ART-01. If the largest complete silhouette under the
  70% profile exceeds two tiles across any facing, use the tested ordinary35
  upper view transitioning to square footing below Z=.42. The entire projected
  silhouette must stay at or below three tiles in every facing, including ground
  depth. Characters retain ordinary35 without that footing deformation.
  Connecting modular architecture retains matching square-ground ports.
- **ART-08 — representation and cooccupancy.** Sushi and all reaction bubbles
  are ImageGen 2D art. Current/swirl/eel warning/lightning/discharge are 2D effects,
  with the warning hatch suitable for direct Godot drawing. Blackboard and blank
  sign have one player-facing blank surface, rooted at the front edge so another
  object can share the cell. They never bake dynamic text/recipe content.
- **ART-09 — remove obsolete large garden bundles.** Delete both A/B versions of
  restaurant border/corner gardens and underwater reef/coral gardens from the
  active catalog and scene examples. Continuous bordered floors plus individual
  concept-specific full-footprint pieces replace them.

All earlier locked character, footprint, animation, source retention and review
requirements continue. The user's 34 feedback items are tracked in the rollout
review record. Issue 33 remains open until the user approves all game-scene art.

## Character surface lighting experiment — pending review, 2026-10-19

The user found the universal emission finish too flat and requested a lighting
trial on the green-hatted chef. [Noor's isolated lighting study](../../assets/character-lighting-study/README.md)
compares the production baseline with three real Blender area-light treatments.
The 125% chunky anatomy, 35° camera, native 135% grade and darker lower-material
ramp stay fixed. Actual matte Principled surfaces replace emission in the study;
an overhead key distinguishes upward faces from sides, and four equal cardinal
fills keep the face readable without introducing a preferred horizontal direction.

All four facings share the same geometry, camera, scale, frame and root. Soft,
Faceted and Crisp vary only overhead strength (100/140/180 W); equal fill remains
100 W per lamp. Enlarged hat crops show the surface separation. Earlier overbright
trials and clipping measurements are retained as evidence. The current candidates
preserve the hat's green channel without clipping in the measured top regions.

This is a requested experiment, not a new universal finish decision. ART-05/06
remain the production baseline until the user chooses a lighting treatment.
No production sprites or models are replaced, and issue 33 remains open.

### Conveyor and crate transfer test — pending review

The user requested the same lighting comparison on the conveyor and wood crate.
The [environment lighting study](../../assets/environment-lighting-study/README.md)
retains the exact Noor presets and the environment's calibrated 70% projection.
It adds four-way straight-belt/crate stills and a connected three-module L with
a complete native 24-frame, 12-fps South-facing loop. Geometry, UVs, registered
roots and the native moving-deck phase remain unchanged.

The lights reveal the belt rails and crate braces more clearly. Pale crate-top
boards lose color detail under the stronger presets, while Soft retains more
wood color. This measured transfer result is shown directly in the review page;
no new universal lighting treatment is selected and no production asset changes.


## Selected Faceted lighting — 2026-10-19

The user chose **Faceted** after reviewing Noor, the conveyor and the wood crate.
Use this native Blender finish for future captures of every Blender object:
matte Principled surfaces, a centered 140 W overhead area light, and four equal
100 W cardinal fills. The overhead light separates top planes from sides; equal
horizontal fills avoid a preferred left/right world direction. Keep the selected
character and environment projection profiles, registered roots and framing.

This decision supersedes **only** ART-06's emission-only surfaces, zero-energy
lamps, and camera-dependent absolute-normal/view tone. Retain ART-06's
native lower-height material ramp on characters, restaurant and underwater
objects, ART-05's 135% native sRGB grade with alpha bypass, and separate future
Godot ground-contact shadows. Do not add a second browser contrast filter.
Earlier zero-light studies remain historical evidence.

### Approved Faceted material refinement

The user also requested wood that reflects less light and conveyor rails with a
duller color. The [material refinement study](../../assets/faceted-material-refinement/README.md)
compares the original Faceted materials against tuned materials on the straight
belt, wood crate and connected conveyor. Both variants retain the exact chosen
light rig; this isolates material response and palette from lighting strength.
All four facings retain identical geometry and registration. The South-facing
connected fixture retains its synchronized 24-frame native moving-deck loop.

The user approved these material adjustments on 2026-10-19 and requested the
entire native sprite library be regenerated before issue 33 closes. Apply the
chosen Faceted light rig to every native Blender object. Use the approved matte
crate-wood response and muted-clay conveyor rail palette, including connected
conveyor corners. The crate's three original wood colors retain their hue
relationships at 42% of their former linear base
color, with roughness 1, specular IOR level 0, metallic 0 and emission 0. Conveyor
rails use sRGB `#966B60`, roughness 1 and specular IOR level 0.
Other wood colors, including conveyor legs, retain their original albedo; they
receive the universal Faceted surface lighting without the crate's darkening.

Preserve the lower-height material ramp, 135% native sRGB grade, projection,
registered roots, geometry and complete animation timing. The ImageGen artwork
and procedural 2D effects remain 2D and are not relit in Blender. The prior
studies remain historical comparisons. This approval authorizes the full native
recapture and ticket closure once complete captures, publication and validation
are finished; the rollout record tracks that completion separately.

During the full-library transfer, a native pilot showed that the new diffuse
lighting washed out the cream floor. Apply a separate 42% linear albedo
calibration to floor materials while preserving procedural patterns and tile
borders. This rollout quality correction keeps the floor palette readable under
Faceted lighting; it is separate from the approved wood material treatment and
does not change floor geometry, projection or atlas resolution.

## ART-10 — UI uses the approved catalog and ImageGen (2026-10-19)

The user explicitly requires every UI-related ticket to inspect **Restaurant UI & item catalog** before implementation and to create corresponding UI elements with ImageGen instead of choosing an unrelated style. Reuse approved assets, follow current wireframes for behavior and the accepted B decision below for revised composition, preserve the transparent restaurant HUD, and inspect the underwater references for expedition-specific work. Keep dynamic labels/counts separate from generated artwork and retain source/prompt/reference provenance.

The [UI reference workflow](README.md#ui-reference-workflow-art-10-approved-2026-10-19) defines the implementation/review steps. Relevant normal, pressed, disabled, selected and specified NEW/MAX states must appear in the shared native gallery and full-scene phone/wider-portrait captures. Catalog branding, example values and illustrative controls do not add gameplay requirements. This applies prospectively to all remaining implementation tickets, beginning with #12; it does not reopen completed #33 world-art approval.

### Whole-screen UI family and undistorted framing — 2026-10-19

The user's issue #12 review rejected three defects: whole ImageGen buttons were stretched and acquired unequal padding; controls were generated in isolation without considering their neighbors; and passive containers retained generic engine styling. Begin each UI slice with a complete screen composition and an inventory of its interactive and passive surfaces, including tray/card backings, modal and recovery panels and toasts. Generate a coordinated ImageGen family using that composition and the catalog as common references. Shared materials, rims, corners, hierarchy, spacing and interaction states must work together.

Retain every full original output and generation record. Calibrate fixed corners/edges and symmetric content insets; use nine-slice framing only for documented plain spans or preserve the designed aspect ratio. Never stretch complete controls or icons. Scale the family uniformly and keep icons undistorted. Compare real full-scene phone and wider-window captures with the complete composition and catalog; provenance/hash verification alone cannot establish visual acceptance. These constraints apply to all remaining UI tickets. The accepted B decision below supersedes older layout and paging requirements while retaining control semantics and the transparent HUD.


### Accepted B — Indigo noren & warm ceramic (2026-10-19)

The user approved [the final B composition](../../assets/ui/editor/v4/raw/b-indigo-ceramic.png) and explicitly allowed creative UI changes beyond the old game layout. This is an approved production direction, rather than a pending concept. It governs #12 and the shared UI family for every future UI ticket, always read with the unchanged [restaurant item catalog](restaurant-item-catalog.png) and [restaurant world concept](restaurant-concept.png).

- Horizontal indigo cloth **People / Layout / Floor** categories above a warm cream drawer; **three visible Layout inventory items with paging**.
- A compact grouped, labeled **Rotate / Return** capsule attached to selection. Return keeps the object in storage; its icon is a box with an inward arrow.
- **Vermilion Live** as the primary action, **quiet cream Shop** and **neutral ivory/navy stock badges**.
- Coordinated generated artwork and calibrated framing for interactive controls and passive drawers, trays, cards, panels and feedback surfaces; dynamic labels/counts remain native text.

This decision explicitly supersedes the earlier right-side category stack, two-inventory-items-per-page requirement and fixed UI control placements for #12. Preserve category/action semantics, placement/drag/rotation/return, paging, edit pause, autosave/recovery and system Back. Do not add Save/Done/Cancel/Undo/page numbers. The world pictured in B is composition guidance; the approval does not replace registered native sprites, projection, roots, footprints or the locked world-art decisions. A and v2/v3 sources remain historical comparisons; only selected B is normative.

The historical production extraction lives in `assets/ui/editor/v5/`. Retain its full generated coordinated sheets, exact prompts, references/hashes and packing procedure unchanged. Manifest version 2 traces its active and passive regions to those sheets and records source slices, fixed logical edges and symmetric content calibration. Passing provenance checks is necessary for packaging and does not replace full-scene native visual review.

### B refinement — independent noren and compact goods (2026-10-19)

The user's [latest #12 amendment](../../godot/review/12/noren-revision/contract.md) requests separate hanging People/Layout/Floor cloth panels and a visible rod, with cream behind the seams; a bottom dock; subtle press-in feedback beginning on pointer down; smaller goods and a shorter drawer; and narrower paging surfaces that match the goods material and height. Layout now shows four goods per page, while People keeps three profiles per page. Shop, Live, Editing and coin displays use rounded capsules; cream Editing/coin pills supersede the older unbacked HUD labels. Surface separation comes from shadows, without dark borders. Curtain icons use the monochrome Floor icon as the accepted family reference.

The goods shown in editor inventory use editable native Blender three-quarter renders, including floor-tile thickness. This authorizes a separate UI preview camera; the approved world sprites, projection, roots and footprints remain governed by their existing contracts. UI artwork uses a coordinated v6 ImageGen family with full original outputs, exact prompts/reference hashes, unchanged crop pixels and uniform calibrated corners. Technical PNG packing is allowed; goods artwork is rendered in Blender through MCP.

This is the current implementation direction and a request for revision, not final visual approval. Keep v5 sources, generation records and 0.4.1 captures unchanged as history. Continue issue #12 only; the amendment adds no gameplay mechanics and does not start a later ticket.

### Rounded pill minimum height (2026-10-19)

The user rejected pill surfaces whose sides became pointed when compressed vertically. The current v6 neutral, pressed, primary, primary-pressed and disabled controls, coin/Editing panel, contextual capsule and error toast therefore require a **100 logical-unit minimum height**, with the uniformly scaled complete source height as an additional lower bound. Store `minimum_height` in authored calibration, source registration and runtime style; the shared native style enforces that minimum. This changes calibration and layout, preserving the generated source pixels.
