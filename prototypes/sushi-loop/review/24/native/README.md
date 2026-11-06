# Issue #24 · native Godot evidence

The approved HTML composition is `design/pursuit-preview/` (draft link `https://pursuit-catch-24--game-prototypes-yiochen.netlify.app/prototypes/sushi-loop/design/pursuit-preview/`). The user asked for Godot implementation on 2026-11-05.

User decisions:
- A pursuit with no following range: ship and eel speed up together.
- Resistance is the creature's health and only drains.
- Collisions cost hull only.
- One harpoon at a time.
- The harpoon retracts into the ship when the eel is caught.
- There is no "Back at the restaurant" screen.

## What is implemented

**Route.** Version 4 places the arena five ordinary chunks before the finish. Saves from #23 keep version 3.

**Pursuit.** A hook starts the chase:
- Ship and eel ramp to 1.4× travel speed over 1 s.
- The cable stretches freely from the nose to the pinned harpoon, drawn over the world.
- The arrows stay live, the Harpoon hides, and pale streaks rush past.
- The eel swims above the terrain and thrashes (`struggle`) below 30% resistance.
- The resistance pill drains at 4.5/s (about 22 s) and turns amber below 25%.
- Hits cost hull only, with knock-back.

**Catch.** At zero resistance the rules commit the catch and the Eel roll discovery (marked NEW) and end the run as complete, with the completion bonus. Reaching the finish while hooked also lands the catch.

Then a 2.8 s cutscene plays with no Skip:
- the scene dims and rays turn;
- the exhausted eel is drawn into the upper middle and grows;
- the harpoon pulls free and reels home into the nose;
- "Caught! · Storm Eel · first catch" appears.

**Award.** A maple "New recipe!" card follows:
- the ImageGen stage (`assets/ui/awards/`, with its manifest and provenance);
- the #15 Red plate and Eel roll as separate layers;
- the name, "From the Storm Eel", and Price 48 and Base prep 7.5 sec chips;
- Continue.

It then shows the results. A repeat catch goes straight to the results.

**Escape.** Zero hull mid-chase snaps the cable and the eel bursts away ("It got away · Hull depleted"). The Hull depleted results follow, with no recipe and no second attempt.

**Restaurant.** Restaurant returns directly, and Eel roll shows NEW in each chef's recipes until inspected.

**Saves.** An unfinished pursuit reopens behind Paused with its resistance, hull and timers. After the catch the run is over, so reopening shows the results once and never resumes the pursuit.

**Debug.** With the cheats flag, DEBUG · Catch drains resistance to its last moment.

Gallery: `--expedition-gallery --expedition-feature=pursuit|award`.

## Screenshots

`phone/` (390 × 844) and `wide/` (1100 × 820) come from `tests/capture_expedition_pursuit.gd`, run on Metal with 0 failures.

| File | State |
|---|---|
| 01 | Hooked |
| 02 | Chase, steering at speed |
| 03 | Low resistance (amber bar, thrashing) |
| 04 | Caught |
| 05 | Harpoon reeling home |
| 06 | Cutscene |
| 07 | Recipe award |
| 08 | Results |
| 09 | NEW Eel roll in Lena's recipes |
| 10 | Escape: the cable snaps |
| 11 | Hull depleted results |

## Checks

- `tests/expedition_pursuit_tests.gd`: 48 checks.
- Encounter, features and travel rules are updated and pass: 53, 38 and 180 checks.
- The route parity checks pass: 143 checks.
- Five pre-existing failures are unchanged and identical on `main`: customer_visit, session, wood_editor, frame_work and art_cache.
