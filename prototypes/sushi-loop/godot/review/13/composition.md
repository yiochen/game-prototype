# Issue 13 — conveyor construction composition and state inventory

References inspected before implementation: accepted B composition, Restaurant
UI & item catalog, restaurant concept, current restaurant-edit/inventory-empty/
component-editor-controls wireframes, and the accepted native wood dock.
Catalog sections 1–2 govern grid/registration, 11–13 govern belt modules/food;
5, 6, 8 and 14 govern reused control surfaces, icons and rejection feedback.

The existing native wood dock and upper HUD form the full screen composition.
World tiles, sprite roots, shadows and portrait containment retain their current
contracts. Path construction highlights the four neighbors of the latest tile.
Green marks usable placement/reuse; amber marks closure at the starting tile;
muted targets explain unavailable empty extensions when stock is exhausted.
Rotating the latest tile turns the whole object one quarter turn, detaches its
old ports and starts the cursor there; disconnected neighboring tiles remain.

An active path uses the existing cream contextual capsule directly above the
maple dock, containing native remaining-stock text and Rotate, Return and
Inventory (X) controls. All use the approved existing surfaces and icons; no
missing raster artwork or new visual material is introduced. Other selected
objects use their existing contextual controls. Inventory exit keeps accepted
edits, stays in Edit and exposes the same inventory drawer. Live remains the
explicit resume action. Each accepted command saves immediately.

| Surface | Relevant states and behavior |
| --- | --- |
| Live, coin/Editing pills, wood categories and Shop | Existing normal, pressed, selected and unavailable states |
| Inventory | Existing horizontal scrolling and upward pickup; zero belt stock gives a short toast |
| Construction capsule | Remaining stock, normal/pressed Rotate and Return, Inventory exit; all actions remain available at zero stock |
| Neighbor cells | New tile, reused belt, valid closure, occupied/rejected and exhausted-stock target |
| Belt modules and sushi | Approved straight, both corner chiralities, inlet/outlet caps; connected ports and curved dish motion |
| Object selection | Existing select-before-drag, move, rotate and inventory return; selecting a belt resumes construction there |
| Feedback | Existing catalog-derived toast surface; no shortage modal |
| Save/recovery | Path cursor, links, inventory and food persist; interrupted drops retain the accepted prior state; existing Retry owns write failures |
| Shared native gallery | Same construction capsule, stock/disabled states and route renderer as gameplay |

Validation covers public command/time/save behavior, native touch and keyboard,
real native phone/wider portrait/landscape captures, engine tests and build.
Complex overlapping reconnections remain outside this ticket; construction
reuses adjacent tiles and replaces their old edges without splits or merges.
