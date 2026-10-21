# Rowan round03 saved native source

Active frozen brief: `brief-v4-food-occlusion.json`. The editable
`source/round-03.blend` retains the exact round01 body, native knife, original
25-bone rig/24 action cohorts, materials, camera, light and render settings.
The canonical731x505 salmon remains a packed **2D image** on its unchanged
fullUV plane; it is not modeled3D food.

Only the plane's saved native XYZ camera-ray location drivers and explicit
provenance differ. They implement one continuous law from semantic root yaw:
`f=cos(rootYaw); d=.60-.15*max(0,-f)^2`. No state/frame/facing-label lookup,
external driver namespace, handler, visibility, material or pixel changes are
used. The original native yaw-cancellation driver is retained. The three location
drivers use saved native polynomial identity mappings (coefficients0,1)
rather than the default keyed identity, whose endpoint solver snaps tiny
values near zero; this preserves the continuous mathematical law in native
evaluation without any external namespace. All projected
corners/plate-bottom anchors remain invariant; physical food-root/palm paths
are unchanged.

## Saved-source native recapture

Use a scratch object copy containing the active brief, `inputs/`, the new
round03 source/capture/audit scripts, `source/resources/`, and
`source/inspection-v1/native-action-audit.json` plus
`source/inspection-v1/original-action-identity.json`. No production folder,
sibling object or original library is needed. From the copied object root:

```sh
/opt/homebrew/bin/blender -b source/round-03.blend \
  --python source/capture-round-03.py -- --preview
```

This evaluates all192 native records and renders20 actual representative
frames, including held/load in all four views and load midpoint. Use `--full`
to capture192 untouched384x640 native PNGs at the original12fps timing.
Outputs go under `candidates/round-03/`.

For the complete compact saved-source law/projection comparison, including
all192 and intermediate angles, run:

```sh
/opt/homebrew/bin/blender -b --python source/audit-round03-occlusion.py
```

This additionally uses declared `inputs/baseline-round01.blend`. Intermediate
angles invoke the same normal frame evaluation as capture; native hidden
billboard descendants can have stale evaluated matrices, so the receipt uses
the original composed parent/driver geometry and checks visible evaluated
matrices separately. It does not misidentify a stale hidden matrix as a quad.

`source/closed-package-round03-test.py` runs both audits in a closed copy,
asserts no linked libraries, redirects the packed image external filepath to
a nonexistent path, reloads its packed pixels, and captures the same20 frames
without saving the blend. Receipt and capture evidence are retained in
`source/portability-proof-round03/`.

## Reapply this narrow repair

This requires the exact supplied round01 baseline SHA-256
`9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024`:

```sh
/opt/homebrew/bin/blender -b inputs/baseline-round01.blend \
  --python source/round-03-recipe.py
```

It writes a new round03 blend and recipe receipt. This does not reconstruct
from the historical original production library. Historical reconstruction
requirements remain in the unchanged original `source/README.md`.

Presentation assembly uses `source/assemble-round-03.py` and the exact local
published neighbor/original sprite bytes in `source/round02-context-resources/`.
Those sprite assemblies are diagnostic context, not a single3D scene, and
are independent of native source rendering. The independent judge records
any final appearance decision separately.
