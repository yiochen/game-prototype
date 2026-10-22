# Final Godot cutover

Status: pending. Follow `../integration-dependencies.json` for approval state. Target readiness is not native approval. Finish all in-scope catalog refinements, same-character held-food updates, customer empty/salmon variants and runtime variant approvals before the combined cutover. Keep the existing restaurant object selection, gameplay, saves, UI, picking and the three excluded restaurant floors.

The five approved inventory views, happy-smile overlay, and per-character chef/customer runtime bundles now have strict import adapters. Their integration regressions use disposable directories and leave the game's sprite payloads unchanged. Both legacy and refined provenance formats remain supported.

From the repository root, use a Python environment with Pillow for packing/tests:

```sh
python prototypes/sushi-loop/godot/tools/test_refinement_imports.py
python prototypes/sushi-loop/godot/tools/sync_catalog.py
python prototypes/sushi-loop/godot/tools/pack_refined_goods.py --output prototypes/sushi-loop/godot/assets/ui/editor-goods
python prototypes/sushi-loop/godot/tools/sync_refined_feedback.py --output prototypes/sushi-loop/godot/assets/feedback-variants
python prototypes/sushi-loop/godot/tools/sync_refined_actor_variants.py --kind chef --output prototypes/sushi-loop/godot/assets/chef-variants
python prototypes/sushi-loop/godot/tools/sync_refined_actor_variants.py --kind recipe --output prototypes/sushi-loop/godot/assets/recipe-variants
```

`sync_catalog.py` preserves the existing restaurant selection. The two explicit-output packers copy whole approved canvases/atlas bytes; they do not render, fit alpha bounds or alter the UI. The goods adapter retains the exact cream-floor native PNG and atlas crop. The feedback adapter refreshes library/source paths while retaining the approved 48-frame art and timing. Their validators use the standard library and verify packet/review bindings and exact pixels.

The actor adapter requires a per-object `final/runtime-variant-approval.json`, the same main body packet/review, packet-bound exact editable native source, canonical food, 96 whole frames and eight atlases per object. It validates all complete RGBA cells, original roots, 12 fps and clip loop behavior. Omar's two cucumber clips pass the refined path in an isolated fixture. The four customer salmon/empty bundles are still pending their independent approvals; recipe cutover correctly refuses to proceed without them. The legacy chef and recipe checks remain intact, including their original single-source scale4 worker receipts. Do not forge those old receipts for a new per-character scale2 capture.

After every runtime payload is synchronized, verify catalog, goods, feedback, chef and meal provenance; run engine/build/package checks and native tests/captures in disposable projects. Inspect real phone and landscape scenes, feedback, inventory, motion, joins and picking. Refresh the integration ledger with exact final source/atlas hashes and evidence. The full cutover is not complete until these checks pass. No device installation, production deploy or gameplay expansion is part of this task.
