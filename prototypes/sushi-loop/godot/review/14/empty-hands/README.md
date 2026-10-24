# Empty hands after leaving a stool — issue 14 amendment

The user requested that held sushi disappear when an eating guest becomes standing because their stool was removed or the guest was picked up and moved off it. This supersedes the earlier carried-plate visual requirement.

## Composition and states

Reuse the accepted B/maple full-screen composition, current restaurant catalog (sections 1–2, 7, 9–11, 13–14), world concept, registered guest sprites and existing controls. There are no new surfaces or artwork.

| State | Food presentation |
| --- | --- |
| Seated eating, including movement with the whole stool | Existing seated eating sprite shows its sushi |
| Stool removed; guest standing | Authored standing sprite with empty hands |
| Guest picked up directly from the stool | Lifted standing sprite with empty hands |
| Guest dropped on clear floor | Standing sprite with empty hands |
| Guest walking to replacement seating | Walking sprite with empty hands |
| Guest reseated | Original eating presentation resumes |
| Guest pickup canceled | Prior seated presentation returns |

This changes presentation only. The same visit retains its unfinished meal, preference, fullness and frozen meal clock; food is neither sold nor discarded by the visual transition. Long press, tap menus, persistent object selection and interrupted-drop behavior remain intact. Renderer and picker share the same sprite pass, so an invisible plate cannot become a selectable extension.

## Validation and delivery

- All **22 native suites pass**, including **108 presentation/touch checks** covering all four guests, four directions, three sushi recipes, standing/walking, stool removal, pickup, cancellation, reseating and save/reopen.
- The 108 checks pass visibly at 320×720, 390×844, 984×1224 and 1280×720. Each size has six full-scene captures and records the actual **Mobile/Metal** renderer. Narrow and wide scenes were visually inspected; the same shared renderer supplies every presentation.
- **66 Android packaging checks**, **41 browser checks** and the **Vite production build** pass. JavaScript remains **200 passes / two existing missing art-archive failures**; see the [baseline](../baseline-test-failures.json).
- [Logs](checks/), [test/source audit](verification.json), [build receipt](normal-build.json) and [source/signing verification](runtime-verification.json) bind this run to the current source. The exact unfinished meal and clock remain preserved; no simulation logic changed.

| Capture | Narrow phone | Wider portrait containment |
| --- | --- | --- |
| Seated eating | [Before](320x720/01-seated-eating.png) | [Before](984x1224/01-seated-eating.png) |
| Stool removed | [Empty hands](320x720/02-stool-removed-empty-hands.png) | [Empty hands](984x1224/02-stool-removed-empty-hands.png) |
| Reseated | [Eating resumes](320x720/03-reseated-eating.png) | [Eating resumes](984x1224/03-reseated-eating.png) |
| Picked up | [Empty hands](320x720/04-picked-up-empty-hands.png) | [Empty hands](984x1224/04-picked-up-empty-hands.png) |
| Dropped on floor | [Empty hands](320x720/05-dropped-empty-hands.png) | [Empty hands](984x1224/05-dropped-empty-hands.png) |
| Walking | [Empty hands](320x720/06-walking-empty-hands.png) | [Empty hands](984x1224/06-walking-empty-hands.png) |

Release **0.6.2 / code 60** retains the original pinned signer, package/save identity, nondebuggable offline settings and Mobile/Vulkan configuration with OpenGL fallback disabled. APK: 246,571,576 bytes, SHA-256 `453b5cc448d3d28293ab5dd702f79f975da429150be35c218d8e759f0a2ce350`.

[Download signed APK 0.6.2](https://drive.google.com/file/d/1jbrR88WHrkYUnwna7NC_OcqMerzUlnML/view?usp=drivesdk). Drive size and checksum match the verified local build; [readback evidence](drive-upload.json).

**Android phone verification remains pending.** Native tests use isolated save storage and do not access installed app data. Mobile/Metal captures do not establish Android Vulkan graphics behavior.
