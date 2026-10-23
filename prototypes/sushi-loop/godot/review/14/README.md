# Issue 14 — customer layout recovery

Native Godot implementation for [issue 14](https://github.com/yiochen/game-prototype/issues/14), ready for user verification. The [complete composition and state inventory](composition.md) records the screen before implementation; [reference and art hashes](references-and-art.json) identify the exact approved artwork reused. The current maple dock, character/stool/dish atlases and finished puzzled/panic feedback are retained.

## Try it

1. In **Edit → Layout**, tap an occupied stool (including its customer's visible body), then drag it. The stool carries the seated customer, current animation frame and exact unfinished meal. **Rotate** preserves their progress too.
2. **Return** stores the stool and leaves the guest standing at its former position. Their dish, fullness, preference and meal clock remain owned by the same visit. Reactions wait until **Live**. Live shows puzzled feedback and seeks a reachable free stool beside a belt. Walking to replacement seating carries the plate; eating resumes from the unfinished clock after sitting.
3. Drag a suitable stool onto the standing guest to reseat them immediately. Another object displaces them to a nearest valid clear cell. The whole placement rejects without spending inventory or moving anyone when no displacement cell exists. The entrance and occupied seats remain protected.
4. In **People**, tap a standing or trapped customer and then drag their rendered body to empty cleared floor or a free seat. Rescue requires no walking route, including across a completely blocked aisle. It keeps their identity, appearance, visit, preference, fullness and unfinished meal. Direct dragging off an occupied seat remains unavailable; move that stool instead.
5. Selected customers use the existing floor marker, repeated above raised furniture for clear anchors. Object-only Rotate/Return controls are hidden. Named keyboard/accessibility selection targets are at least 44 physical pixels; **Back/Escape** clears customer selection while keeping Edit paused.
6. Invalid, canceled, backgrounded or focus-interrupted drops preserve the valid prior state. Every accepted drop saves immediately. A failed write retains that accepted arrangement in the blocking **Retry** flow; Retry writes the same visit/meal once storage recovers.

A seatless guest waits with puzzled feedback when a way to the entrance remains. If neither seating nor an exit is reachable, they panic and wander slowly. Opening access, placing seating or direct rescue restores their visit. New arrivals retain their existing separate four-second entrance-wait behavior.

A loaded belt move also retains the exact plate and unfinished transfer clock. The detached endpoint holds both until reconnected; reshaping other existing outputs retains its current geometry rules. Returning a loaded belt still discards its plate without revenue.

## Native captures

These are actual native Mobile/Metal renders and viewport touch dispatch. Narrow is 320×720, phone is 390×844, wide is 984×1224 with portrait containment, and landscape is 1280×720. Gameplay and the Shared editor use the same presentation. Catalog sections 1–2, 7, 9–11 and 13–14 govern floor anchors, people, food and feedback. Existing B/wood controls remain the current UI family. No new artwork generation was required.

| State | Narrow phone | Wider portrait containment |
| --- | --- | --- |
| Occupied stool selected | [Selected](narrow/01-occupied-seat-selected.png) | [Selected](wide/01-occupied-seat-selected.png) |
| Actual held Rotate press | [Pressed](narrow/02-occupied-seat-pressed.png) | [Pressed](wide/02-occupied-seat-pressed.png) |
| Carried guest/meal preview | [Preview](narrow/03-carried-customer-preview.png) | [Preview](wide/03-carried-customer-preview.png) |
| Accepted occupied-stool move | [Moved](narrow/04-carried-customer-dropped.png) | [Moved](wide/04-carried-customer-dropped.png) |
| Removed seat; paused guest | [Standing](narrow/05-seat-removed-paused.png) | [Standing](wide/05-seat-removed-paused.png) |
| Live puzzled reaction | [Puzzled](narrow/06-puzzled-standing-guest.png) | [Puzzled](wide/06-puzzled-standing-guest.png) |
| Immediate seating placement | [Reseated](narrow/07-immediate-reseating.png) | [Reseated](wide/07-immediate-reseating.png) |
| Visible nearest-cell displacement | [Displaced](narrow/08-visible-displacement.png) | [Displaced](wide/08-visible-displacement.png) |
| People selection | [Selected guest](narrow/09-people-selected.png) | [Selected guest](wide/09-people-selected.png) |
| Rescue onto a free seat | [Preview](narrow/10-rescue-to-free-seat-preview.png) | [Preview](wide/10-rescue-to-free-seat-preview.png) |
| Same unfinished meal restored | [Rescued](narrow/11-rescued-and-reseated.png) | [Rescued](wide/11-rescued-and-reseated.png) |
| Inaccessible guest; panic | [Panic](narrow/12-trapped-panic.png) | [Panic](wide/12-trapped-panic.png) |
| Rescue across a blocked aisle | [Rescued](narrow/13-rescued-across-barrier.png) | [Rescued](wide/13-rescued-across-barrier.png) |
| Shared native editor/gallery | [Shared](narrow/14-shared-rescue-gallery.png) | [Shared](wide/14-shared-rescue-gallery.png) |
| Failed save and Retry | [Retry](narrow/15-rescue-save-retry.png) | [Retry](wide/15-rescue-save-retry.png) |

The carried plate uses the character's authored right-hand socket, keeping the face recognizable. Feedback follows the registered head attachment, and selected guests have no object-action capsule over their reaction. Square floor cells and bottom-centered roots remain undistorted. Labels, modal padding, press feedback, 44px targets and portrait containment were inspected in full scenes. The diagnostic timings include scripted captures and background build work; they are not Android performance measurements.

## Validation

- **20 native suites pass**, including **78 new customer-layout checks**, **31 new native touch/persistence checks**, 185 inherited editor checks, 148 inherited actual-app checks, 88 conveyor-route checks and 1,604 art checks / 260 atlases. [Full log](checks/native-full.log) and [isolated run/source audit](native-verification.json).
- All **31 new native touch checks pass** visibly at each of the four capture sizes. They cover carried food/person ownership, reseating, displacement, rescue across blocked paths, invalid/canceled/interrupted drops, keyboard/system Back, save/reopen and write failure/Retry. Per-size `verification.json` records actual renderer/driver and failures.
- **66 Android packaging tests**, **41 relevant browser checks** and the **Vite production build** pass. See [packaging](checks/packaging-tests.log), [browser](checks/browser.log) and [build](checks/build.log).
- The complete JavaScript run reports **200 passes and two existing missing art-archive failures**. Both inputs, their test and the production catalog are unchanged by this ticket. See [baseline evidence](baseline-test-failures.json) and [engine log](checks/engine.log).

## Android builds

Signed release **0.6.0 / code 58** retains the normal package/save identity, original pinned release certificate, nondebuggable offline settings and Mobile/Vulkan renderer with automatic OpenGL fallback disabled.

- Normal update: `.scratch/sushi-loop-v0.6.0-customer-rescue.apk`, 246,567,480 bytes, SHA-256 `6cdab3edea98731c8f249968c76e0c2af4282bb509974daa8fd08446602824a1`.
- Separate review app: `.scratch/sushi-loop-v0.6.0-customer-rescue-review.apk`, package `com.yiochen.sushilooptickets.review14`, 246,571,576 bytes, SHA-256 `a6bdf8ff932ae895a968a92ed9126921b25fa5ed1cf1aba169f73a1763902b24`.

The [normal build receipt](normal-build.json), [review build receipt](review-build.json) and [runtime verification](runtime-verification.json) record APK hashes, signing/package checks and the exported runtime source fingerprint. Review differs only in staged title/package metadata; it shares all gameplay, content and artwork with the normal update.

**Phone verification remains pending.** [Device inventory](android-device-status.json) found no attached Android device. No #14 Android installation or Vulkan graphics check is claimed. Native tests/captures use isolated save identities, and no normal installed app data was accessed. Keep this issue open for the user's Android review.
