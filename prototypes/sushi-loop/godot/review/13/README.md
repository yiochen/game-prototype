# Issue 13 — serving conveyor routes

Native Godot implementation for [issue 13](https://github.com/yiochen/game-prototype/issues/13), ready for user verification. The accepted wood dock and approved world artwork are reused. The [composition and surface/state inventory](composition.md) records the full screen design before implementation; [reference hashes and asset audit](references-and-art.json) identify the catalog sections and exact reused artwork.

## Try it

1. Enter **Edit**, then drag a **Belt** from Layout onto clear floor. The first tile is committed immediately and starts a path.
2. Tap a highlighted neighboring cell to extend. Empty cells spend one owned tile; existing neighboring belts are reused and reoriented without spending stock. Amber identifies a valid closure at the starting tile.
3. **Rotate** turns the latest tile a quarter turn and restarts the cursor there. Old connections detach while their tiles and food remain. **Return** stores the latest tile, discards its plate without revenue and returns the cursor to its predecessor. **Inventory** (X), an outside tap or system Back exits path construction. Live remains the explicit service resume action.
4. At zero stock, empty extensions show **No belt tiles left**. Existing-tile reuse, valid closure, Rotate, Return and Inventory remain usable.
5. Reopen during construction: the exact path cursor, graph, inventory, camera and food return in paused Edit. Every accepted command is already saved; existing write-failure Retry behavior still blocks further changes until persistence succeeds.

Selecting an existing belt starts a path there. Ordinary selected-object dragging still moves it; moving or rotating a belt detaches its old connections. Native sprite picking includes raised artwork and preserves the grab offset. Neighbor targets also have accessible names and keyboard focus/activation.

Connections are explicit, with at most one incoming and outgoing edge. Reshaping replaces edges and retains disconnected old segments. The starting tile can close a valid loop; intermediate visited tiles reject backtracking. No junction/split/merge mechanic is introduced. Separate neighboring routes remain separate until explicitly connected.

Pre-route saves acquire their existing facing/adjacency links. An ambiguous old merge keeps the first input in saved object order and leaves the other segment disconnected; its tiles, food, inventory and coins remain owned.

Full occupied loops move their plates simultaneously. Open endpoints retain their plates and stop their upstream queue; eating a stopped plate releases that queue. Decisions use one occupancy snapshot, and ownership transfers clear all sources before assigning destinations. Chefs cannot insert a plate into an empty tile already reserved by an approaching plate. Food follows the actual quarter-circle and meets the approved sprite ports continuously across ownership boundaries.

## Review captures

All four sets are actual Mobile/Metal Godot renders with native viewport touch dispatch. The same native presentation is used by gameplay and the Shared editor gallery. Catalog sections 1–2 and 11–13 govern grid, belt geometry and food; 5, 6, 8 and 14 govern the reused controls and feedback. Existing UI surfaces, icons and 34 catalog objects remain unchanged; two approved corner objects add eight exact native atlases. No new artwork generation was needed.

| State | Narrow phone | Wider portrait containment |
| --- | --- | --- |
| Start and normal controls | [Start](narrow/01-path-start.png) | [Start](wide/01-path-start.png) |
| Actual pointer-down press | [Pressed](narrow/02-path-pressed.png) | [Pressed](wide/02-path-pressed.png) |
| Selected turn and valid targets | [Turn](narrow/03-path-turn.png) | [Turn](wide/03-path-turn.png) |
| Zero stock / disabled empty targets | [Zero stock](narrow/04-zero-stock.png) | [Zero stock](wide/04-zero-stock.png) |
| Rejected extension / toast | [Rejection](narrow/05-shortage-feedback.png) | [Rejection](wide/05-shortage-feedback.png) |
| Reopened paused path | [Reopened](narrow/06-reopened-path.png) | [Reopened](wide/06-reopened-path.png) |
| Closed loop / selection | [Closed](narrow/07-loop-closed-selected.png) | [Closed](wide/07-loop-closed-selected.png) |
| Shared native gallery | [Shared](narrow/08-shared-construction-gallery.png) | [Shared](wide/08-shared-construction-gallery.png) |
| Full loop with moving food | [Live](narrow/09-live-full-loop.png) | [Live](wide/09-live-full-loop.png) |

Additional [390×844 phone](phone/04-zero-stock.png) and [1280×720 landscape](landscape/04-zero-stock.png) captures preserve the current portrait composition. The narrow set is 320×720 and the wide set is 984×1224. Neighbor outlines remain legible over raised furniture, labels stay inside their surfaces and path controls retain at least 44px physical touch targets. The existing diagnostic overlay is visible; timings during scripted capture and background builds are not an Android performance measurement.

## Validation

- **18 native suites pass** in a fresh isolated project/save identity. This includes **88 route checks**, **29 new actual-app touch/persistence checks**, **185 inherited editor checks**, **148 inherited actual-app checks**, and **1,604 art checks / 260 atlases / 3,052 complete frames**. Existing session, customer, save, sprite selection, entrance, guest recovery, layout, frame-work and performance-overlay regressions also pass. See [native suite log](checks/native-full.log).
- All **29** new native app checks also pass visibly at each of the four capture sizes, including canceled presses/drags, raised-sprite loop closure, keyboard reuse, zero-stock inventory feedback, immediate persistence, Return, outside taps and Back.
- **66 Android packaging tests pass**, including isolated review13 identity, release identity, exact art/UI sources and excluded authoring/private files. See [packaging log](checks/packaging-tests.log).
- **41 relevant browser checks and the Vite production build pass**. These verify the existing reference studio and dock preview; native input is covered separately above. See [browser](checks/browser.log) and [build](checks/build.log).
- The full JavaScript suite reports **200 passes and 2 failures**. Both failures are existing art-provenance inputs absent from the checkout and HEAD: a belt candidate's ignored `.godot/.gdignore` and the coin-pop original catalog record. The relevant test and production library are unchanged by this work. See [baseline evidence](baseline-test-failures.json) and [engine output](checks/engine.log). Those archival failures are not claimed as passing.

## Android artifacts and remaining device check

Release **0.5.0 / code 57** retains the normal package/save identity, current pinned release certificate, offline/nondebuggable settings and Mobile/Vulkan configuration with OpenGL fallback disabled. Both APKs are 246,559,288 bytes. Local artifacts:

- Normal update: `.scratch/sushi-loop-v0.5.0-conveyor-routes.apk`, SHA-256 `6a63f60c997250299d12a211b2cb5fd79d80966756494eb51b3e5a3f270a425e`.
- Separate exhibition package: `.scratch/sushi-loop-v0.5.0-conveyor-routes-review.apk`, package `com.yiochen.sushilooptickets.review13`, SHA-256 `d13c981abaaf6dffd2b62485b0d21b22fcd6b7ef109aed495238c9d26249afa2`.

[Normal build audit](normal-build.json), [review build audit](review-build.json) and [current runtime verification](runtime-verification.json) confirm all 343 runtime source files still match the exports. Normal and review builds share every gameplay/content/art source; only staged branding/package metadata differs.

**Actual Android graphics validation is blocked.** The exact signed review APK installs and initializes on an isolated Pixel 8 / API 35 clone, but both SwiftShader and Apple M4 host GPU modes report Vulkan 1.3 / Forward Mobile followed by `Couldn't present to Vulkan queue (VkResult error 5)` and a black frame. No Android touch tests are claimed as passing. The required renderer was retained. See [Android verification](android/verification.json), [host log](android/host-gpu.log) and [SwiftShader log](android/swiftshader/runtime.log).

The clone was stopped and removed. Original AVD file hashes, sizes and modification times and the normal app's save hashes remain unchanged; [isolation evidence](android/avd-isolation.json) records those checks. Physical-device verification remains the next review step before completing this ticket.
