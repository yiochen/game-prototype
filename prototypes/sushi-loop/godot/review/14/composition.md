# Issue 14 — composition and state inventory

Before implementation, inspect the accepted B whole-screen composition, restaurant item catalog (sections 1–2, 7, 9–11, 13–14), restaurant world concept, current restaurant-edit/restaurant-selected and component-editor-controls wireframes, and ART-10. The later continuous maple dock amendment governs the current composition.

## Complete screen

Retain the safe-area sky, cream coin/Editing pills, vermilion Live action, square restaurant floor, registered world sprites and continuous maple People/Layout/Floor/Shop dock. Layout selection uses the existing sage/navy floor brackets and Rotate/Return capsule. Occupied stools carry their guest; loaded belts carry their exact dish. Use the existing character, dish and stool production atlases at their registered floor roots.

People permits selecting a standing or trapped guest through their actual sprite pixels, followed by a drag. Selected guests use the same floor brackets. Hide object Rotate/Return actions for customers: customers are rescued, never stored or rotated. Keep the existing roster, category selection and tray-collapse behavior. Drag previews show the customer's same appearance and any unfinished dish, on a green/red floor footprint. Cancel, interruption and invalid drops retain the original state. System Back clears selection before leaving Edit.

After a seat is removed, show its guest standing at that cell. Defer new puzzled/panic reactions until Live. Reuse the finished puzzled bubble for a guest searching for seating and the finished panic bubble for an inaccessible guest. Place feedback at the existing registered head attachment, with no contextual capsule over a selected guest. Reseating restores the same unfinished meal. A non-seat placement visibly relocates the guest to the nearest valid empty cell, with their recognizable sprite and floor anchor intact; reject atomically if no space exists.

## Surface/state inventory

| Surface | States | Source |
| --- | --- | --- |
| Coin/Editing pills, Live | normal, pressed | approved shared native HUD |
| Maple dock, category tabs, Shop, roster | normal, selected, pressed, disabled roster entries | approved wood editor and shared roster |
| Object selection and action capsule | selected, pressed Rotate/Return | approved editor family |
| Customer selection | selected, keyboard focus, dragging | existing floor bracket treatment, exact character atlas |
| Placement footprint and ghost | valid, invalid, canceled | existing native placement presentation |
| Customer/dish/stool | seated waiting/eating, carried, standing, reseated, wandering | existing refined world atlases |
| Puzzled/panic feedback | appear, idle, reduced motion | existing refined feedback atlases |
| Rejection toast | no displacement room, occupied seat, seated guest rescue unavailable | existing shared toast with dynamic text |
| Persistence recovery | retry, blocking input, focus/Back | unchanged shared recovery panel |

No NEW/MAX mechanic or new visible control is introduced. All artwork is approved production artwork; no missing visual surface requires ImageGen generation. Native Shared captures reuse the same presentation as the full scene. Capture narrow phone, normal phone, wider portrait containment and landscape; inspect recognizable carried people/food, anchors, feedback clearance, readable dynamic labels and 44px native hit targets.
