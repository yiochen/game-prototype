# Issue #24 · versus HUD (native)

The user approved the versus HUD and its arrival transition from `design/pursuit-preview/` (draft `https://versus-hud-24--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/pursuit-preview/`). On 2026-11-05 they asked for the Godot version.

**Layout.** From the creature's arrival, the hull bar (left) and the creature's resistance (right) share the top row. The resistance bar is mirrored: the eel icon sits at its outer end, and the fill drains toward the middle. The gold count steps aside, and Pause stays. With the second row gone, the eel's head clears the HUD on 16:9 screens.

**Arrival transition** (`encounter_start`):
- the gold count lifts and fades (0.25 s);
- the empty eel bar slides in from the right with a small overshoot (0.38 s, after 0.18 s);
- it fills from empty (0.6 s).

**Other cases.**
- If the creature escapes, the gold count fades back.
- Reopening a save mid-encounter shows the settled layout without replaying the transition.
- Reduced motion uses fades only.

**Evidence.** Captures at 405 × 720 from `tests/capture_expedition_versus.gd`, run on Metal with 0 failures:

| File | State |
|---|---|
| 01 | Travel row (hull and gold) |
| 02 | Arrival frames, in milliseconds after the encounter starts |
| 03 | Chase with the eel's head below the HUD row |
| 04 | After an escape: the gold count is back |
