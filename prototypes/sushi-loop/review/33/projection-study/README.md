# Height projection study — issue #33

Review route: `#projection-study`. This is an experimental comparison, not approval of a new projection or of the production art.

- Seven groups: five environment objects, one fixed Lena pose, one connected conveyor assembly.
- Four height coefficients in requested order: 1.0, 0.7, 0.5, 0.4; plus the same chef pose under the current ordinary 35° character camera.
- All 29 stills rendered directly in Blender at 4× source resolution. No animation was added.
- Independent native audit passes all camera-matrix, floor-pitch, height, root, geometry, material, transform, byte-hash, dimension and alpha-edge checks. Ground pitch stays 128 logical pixels; unit height is 128 / 89.6 / 64 / 51.2 pixels. Minimum transparent margin: 21.5 logical pixels.
- The production world-library SHA256 remains `732a5a4cc73c908f69ccc832e8dc1e66a63c81307157427d9b73e0efdc2acbcd`; no existing 125-asset source or scene sprites were replaced.

The editable isolated study, capture recipe and reusable audit are under `assets/projection-study/`. Issue #33 remains open for user review.

Browser and repository verification: all 164 engine/helper tests pass; final Vite production build passes (3.20 seconds); all five existing world-showcase checks pass (17.5 seconds). Five focused projection checks pass on desktop 1440, phone 320/390 and landscape 844, including native image decoding, all four columns, fixed frame/root/floor registration, common 48/64/96-pixel tile pitch, offscreen image loading, guide controls, horizontal touch panning and document-owned vertical touch scrolling. The wide assembly label scrolls with its row so it does not obscure captures or captions on narrow phones. SVG paint assertions wait for layout after a scale change.
