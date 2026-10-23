# Rowan round 02: saved native source and depth repair

Active brief: `brief-v3-food-depth.json`. `source/round-02.blend` is the editable
round01 source with only the globally shared 2D food camera-ray depth reduced
from 0.60 to 0.45 world cells. Body, native knife, rig, actions, materials,
camera, lights, canonical PNG pixels/UV/plane mesh and physical food root are
preserved. The exact canonical salmon remains a packed **2D image**, not 3D food.

## Recapture the saved source

Use a scratch copy of this object folder. Include the active versioned brief,
`inputs/`, `source/round-02.blend`, `source/capture-round-02.py`,
`source/closed-package-round02-test.py`, `source/resources/`, and the two files
`source/inspection-v1/native-action-audit.json` and
`source/inspection-v1/original-action-identity.json`. The saved-source path needs
no sibling object, production folder or original Blender library. From the
copied object folder run:

```sh
/opt/homebrew/bin/blender -b source/round-02.blend \
  --python source/capture-round-02.py -- --preview
```

This audits all192 original pose slots and renders20 representative frames,
including hold/load in all four facings and the load middle. To render all192:

```sh
/opt/homebrew/bin/blender -b source/round-02.blend \
  --python source/capture-round-02.py -- --full
```

Outputs are under `candidates/round-02/`. `--preview` uses `preflight/` and
`--full` uses `frames/`. Native rendering is independent of the external PNG
filepath because the canonical image is packed in the blend.
`closed-package-round02-test.py` explicitly redirects that filepath in memory
to a nonexistent path and reloads the packed image before running the preview
command. The recorded closed-copy receipt is in
`source/portability-proof-round02/receipt.json`.

## Reapply the depth repair

This operation requires the exact round01 baseline SHA-256
`9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024`,
provided as `inputs/baseline-round01.blend`. It does not reconstruct the body
from the old production library:

```sh
/opt/homebrew/bin/blender -b inputs/baseline-round01.blend \
  --python source/round-02-recipe.py
```

The recipe writes `source/round-02.blend` and `source/round-02-recipe.json`.
For the historical original-library reconstruction requirements see the
immutable `source/README.md` and round01 recipe; that is a separate operation.

Atlas/playback/context assembly is `source/assemble-round-02.py`. It reads
published neighboring sprite assets for diagnostic assemblies; those are
bound in the round02 resource closure. That separate presentation step is not
a dependency of saved-source native recapture. Technical audits and any
independent visual decision are recorded separately.
