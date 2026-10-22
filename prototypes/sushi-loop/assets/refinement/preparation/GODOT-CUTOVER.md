# Final Godot cutover

Status: pending. Follow `../integration-dependencies.json` for approval state. Target readiness is not native approval. Finish all in-scope catalog refinements, same-character held-food updates, customer empty/salmon variants and runtime variant approvals before the combined cutover. Keep the existing restaurant object selection, gameplay, saves, UI, picking and the three excluded restaurant floors.

The five approved inventory views and happy-smile overlay now have strict import adapters. Their integration regressions use disposable directories and leave the game's sprite payloads unchanged. Both legacy and refined provenance formats remain supported.

From the repository root, use a Python environment with Pillow for packing/tests:

```sh
python prototypes/sushi-loop/godot/tools/test_refinement_imports.py
python prototypes/sushi-loop/godot/tools/sync_catalog.py
python prototypes/sushi-loop/godot/tools/pack_refined_goods.py --output prototypes/sushi-loop/godot/assets/ui/editor-goods
python prototypes/sushi-loop/godot/tools/sync_refined_feedback.py --output prototypes/sushi-loop/godot/assets/feedback-variants
```

`sync_catalog.py` preserves the existing restaurant selection. The two explicit-output packers copy whole approved canvases/atlas bytes; they do not render, fit alpha bounds or alter the UI. The goods adapter retains the exact cream-floor native PNG and atlas crop. The feedback adapter refreshes library/source paths while retaining the approved 48-frame art and timing. Their validators use the standard library and verify packet/review bindings and exact pixels.

Still required: equally strict approved-per-character adapters for `verify_chef_variants.py` and `verify_recipe_variants.py`. Their legacy branches assume a single old Blender source and native scale4, whereas approved refinement bundles may have per-object sources and actual native scale2. Keep legacy checks intact; do not forge old worker receipts or claim a new source used that old capture setup. Use the same-object main packet/review, final variant receipt, exact native source, runtime manifest, all atlas regions and raw native frame hashes. Preserve Omar's two cucumber clips and all four customers' salmon/empty clips. Do not leave old-style variants over new bodies.

After every runtime payload is synchronized, verify catalog, goods, feedback, chef and meal provenance; run engine/build/package checks and native tests/captures in disposable projects. Inspect real phone and landscape scenes, feedback, inventory, motion, joins and picking. Refresh the integration ledger with exact final source/atlas hashes and evidence. The full cutover is not complete until these checks pass. No device installation, production deploy or gameplay expansion is part of this task.
