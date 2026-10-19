# Full art-library revision — issue 33

User authorization: 2026-10-19 full revamp request, including 34 pasted feedback
items. This review remains pending user approval; issue 33 is not closed.

## Shared treatment

All 104 native production objects are rebuilt with the approved 70% environment
projection or documented ordinary camera exception, native 135% sRGB compositor,
and darker lower surfaces. Emission materials and zero world/light strength avoid
a directional key light. Camera-symmetric facet tone retains form. Floors have
explicit narrow cell borders. The compositor preserves original alpha; production
sprites receive no extra CSS contrast.

Twelve production characters use C125 with individual identities, costumes and
fuller hair, rounded faces, very short legs and tiny feet. Native gait travel is
0.225 physical cells per one-second walk cycle (panic two cycles/second). The
ordinary35 camera projects that travel to 0.225 square-floor cells E/W and
0.129055 N/S. Published locomotion metadata records both; the restaurant walker
uses facing-specific segment timing to cancel planted-foot motion. All anatomy and
knife poses fit one cell; ImageGen food is a separate 0.35-cell-wide camera-facing plane aligned
to the evaluated palms and biased along the camera ray to prevent torso occlusion.

Concept-derived cobalt banks, pink/violet coral fans, branching kelp, pale column
and mossy face replace the exploratory underwater decorations. Tall decor uses
ordinary35 upper projection plus square footing below Z=.42; the complete
silhouette cap is three tiles across facings. Original concept images remain
unchanged in the review site.

## Feedback coverage

| User items | Implementation / review target |
| --- | --- |
| 1 | Four reaction bubbles and ambient bubbles use separate transparent ImageGen 2D originals. |
| 2, 13 | Blackboard is blank, single player-facing S, physically in front tile band, sharing chef cell. |
| 3, 4 | All wall tiers use matching native miter sections and connected straight/corner fixtures. |
| 5 | Angular plant has dense full-cell foliage and substantial ground mass. |
| 6 | Barrel has curved bulging stave profile and thick hoops. |
| 7 | Crate fills 0.979 cells in width/depth with thick frames and braces. |
| 8 | Blank sign is S-only in the front band, shown cooccupying a planted cell. |
| 9 | Slate rock has broad uneven crown and full-cell footing. |
| 10 | Dock post/rope are thicker; adjoining half-posts reconstruct a full post. |
| 11, 12 | All 20 belt modules have thicker red borders and 0.16-cell legs; deck paths, UV flow and 24-frame travel are retained. Corner legs remain under the curve. |
| 14 | All three sushi dishes are transparent ImageGen 2D art, including held food. |
| 15 | Sofa spans its declared two-cell width; faded upholstery, torn seat and stuffing convey age. |
| 16 | Muted wrecked car has jagged broken glass, dark cabin openings, rust and bent parts. |
| 17 | Collapsed shelf fills its declared two-cell width. |
| 18 | Dock cover clarified as a 3×3 overhead weather tarp, with ridge, rolled hems, ties, support frame and a folding animation; shown above dock/sub/workshop. |
| 19, 20 | Cobalt wall family has full-cell contact mass and shared port sections. |
| 21–25 | Current, swirl, eel warning hatch, lightning and discharge use procedural 2D atlases with editable Godot drawing source. Their 3D source entries are removed. |
| 26–33 | Eight obsolete A/B garden bundles are removed from the active catalog and full-scene fixtures. Individual tiles layer over continuous floors. Historical sources remain only as provenance. |
| 34 | Every production floor style has a readable registered border. |

## Reproduction

Native authoring recipes are in `assets/production/source/blender/`:
`build_art_rollout.py`, `production_library.py`, `catalog_art_revision.py`,
`catalog_concept_decor.py`, `character_builders.py`, `character_composition.py`,
`catalog_style.py` and the shared native-action baker. The canonical editable
project is `sushi-loop-world-library.blend`. Registered sprite publication uses
`capture_worker.py` then `publish_captures.py`. The 2D originals, exact generation
prompts, alpha registration, atlas publisher and Godot effects source are in
`assets/production/source/2d/`.

Evidence from separate native geometry/rig audits is linked from
[native props](native-props.md) and `../character-rollout/`. Full capture and browser verification results are recorded below.


## Final verification

- Canonical editable project: SHA256 `c02e04d6c90e34afce2b0895328d4a1e26d47817ce9d38fb2b458fa3e766fc1f`.
- Independent native audit: 104 objects, 525 materials, 2,580 evaluated pose/facing combinations passed.
- Complete 4× source pixel audit: 104 objects / 9,390 frames passed, no clipping or insufficient visible animation variation.
- Published 2× atlas audit: all 117 objects / 11,082 frame-facing contexts passed; no animated clip has fewer than six distinct visible frames.
- 183 repository engine/helper tests and the production Vite build passed. The editable Godot 2D effect source also passed the Godot 4 parser check.
- Responsive browser coverage includes object playback, blank signs/boards, 2D source links, independent comments, Prev/Next navigation, single document scrolling and both complete scenes. Evidence is retained in the browser logs and 320/844/1440-pixel scene screenshots here. The initial landscape navigation check sampled a transient 3px scroll position; an exact-zero polling assertion now waits for layout to settle, and the focused case passes.
- Removed 272 unreferenced runtime atlases (248 MB). The active catalog has 117 objects and 967 distinct atlas PNGs; shared 2D directions deliberately reference the same artwork.

See [feedback coverage](feedback-coverage.md) for all 34 requested changes and the availability limits of intermediate authoring snapshots. The final frozen project, render-time helpers, current recipes, registered capture records and original 2D artwork are retained. Final art approval remains pending; issue 33 stays open.
