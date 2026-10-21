# Warm soft catalog rollout

This is ongoing work, not a completed batch. Continue through the whole catalog and then update the existing Godot game. User explicitly requires a fresh editor and judge instance for every object. Reuse that object's pair for revisions, never for another object.

- Worktree: `/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype`, branch `codex/warm-soft-catalog`. Primary checkout has unrelated local changes; leave it alone.
- Draft PR: https://github.com/yiochen/game-prototype/pull/37 (already attached to task).
- Stable review URL: https://deploy-preview-37--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-library
- Git pushes update the real PR Deploy Preview automatically. Site is `game-prototypes-yiochen`, ID `a05448cf-3d0c-4100-9b1a-6d8a0d28c886`. Never deploy to Midnight Noodle or production.
- Scope: 118 catalog entries, excluding the three restaurant floors at the user's request. Keep `floor-cream`, `floor-blue-wave`, `floor-checker` unchanged. Underwater floor remains in scope. `progress.json` is authoritative for status/agent IDs; `excluded-restaurant-floors.json` locks the retained floors.
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
