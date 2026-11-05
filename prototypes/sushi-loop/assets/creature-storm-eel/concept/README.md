# Storm Eel boss — concept round 1 (issue #23)

Design references only, not registered sprites. Provider: codex image_gen via `sprite-gen gen --provider codex --model gpt-5.6-sol`.
Prompt = `common.txt` + the direction's suffix (`a.txt`/`b.txt`/`c.txt` hold the full exact prompts). Raw outputs: `concept-*.png.raw.png`; run reports: `concept-*.report.json`.

| Concept | Direction |
|---|---|
| concept-a.png | A — Thunder Serpent (flowing frilled mane, glowing barbels) |
| concept-b.png | B — Armored Storm Eel (faceted bands, crystal spines) |
| concept-c.png | C — Moray Storm Eel (big head, nub teeth, lantern spots) |

Reference roles (in order): style, gameplay scale/camera, identity.

651703b4e09da6b025e22239d4d41840bf0696d2836676ef9719aa3b88996f64  refs/underwater-item-catalog.png
dcdaaf966e2d630ddfdfd54e1813e18efc6e4c7af3b9a167c8ce1ec71ab3f7a8  refs/underwater-concept.png
e5adeac8bf6e7b95ee8595e632fd7e7785ed34e7259dbca1cdd368d6522723eb  refs/existing-eel-original.png

## Round 2 — ugly-cute refinement of C (user picked C, "ugly cute")

`r2/`: refs = concept-c.png (edit target/identity), underwater-item-catalog.png (style). Full prompts in `r2/c1.txt`, `r2/c2.txt`.

| Concept | Direction |
|---|---|
| r2/concept-c1.png | C1 — grumpy: underbite tusks, droopy lids, bulbous snout, warty bumps, floppy ear-frills |
| r2/concept-c2.png | C2 — goofy oaf: gap-toothed grin, mismatched eyes, mottled skin, barnacles, trumpet ear-frills |
