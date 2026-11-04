# Issue #22 · native Godot evidence

Approved HTML composition: `design/expedition-currents-preview/` (review link in `review/22/prototype/deploy.json`). Decisions: the travel boost is presented as a **Shield** and keeps its speed increase; the bonus passage ride is **automatic**.

## Review video

`expedition-22-review.mp4` (390 × 844, 30 fps, about 47 s) is recorded from the real game with injected touches; a ring marks the finger:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/record_expedition.gd --visible --fixed-fps 30 \
    --resolution 390x844 --timeout 1500 --output <frames>
ffmpeg -framerate 30 -i <frames>/frame-%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 expedition-22-review.mp4
```

It dives from the preparation screen, then cuts ahead to each feature in route order: a current field (the finger lets go and the ship drifts with the flow lines), the portal (spin into the whirlpool, iris, automatic passage ride with dimmed arrows and "The current carries you", iris out to the rejoin outflow), and the shield (pickup, shield bubble, ploughing through rock without damage), then Pause and the resume countdown. The script asserts the drift, the passage pickups and rejoin, and the undamaged hull (0 failures). `--issue21` replays the original #21 sequence.

## Screenshots

`phone/` (390 × 844) and `wide/` (1100 × 820, portrait-contained) from `tests/capture_expedition_features.gd`:

| File | State |
|---|---|
| 01 | Current field: seabed wash and flow lines; the released ship drifting |
| 02–04 | Shield pickup ahead; shield active (toast, bubble with draining rim); rock bump with no damage |
| 05–06 | Portal approach (stone ring, live whirlpool); entry transition (ship spinning into the whirlpool) |
| 07 | Passage ride: deeper tint, forward flow, gold ribbon, dimmed arrows and the ride label |
| 08–09 | Exit iris; rejoin outflow on the main route |
| 10 | Spent portal (still, dim pool) |
| 11 | Paused with features on screen |

## Rules

- `tests/expedition_features_tests.gd` (36 checks): feature slots in the plan, no shield or portal in the encounter, current push added to steering and continuing after release, shield speed/immunity/no multiplier/expiry/encounter cut-off/pause freeze, portal optional and spent on entry, automatic ride ignoring input, passage pickups counted once across save/reopen, rejoin past the next chunk, corrupt feature saves rejected, and pre-#22 runs keeping route version 1.
- `tests/expedition_tests.gd` (174) and `tests/expedition_route_tests.gd` (parity with the JS reference, now including feature-plan runs) pass unchanged in intent.
