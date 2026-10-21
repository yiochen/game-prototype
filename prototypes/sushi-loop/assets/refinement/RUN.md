# Warm soft catalog rollout

This is ongoing work, not a completed batch. Continue through the whole catalog and then update the existing Godot game. User explicitly requires a fresh editor and judge instance for every object. Reuse that object's pair for revisions, never for another object.

- Worktree: `/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype`, branch `codex/warm-soft-catalog`. Primary checkout has unrelated local changes; leave it alone.
- Draft PR: https://github.com/yiochen/game-prototype/pull/37 (already attached to task).
- Stable review URL: https://deploy-preview-37--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library
- Git pushes update the real PR Deploy Preview automatically. Site is `game-prototypes-yiochen`, ID `a05448cf-3d0c-4100-9b1a-6d8a0d28c886`. Never deploy to Midnight Noodle or production.
- Scope: 118 catalog entries, excluding the three restaurant floors at the user's request. Keep `floor-cream`, `floor-blue-wave`, `floor-checker` unchanged. Underwater floor remains in scope. `progress.json` is authoritative for status/agent IDs; `excluded-restaurant-floors.json` locks the retained floors.
- New user direction for follow-on objects: give ImageGen freedom to improve modeling, structure and decorations. Use `prompts/imagegen-target.txt` plus `style/modeling-policy.json` v2. Pass that freedom through the native editor and judge briefs; original part counts/weak shapes are not constraints. Camera, registration, gameplay attachments, clearance, modular joins and continuity remain fixed. Already sealed work stays immutable. The backdrop-wall target was regenerated as v2 under this direction; its fresh pair is working from it. Its interior may change, with the entrance family capture/material/connection settings bound as technical resources.
- Source library is `../production/library.json`. 105 original native3D sources, 13 explicitly 2D entries. Do not invent Blender sources for the 2D entries; retain honest native2D provenance.

## Per object

Read `/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md` and its role prompts. Existing object directories contain copies. `prompts/native-capture-notes.md` records technical capture lessons without previous art judgments.

1. Generate ImageGen style target from the actual exported snapshot plus style-only `style/warm-soft-reference.png`; preserve raw target and exact prompt. Reuse selected existing targets where appropriate. Target drift/halos are not geometry authority.
2. `tools/prepare_object.py <id> --target <raw-target>` prepares source backup, snapshot, reduced contract and fresh role prompts. Use bundled Python below (system Python lacks Pillow).
3. Spawn fresh judge/editor with `fork_turns:none`, raw source/reference/contract, no old art opinions. Editor independently inspects before reading initial critique. Judge writes `reviews/initial.json` and `criteria.json`. Root freezes criteria in `brief.json`; qualityCriteria must be a nonempty DICT (wrap a list as `{aestheticGoals:[...]}`).
4. Editor saves immutable native project, recipe, all required views, every animation frame, original-layout atlases, motion/background/repetition previews, actual validation and delivery.json. Do not selfapprove. Only approved native pixels reach production.
5. `python3 tools/seal_object.py <id> --round round-NN` hashes the entire handoff via installed skill helper. Dispatch same object's judge to inspect actual PNGs/every declared preview, technical evidence and exact packet. Review must bind candidatePacketSHA256, verdict approve, blockers[], inspectedFiles exact packet-relative render/preview paths. Revisions get a new immutable round.
6. `tools/promote_object.py <id> --round round-NN` dry-runs approval, layout and raw/atlas pixel checks. Add `--apply` only after approval. Copies exact bytes, saves rollback object, corrects captureScale2 provenance, updates production source links/metadata and progress. Never rerender approved source.
7. Run relevant engine/integrity tests, build, phone/landscape browser load/visual checks. Commit/push ONE approved object at a time; wait for successful deploy before claiming live. Preserve all rounds and approvals. Force-add the new production source-captures (parent .gitignore ignores them); candidate raw PNGs are ordinary tracked files. Git deduplicates identical copies.

Bundled Pillow Python: `/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.

Useful commands from repository root:

```sh
node --test prototypes/sushi-loop/tests/*.test.js
npm run build > /tmp/warm-catalog-build.log 2>&1
gh pr checks 37 --json name,state,link,bucket --repo yiochen/game-prototype
git push origin codex/warm-soft-catalog
```

Local review Vite server is port4178 (original primary dev server remains4176). Stable object links use `#object-<id>`. Browser smoke selector `.object-refinement[data-refinement-status="approved"]`; catalog filter `.object-library-filters select` value `refined`. The studio intentionally has a phone frame on desktop.

## Current source caveats

- Sign target prompt miscounted two boards; actual native sign has THREE plank meshes, four nails and two posts. Original native construction is authoritative. Judge was told to preserve three, with target as material/light reference; freeze that explicitly before editor submission.
- Modular belts/walls/terrain need shared connection/material constraints and joined previews, not just isolated props. Protect connection planes and animation/UV phase across the family while still using fresh object-specific agents.
- `seal_object.py` and `promote_object.py` currently target native Blender delivery. Extend honestly for existing2D source entries when reaching them; preserve facing policy and fixed-frame registration.

## Final Godot integration remains required

Existing project: `prototypes/sushi-loop/godot/project.godot`. `godot/tools/sync_catalog.py` copies a selected catalog subset and supports `--check`. Inspect `godot/tools/catalog_contract.py` and `godot/scripts/art_book.gd`; separate chef/recipe/feedback variant atlas overlays may override catalog sprites. Ensure the running game actually uses refined assets, including relevant overlays, without losing identities/states. Preserve Indigo/noren UI and behavior. Run Godot tests/import/headless/native visual checks and portrait/landscape checks; no device installation or production deployment was requested.

## Native modular seam findings

BOX filtering at width1 prevents transparent-boundary coverage deficits in these native captures. Denoising can introduce RGB dark/light ringing against alpha boundaries even when assembled alpha is255; the entrance family uses256samples with denoisingOFF. Exposed internal cut faces can also differ from a connected top surface because Cycles evaluates the real surface hemisphere even with a modified shading normal. The dock round07 uses a native procedural camera-ray cut-face field with ordinary BSDF transport, common across facings, without geometry or raster changes. These are technical diagnoses, not blanket appearance approval. Require RGB as well as alpha comparisons, native AND independent assembly, and logical-size inspection. Do not extend geometry beyond frozen connecting planes to conceal seams.

The backdrop native camera record nests its per-asset fields under assets.gate/wall. Promotion selects the unique exact frame/anchor/scale match and flattens those fields without changing numeric camera/contact data; retains exact approved source record plus hash. Front contact [0,-.5,0] differs from world origin. Tests verify exact normalization.

Godot integration audit: chef-variants adds Omar hold-cucumber/load-cucumber; recipe-variants adds customer eat-salmon/seated-wait-empty; feedback-variants adds happy-smile transitions. Retain and refine these native game-specific clips with their corresponding object's pair so final runtime does not retain old-style overlays. Existing editor inventory goods also use separate native Blender three-quarter captures; account for the refined model/materials while preserving the accepted UI contract.

## Conveyor consumer filtering investigation

Belt-straight-n round08 native art/geometry/timing/raw joins passed independent inspection, but its judge verdict is revise for current Godot consumer rail seams. Preserve sealed round08. Exact project importer_defaults.texture has mipmaps/generate=true; do not infer current behavior from standalone default-import-false PNGs. Actual Godot diagnostics/belt-filtering-game-import captures true default flags and shows direct-vs-precomposed maxRGBA[50,22,16,64] at logical128 and[38,20,24,60] at phone32. Native art itself is not approved for publishing while this consumer blocker remains. Same object's editor is exploring a native composition renderer in round09; root must integrate/test any proposed helper preserving painterorder/hitpicking/UI.

Root diagnostics/belt-native-composition proves a native256-cell offscreen composition followed by premultiplied-alpha area downsampling is a promising option; only a prototype, no game change or final approval. Plain nearest as a one-line replacement is NOT proven. Transparent Godot ViewportTexture is premultiplied; use blend_premul_alpha on its consumer. See official docs https://docs.godotengine.org/en/stable/tutorials/shaders/using_viewport_as_texture.html . Keep original technical evidence, never mutate reviewed candidates for further tests.
