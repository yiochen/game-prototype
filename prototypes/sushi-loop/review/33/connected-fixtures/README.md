# Connected module review — issue 33

Local production preview: port 4189, 2026-10-17 PDT. Final artwork approval is still pending.

## Results

- All 50 connected section-03 records passed rendered geometry checks: 20 directed belts, 22 other explicit-port modules, four floor patches and four dock assemblies. Every reviewed native port coincides with a compatible neighbor's rendered port. Belt modules share the sampled animation frame; floors use contiguous 3×3 patches; every dock context includes its overlapping entrance ramp.
- All 20 belt routes passed visible-plate checks at five positions each: 100 screenshot comparisons against hiding only the plate. Every sample retained visible plate pixels (minimum 309 pixels), and its registered root matched the staged path. The quarter-circle route is presentation motion, independent of native slat timing.
- At 320px portrait and 844px landscape, corner belts, wall corners and dock entry stay contained with zero nested vertical scroll containers. Wheel gestures reach the document. The phone touch gesture moved the document from 1429px to 1570px.
- No page exceptions, image decode failures or HTTP errors. Geometry/responsive pass: 18.813 seconds. Focused visible-plate pass: 18.259 seconds.
- The independent native geometry report validates all 42 port modules, four floor patches and four dock assemblies, including actual cross-section compatibility and all four corner support footprints inside the deck annulus. The five connected-fixture unit tests remain in `tests/connected-fixtures.test.js`; the complete 149-test suite and production build also passed.

## Evidence

`*-clean.png` show connected artwork without calibration overlays; `*-ports.png` expose coincident native attachment points. `*-plate-midpoint.png` show both travel directions on a curved deck. The 320px images preserve the phone layout.

`geometry-and-responsive-report.json` records the 50-object pass. Visual inspection after that pass found a moving plate hidden by fractional-row depth sorting; `before-dish-layering.png` preserves this original defect. The fix assigns only the staged plate an explicit foreground pass in these isolated, shared-height deck fixtures. Other character and prop sorting is unchanged. `visible-dish-report.json` records the subsequent 100 successful pixel comparisons and exact sampled roots.

Both manual QA scripts are included. With the production preview already running at port 4189, execute them with Node from this repository; their output remains under `/private/tmp/sushi-object-review/connected-fixtures/`. The pixel comparison uses the bundled workspace Python/Pillow runtime. They do not modify assets or the manifest.
