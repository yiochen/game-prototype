# Faceted lighting production rollout — issue 33

On 2026-10-19 the user approved the Faceted lighting treatment, the matte wood
material and the muted-clay conveyor rails, and requested every native sprite
be regenerated before closing issue 33. This is authorization to roll out and
finish the asset ticket, superseding earlier pending-review language.

The selected treatment uses matte Principled surfaces, a centered 140 W overhead
area light and four equal 100 W cardinal fills. The material-height ramp keeps
lower surfaces dark; native 135% sRGB contrast preserves alpha. Crate wood uses
the approved lower linear albedo with roughness 1 and specular IOR level 0.
Conveyor rails use sRGB `#966B60`, roughness 1 and specular IOR level 0. Keep all
registered camera profiles, roots, geometry and animation samples unchanged.
Other wood colors, including the conveyor legs, retain their original albedo
under the new universal lighting; the crate-only darkening is not global.

Scope: regenerate the 104 active native Blender entries and every declared
clip/facing. Preserve the 13 ImageGen/procedural 2D entries. The active review
catalog remains the wireframe site; Godot Android remains the eventual game
target. This checkout contains editable Godot effect source but no Godot game
project. Validating sprite imports does not claim a completed Android game.

The complete native capture batch is published and independently validated.
User approval is recorded in the runtime manifest, and the current native index
identifies the new project. Godot resource verification and final browser checks
pass. All six actual tiled-preview recordings are complete. The asset milestone
is ready for the final live-deployment check and issue closure.

The first lighting-transfer pilot exposed washed-out floor color under the new
diffuse illumination. Floor materials therefore receive a separate 42% linear
albedo calibration before the native grade, preserving their authored palette,
procedural pattern and visible tile borders. This is a floor readability fix,
distinct from the selected wood material adjustment. That first pilot is not
published as production art; the corrected frozen project is recaptured.

## Frozen source and capture results

- Final editable project: SHA-256
  `b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6`.
  The separate original MCP export, its report and the normal-project
  finalization receipt retain the full identity chain. The generated
  `finalized-export-report.json` describes both source files without assigning
  the finalized hash to the original export.
- All 104 native entries and 9,390 native frames pass receipt identity,
  dimensions, frame completeness, unique animation and source checks.
  Every animated group has at least six distinct visible frames; every directed
  conveyor retains 24 unique frames.
- All 117 catalog entries, 11,082 frame/facing contexts and 967 atlas PNGs pass
  the independent publication audit. Every native cell is pixel-exact against
  the declared full-frame 4×→2× LANCZOS sample; the 13 flat artwork/effect
  entries remain byte-identical.
- Geometry, roots, camera registration and animation cohorts match the preceding
  native project. Alpha is byte-identical for 9,385 of 9,390 frames. Five
  translucent-ray frames differ only at 2–7 pixels by at most 5/255, with the
  same alpha bounds; the exception audit records these measured differences.
- The production crate and belt match the approved material study in all four
  facings within the expected 32-versus-64-sample render difference: mean opaque
  RGB error below 0.5/255, with no top-region clipping.
- Maximum published atlas dimensions are 7360 × 4224; all retain complete 2×
  frames. See `audit.md` and the native, receipt, pixel, alpha-exception,
  selected-reference and published-atlas JSON reports.
- All 189 engine/helper tests and the final production build pass. Godot import
  verification passes on Godot 4.7.2: all 117 objects, 967 imported textures and
  11,082 `AtlasTexture`/`SpriteFrames` frame contexts, with zero errors. Imported
  dimensions match every registered atlas; resources are released per clip.
  Browser coverage finishes with **76 passed and one expected queued-item skip**.
  The initial full run found a navigation assertion settling at two pixels rather
  than exact zero. A bounded ≤2-pixel top tolerance now covers that browser
  rounding, and all three targeted navigation sizes pass; `browser.log` and
  `browser-navigation.log` preserve the initial result and corrected rerun.
  All six actual tiled-preview videos are complete, with served-atlas hashes
  checked against the approved production PNGs. Every recorded chef/customer
  state shows all 12 native frames; the connected conveyor shows all 24 frames.
  Video dimensions/durations are independently checked with ffprobe. The six
  WebMs total 6.24 MB; redundant test-run snapshots/traces are removed.

## Actual tiled-preview recordings

| Preview | Phone | Close-up |
| --- | --- | --- |
| Chef work and load | [Video](videos/chef-work-load-phone.webm) · [Still](videos/chef-work-load-phone.png) | [Video](videos/chef-work-load-closeup.webm) · [Still](videos/chef-work-load-closeup.png) |
| Customer walk, sit and eat | [Video](videos/customer-walk-sit-eat-phone.webm) · [Still](videos/customer-walk-sit-eat-phone.png) | [Video](videos/customer-walk-sit-eat-closeup.webm) · [Still](videos/customer-walk-sit-eat-closeup.png) |
| Connected conveyor | [Video](videos/connected-conveyor-phone.webm) · [Still](videos/connected-conveyor-phone.png) | [Video](videos/connected-conveyor-closeup.webm) · [Still](videos/connected-conveyor-closeup.png) |

These are recordings of the real catalog pages playing the final registered
sprites on their tile grids, with the original UI and connected belt fixture.
`videos/recordings.json` retains source hashes, observed frame coverage and video
metadata. Complete-scene phone and desktop captures are
[restaurant 320](screenshots/restaurant-320.png),
[restaurant 1440](screenshots/restaurant-1440.png),
[underwater 320](screenshots/underwater-320.png) and
[underwater 1440](screenshots/underwater-1440.png).
`browser-summary.json` records the final 76-pass/one-skip outcome and the focused
navigation rerun; original logs remain available.

The individual 4× source PNGs and intermediate packing sheets are **local,
ignored render intermediates**, present in the new raw batch and registered
capture folders. They are not all tracked in Git. Git retains the complete 2×
runtime atlases, editable finalized/original Blender projects, frozen recipes,
native records, packing guides, per-frame source hashes and independent audits.
This keeps source iteration and full-frame provenance without duplicating the
entire render batch in repository history.

## Texture packing and Godot verification

Runtime packing retains complete authored frames at 2× logical resolution.
Columns stay near the established six-column layout while keeping both atlas
dimensions at or below 8192 pixels. The eight dock-cover covered/uncover facing
atlases previously measured 8832 × 2816; their five-column layout is
7360 × 4224, with identical per-frame size, ground root and timing. No sprite is
shrunk or fitted to its visible silhouette. The packing fingerprint records the
chosen columns and texture cap.

After publication, validate the exact active sprites in a disposable Godot
project:

```sh
python3 prototypes/sushi-loop/review/33/faceted-rollout/validate_godot_imports.py \
  --repo "$PWD"
```

The helper copies the active manifest, referenced atlases and editable Godot
effect script into a fresh temporary project; it never puts import sidecars in
the repository. It runs the actual Godot editor importer, loads every atlas,
checks its imported dimensions and every frame rectangle, and constructs each
declared animation as `SpriteFrames` of `AtlasTexture` resources. Source hashes
and logs identify the tested publication. This verifies engine resource
compatibility; it is not an Android APK, gameplay or device performance test.
