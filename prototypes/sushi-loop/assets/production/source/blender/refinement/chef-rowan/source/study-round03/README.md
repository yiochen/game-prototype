# Rowan global-depth diagnostic, round03

Active frozen brief: `brief-v3-food-depth.json`. No criteria were changed.

The study renders112 new native representatives: four common scalars
0.50/0.525/0.55/0.575, four actual facings, hold frames1/4/10 and load
frames1/6/7/12. Every scalar passes all192 registered projection/ray checks.
Each native variant is saved/reopened from the exact round01 baseline before
measurement and capture; only permitted plane-depth fields are changed.
No full192 capture or submitted round03 candidate was started.

The primary comparisons are `sheets/all-facing-hold01-load06-gray.png` and
its light/dark siblings. Every tile is a complete native384x640 frame uniformly
reduced to the exact logical192x320, with identical registration; no fitting.
Rows are .45 baseline02, .50, .525, .55, .575, .60 baseline01. Columns are
hold1 N/E/S/W followed by load6 N/E/S/W. Fixed-window diagnostics use the same
original native pixel rectangle80,320,304,475 in every image, without fitting.
All other sampled extrema have full logical sheets on all three backgrounds.

The editor finds no acceptable shared window among these finer samples:
.50/.525 keep N clean but bury the W hold salmon; .55 starts a rear plate line
while W still loses upper salmon; .575 restores more W food but produces a
clear rear plate crescent. `observations.json` records the exact observations
and finite-sampling limit for coordinator/judge reconciliation. It is not a
self-approval or an amended aesthetic standard.

Reproduce in a scratch object copy with active brief, inputs/baseline-round01.blend,
inputs/source-rig.json, source/resources/original-native-actions.py, and this
study directory. Run from the object root:

```sh
/opt/homebrew/bin/blender -b inputs/baseline-round01.blend \
  --python source/study-round03/depth-window-study.py
```

The assembly script additionally reads the existing sealed round01/02 PNG
baselines for comparison rows. Those are not required for native study renders.
`observations.json` verifies all old01/02 packet-bound files remain unchanged.
