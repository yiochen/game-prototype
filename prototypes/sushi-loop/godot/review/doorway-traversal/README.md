# Guest doorway traversal and front routes

Guests enter from the dark part of the approved entrance and return there before removal. The existing HUD, editor controls, world sprites, sprite registration and foot-based curtain layering are retained.

Each new arrival and departure independently samples a continuous horizontal position across the opening. The character joins the nearest usable navigation lane at `(4, 3)` or `(5, 3)` instead of converging on a fixed left-tile anchor. Both entry and exit prefer the matching front approach at row four before turning toward a seat or the doorway. A blocked approach can use another reachable path. The chosen side and crossing position are saved; existing crossings without the new fields retain their previous path.

**Both front tiles accept objects.** They follow normal occupancy, customer recovery and placement rules. Neither is reserved by the entrance. One blocked side routes guests through the other. With both sides blocked, new admissions wait outside without spawning inside furniture. Already-admitted departures wander with the existing trapped feedback until a reachable side reopens; the same visit resumes without duplicate payment. Layout edits and door motion remain frozen in Edit.

The entrance samples use a separate random stream; selecting a side does not consume extra service RNG draws. Actual routes and seat distances can naturally change with the selected entrance. Crossings preserve a continuous presentation between the dark opening and their selected floor tile. Movement uses the configured guest walking speed, with brightness and opacity fading in darkness.

| State | Presentation and behavior |
| --- | --- |
| Arriving | Walk south from darkness to the selected free front tile; no admission/preference clocks advance during this segment. |
| Inside | Walk through that side's front approach to the assigned seat, or start the existing four-second puzzled wait at that side. |
| Departing | Approach an independently selected reachable front tile, walk north into darkness, then emit one departure event. No-seat departures also walk to their selected side. |
| Both sides blocked | Hold new admissions outside; existing guests retain their visits and recover when a side becomes reachable. |
| Edit / reopen | Preserve crossing distance, selected side, RNG, meals and visit state. Explicit People rescue cancels an active portal segment and retains the visit. |

The curtain's ground plane is `y = 2.05`, calibrated to the back edge of the step. Painter order compares this plane with the character's foot root, including passing offsets. Foreground polygons reuse the exact approved gate texture, including cloth waves, straps, fish and open seams. There are no new textures or runtime readbacks. Picking uses the same contours to exclude hidden body pixels; doorway feedback bubbles are suppressed.

## Verification

- `tests/doorway_tests.gd`: 41 checks pass for crossing motion, paid service, no-seat exits, deterministic save continuation, Edit freeze, invalid saves, curtain ordering, hidden-pixel picking, rescue, width sampling and old crossings.
- `tests/entrance_routes_tests.gd`: 20 checks pass, following 24 real admitted/served visits through both front approaches. Covers furniture on either/both front tiles, blocked admissions, trapped departures, reopening the right side, no duplicate payment, invalid saved lanes and stable crossing positions after replanning.
- Entrance waiting (78), exit recovery (68), guest wandering (82), customer recovery (121), and backdrop (48) checks pass. Two older editor migration assertions remain baseline failures; the former entrance-reservation assertions now verify allowed placement/rescue instead.
- Full native Mobile/Metal captures at 450×800 and 844×390 show actual seated-service routes through both front tiles, departures through both sides, furniture blocking both tiles, and admission through the reopened right tile. Evidence: ignored workspace folder `artifacts/sushi-loop/entrance-routes/`. Earlier empty-room crossing evidence is retained in `artifacts/sushi-loop/doorway/` and `doorway-width/`.
- Root engine tests: 200/202 pass; two historical refinement files are missing (belt-straight-n and coin-pop). Vite build and both catalog browser checks pass. Existing unrelated legacy migration failures remain documented in the test logs.

Use the isolated runner `godot/tools/test_native.py` with `--script tests/entrance_routes_tests.gd` or `--script tests/capture_entrance_routes.gd --visible --size 450x800 --output <directory>`.
