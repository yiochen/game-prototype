# Starter restaurant production artwork

Original artwork for the current Godot Android ticket #10 slice, generated with the built-in image-generation tool against the supplied `design/art-directions/doodle.png` catalog. No catalog pixels or archived game assets are reused. No game title is baked into the artwork.

Load [manifest.json](manifest.json) by semantic key. Entries declare an unchanged source PNG, exact native region, measured anchor, and a shared scale reference when required. Equivalent AtlasTexture resources live in `atlas/`. [animations.json](animations.json) declares ordered six-frame loops and playback timing.

The renderer maps character feet to the center of their occupied square floor tile. Each clip shares a physical scale; individual atlas padding cannot shift or resize the character. Taller artwork extends above the ground point. Belts and plates use center anchors; other props use a bottom-center base. Smooth mipmapped sampling reduces the native images cleanly to phone size.

- `chef_work_up/down` and `chef_hold_up` are six-frame preparing and blocked-holding loops. These cover the current north-facing chef and the front-facing Shared gallery.
- `guest_a_walk_*` and `guest_b_walk_*` provide separately drawn up/down/left/right walking loops. Both identities have six-frame `waiting_down` and `eating_down` clips for the current south-facing seats. Waiting hands are empty; eating poses use one plate and serving. A separate stool sits behind each seated person.
- `stool`, `salmon_nigiri`, `blackboard`, `plant`, `plant_tall`, `barrel`, `crate` and `lantern` are prop regions. The blackboard is blank so the current dish can be drawn within it.
- `belt_end_left`, `belt_horizontal`, `belt_horizontal_b` and `belt_end_right` are equal 502 × 460 quarter cuts of one connected conveyor. Each has six synchronized surface frames. `belt_endpoint` aliases the right cap. Rails and supports stay fixed; only the deck scrolls. Fit every module to the same **tile width**, keeping its native aspect ratio, so joins touch exactly.
- `pile_sofa`, `pile_shelf`, `pile_cart` and `covered_dock` are whole environment compositions. `entrance` is an open harbor doorway with no lettering. These use measured complete silhouettes rather than fixed atlas-cell crops.
- `floor_wood` resolves the quiet ochre doodle floor material. The renderer draws an independent undistorted square grid.
- `app_icon` is a title-free square Android launcher illustration.

All 15 character clips contain six different drawings, at least 445 native pixels tall. Source atlas size is 1448 × 1086. [Generation prompts, registration and conveyor baking](../provenance/README.md) explain the reusable pipeline. [Source verification](../provenance/image-verification.json) records dimensions, hashes and alpha; [actual runtime motion and registrations](../../review/10/animation/) provide review evidence.

Cooking, belt occupancy, customer progress, prices, sales and persistence remain controlled by the public game session. Presentation frames follow its elapsed time; the drawings contain local pose changes rather than whole-cutout bobbing.
