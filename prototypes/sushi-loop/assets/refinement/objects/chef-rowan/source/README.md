# Rowan round 01 native source

The saved editable project is `source/round-01.blend`, SHA-256
`9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024`.
It contains the native body, knife, original 25-bone rig and 24 action cohorts,
plus the exact canonical salmon as a **packed 2D image**. The salmon is not a
modeled 3D dish.

## Recapture the saved source

Work in a scratch copy of this object folder so reviewed exports remain
unchanged. Copy `brief-v2-food.json`, `inputs/`, and the entire `source/` folder;
no sibling object, production asset folder or original library is needed for
this path. Keep the supplied inspection JSON baselines and `source/resources/`.
Run from that copied object folder:

```sh
/opt/homebrew/bin/blender -b source/round-01.blend \
  --python source/capture-round-01.py -- --preview
```

This reopens the saved source, audits all 192 clip/facing/frame slots and
renders 20 representative PNGs, including hold/load in all four facings and
the middle of load. Outputs go to `candidates/round-01/preflight/`; the native
audit goes to `candidates/round-01/native-audit.json` inside the scratch copy.
For every native PNG at the fixed 384×640 capture and original 12 fps timing:

```sh
/opt/homebrew/bin/blender -b source/round-01.blend \
  --python source/capture-round-01.py -- --full
```

The full command writes 192 indexed PNGs into
`candidates/round-01/frames/`. Atlas/movie assembly is a separate step in
`source/assemble-round-01.py`; it also expects the supplemental and browser QA
receipts supplied with the delivered experiment.

`source/closed-package-test.py` is the portability test wrapper. It directs
the packed image's external path to a nonexistent path, reloads its packed
data, checks that no linked Blender libraries exist, and runs the same saved
source preview capture without saving the blend. The retained test receipt is
`source/portability-proof/receipt.json`.

## Reconstruct from the original library

`source/round-01-recipe.py` rebuilds the refined geometry/materials and writes
a new round blend. It requires the **untouched original library** with SHA-256
`b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6`.
This is a different operation from recapturing the saved refined blend:

```sh
/opt/homebrew/bin/blender -b /absolute/path/to/original-library.blend \
  --python source/round-01-recipe.py
```

Use a scratch experiment copy for reconstruction. The recipe checks the
original library hash and uses the existing canonical PNG and approval receipt
copies in `source/resources/` first, verifying their exact hashes. Sibling
paths in the frozen brief are fallback provenance locations used only if a
local dependency is absent. The original-library bytes remain an explicit
prerequisite for reconstruction; the closed-package test establishes saved
source recapture, not reconstruction without that original model.

The active brief is `brief-v2-food.json`. The original brief and criteria are
retained as history; the final approval is recorded separately by the judge.
