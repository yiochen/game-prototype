# Long-press pickup amendment

User feedback after the 0.6.0 APK supersedes the earlier standing/trapped-only restriction. Any guest, including an ordinary seated/eating guest, can be picked up in Edit. Long-press works from any Edit layer; a guest body takes precedence over its stool for pickup. Single taps retain the existing layer-aware object selection and Rotate/Return menu. A dropped object stays selected with its context menu available.

## Complete composition and states

Retain the accepted B/continuous maple composition, HUD, production character/object/dish atlases, floor markers, wood roster and shared context capsule. No new artwork or visible controls are introduced. Catalog sections 1–2, 7, 9–11 and 13–14 and the previously recorded whole-screen references remain applicable.

A stationary 400 ms hold picks up the touched guest/object. Ten physical pixels of early movement gives ownership to panning (or the existing immediate drag for an already selected object). Once picked up, the source disappears and the same sprite follows the finger continuously, preserving its grab offset, with a small lift and a green/red snapped floor footprint. Occupied stools retain their carried guest, and loaded belts retain food. A picked-up guest stands with any unfinished plate at the authored hand socket; their original seat remains on the floor.

Hide context/path controls during pickup so they cannot cover the held character or intercept the drop. On valid object release, return the object to its cell and show its selected context menu. Canceled/invalid/interrupted releases restore the prior arrangement with no time, meal, sale or inventory changes. Reduced motion keeps static pickup feedback and direct tracking. Save/reopen contains only accepted state, never a transient lifted position.

Capture pending hold, picked-up seated guest, free tracking, invalid/canceled pickup, ordinary walking guest, unselected furniture pickup, selected-object drop/context menu, occupied stool and loaded belt pickup, plus the shared editor at narrow phone/wider containment and landscape. Reuse existing pressed/selected/disabled controls and Retry behavior; no NEW/MAX state is introduced.
