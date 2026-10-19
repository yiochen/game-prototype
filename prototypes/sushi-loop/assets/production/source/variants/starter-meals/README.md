# Starter meal variants · issue 10

Open **starter-meals-project.blend** to iterate on the four customers in the saved native camera. The frozen **starter-meals.blend** library is the exact SHA-bound render source retained beside it. `finalized-project.json` links the editable normal project to that capture source without geometry or animation edits.

These game-specific clips extend the approved #33 library; they never replace its originals:

- `eat-salmon`: existing eating animation with the original approved ImageGen salmon cutout attached to the evaluated palms. Only the food plane's fixed source UV rectangle/aspect and image reference change.
- `seated-wait-empty`: existing seated breathing/wait action with the held-food plane's visibility keys set to hidden. The body, hands, bones, weights and attachment actions stay unchanged.

All four customers retain ordinary 35° C125 geometry, the same root `(96,248)`, complete `192×320` logical frames, 12 frames at 12 fps in N/E/S/W, and the approved Faceted lighting and native 135% grade. `authorship.json` records the exact user prompt, source hashes, body mesh/rest-bone hashes and unchanged action hashes. The live user's unrelated Blender file and approved collections remain unchanged.

`author_meals.py` was executed through Blender MCP. `capture_worker.py` captured the saved derivative headlessly at 4× and 32 samples after MCP capture stopped. `native-audit.json` verifies all 384 pose/facing samples: exact original salmon packed bytes, food hidden for every waiting sample, food visible while eating, unchanged body/rest geometry and unchanged body/attachment actions. `publication.json` retains every source PNG receipt and the corresponding complete runtime-frame pixel hash.

Packing is the only raster operation: uniformly resample each complete `768×1280` capture to `384×640` with LANCZOS, then pack six columns. No silhouette fitting, alpha masking, color adjustment or per-pose scaling is applied. The raw capture run lives at `/private/tmp/sushi10-meal-raw`; the editable native source, all capture receipts, registration, scripts and packed runtime sprites are retained in the repository. Re-render from the saved source if raw captures are needed again.

Run `godot/tools/verify_recipe_variants.py` with system Python to verify the native/source/receipt provenance, registration, frame rectangles, dimensions, hashes and complete runtime payload. Android packaging calls the same stdlib verifier; only the runtime manifest and PNG atlases ship, not these authoring files.
