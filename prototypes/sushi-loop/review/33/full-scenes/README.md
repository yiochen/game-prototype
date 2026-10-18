# Complete scene review — issue 33

Open `#scene-restaurant` or `#scene-underwater` on the Sushi Loop wireframe site. The **Scene art review · #33** group and object-library crosslinks make both pages discoverable. Scene tabs, object inspection links and Comments retain their own deep links.

The restaurant assembles 69 placements into a cutaway dining room with a connected conveyor loop, working chefs, separate seated customers/stools, storage and an entrance aisle. The underwater scene assembles 77 placements around a connected canyon, reef/wreck pockets, submarine route, fish/eel, salvage and layered water effects. Every sprite comes from the existing native catalog.

## UI and playback verification

The [scene browser spec](../../../tests/world-showcase.spec.js) passes **5/5 tests in 21.6 seconds** across 320×740, 844×390 and 1440×1000. Checks cover actual image decoding and placement counts, reduced-motion paused start, shared 48-second playback/scrubbing, staged movement, fixed swept bounds, Fit/2× horizontal panning, grid/root toggles, asset links, tabs, browser history and one document scroller. Phone touch gestures reach the document over both maps at Fit and 2×. Calibration overlays start off and no controls cover the art.

The [data contract tests](../../../tests/world-showcase-data.test.js) cover exact native object/clip/facing references, finite placement/path positions, unique placement IDs, valid highlight links and complete scene-cycle closure. Scene duration is 48 seconds, with 12 fps sprite playback. The restaurant’s plate travel is staged independently of slat timing; no service or expedition simulation runs.

`browser-results.json` records the initial UI results and the historical native attachment finding; `final-scene-report.json` records the corrected final visual pass. The underwater images show the clean scene at phone, landscape and desktop widths; `underwater-desktop-quarter-path.png` shows a second staged position. Complete scene code lives in the [shared showcase component](../../../wireframe/world-showcase.jsx); the maps are separate [restaurant](../../../wireframe/restaurant-showcase-data.js) and [underwater](../../../wireframe/underwater-showcase-data.js) data modules.

## Native attachment finding — before fix

The restaurant screenshots named **before-attachment-fix** preserve a visual issue found after the UI checks passed: Samir’s W-facing eat sprite at frame 9 contains a cucumber plate floating below the boots. `samir-eat-W-frame9-before.png` is the full registered native source frame showing the defect. Its appearance beneath the blue stool is not caused by the scene renderer or frame order.

The native attachment correction is now published locally for all affected customers and chefs, with both composed layouts retained. The screenshots named **before-attachment-fix** remain historical failure evidence. `samir-eat-W-frame9-before-after.png` shows the plate move from below the boots into the hand; `samir-attachment-proof.json` verifies that the restaurant’s W-facing frame 9 uses the corrected atlas bytes.

## Final corrected visual pass

Both scenes pass a focused render/decode check at **0, 12.25 and 30.5 seconds** (2.346 seconds). Omar’s N-facing hold, Noor’s S-facing work and Samir’s W-facing eat use the current native atlas hashes at every sample. All scene images decode, the six circulating dishes remain foreground layers over the connected belt, and there are no page or HTTP errors. The final 390px phone views remain contained with zero nested vertical scrollers. The unchanged control suite was not repeated after native-only sprite publication.

`restaurant-desktop.png`, `restaurant-desktop-t12-25.png` and `restaurant-phone-final.png` are the corrected restaurant views. The underwater desktop/phone images and `underwater-desktop-t30-5.png` show the submarine and creatures at separated route positions with clear terrain passage. Calibration chrome remains off by default.

User approval of the finished scene assets remains pending; issue #33 remains open.
