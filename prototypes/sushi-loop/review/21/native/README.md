# Issue #21 · native Godot evidence

Captured from the real game through `godot/tests/capture_expedition.gd` in an isolated test project and save identity:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/capture_expedition.gd --visible --resolution 390x844 --output prototypes/sushi-loop/review/21/native/phone
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/capture_expedition.gd --visible --resolution 1100x820 --output prototypes/sushi-loop/review/21/native/wide
```

`phone/` (390 × 844) and `wide/` (1100 × 820, portrait-contained) each hold the same 14 states:

| File | State |
|---|---|
| 00 | Restaurant with the revealed dock, battery full |
| 01 | Underwater preparation: the ship cruises the route's launch lead-in under on-screen text, Sushi Bar exit; pressing the water starts the dive from there |
| 02–03 | Travel: HUD (hull left, run salvage beside it, Pause right), camera following the ship, landmarks, glowing gold, particle bubbles |
| 04 | Low hull: red pulsing meter after repeated impacts |
| 05–07 | Paused card, Return early confirmation, resume countdown |
| 08 | Results · Returned early (no bonus, explanation) |
| 09 | Back at the recentred bar |
| 10 | Charging dock tap: time remaining |
| 11–12 | Results · Expedition complete (+20 bonus) and Hull depleted |
| 13 | Reopened unfinished run behind Paused |

The script also asserts the flow (0 failures) and measured real-time travel at about 120 fps on the development Mac (Metal). The capture-time FPS banner is the existing dev performance overlay; frames that step thousands of simulation updates at once show low figures.

## Review video

`tests/record_expedition.gd` drives the real game with injected touches at a fixed 30 fps (a ring marks the finger) and writes every frame:

```sh
python3 prototypes/sushi-loop/godot/tools/test_native.py --script tests/record_expedition.gd --visible --fixed-fps 30 --resolution 390x844 --timeout 900 --output <frames>
ffmpeg -framerate 30 -i <frames>/frame-%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 prototypes/sushi-loop/review/21/native/expedition-review.mp4
```

It shows the ship cruising the launch lead-in behind the preparation text, press-to-dive, joystick steering (the finger slides to push the ship sideways and lifts to run straight; a faint track shows the stick) with sideways thruster bubbles, gold collected as a swell-and-sparkle, a wall clip with the red edge flash and shake, Pause and the resume countdown.

## Rules and parity

- `tests/expedition_tests.gd`: 47 checks for charge, Start, steering, Pause, impacts and protection, all three outcomes, single commit, recharge (offline, clock moved back), reopen, migration and corrupt-save rejection.
- `tests/expedition_route_tests.gd`: 109 checks that the GDScript route port matches the JS reference exactly.

## Not yet done

- **Android:** no APK exported or installed for this ticket yet. Not measured on a phone GPU yet.
- **UI art:** HUD, Paused, confirm, preparation and results reuse the approved shared family. The ART-10 ImageGen pass, including the three distinct outcome backgrounds, is pending. Outcomes use tinted scrims until then.
- **Restaurant earnings:** coins earned while away are credited live. The spec's separate pending-coins credit on return belongs to the concurrent-earnings ticket.
