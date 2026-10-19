# Compact organic study review

Browser feedback requested: no continuous gap before rock bases; less uniformly carved pillars; fuller coral forms; capture shading that does not change with a light direction; vertical rise under three tiles.

The revised meshes have offset shoulders, width changes, larger irregular planes and uneven broad crowns. Coral uses thick-lipped flared sponges and asymmetric branching forms; the first flat-looking coral pass is retained under iterations/first-coral-pass. A second pass adds symmetric form tone and more irregular branches. No plant is stretched to gain rock height.

All 45 materials are connected emission surfaces; the isolated scene has no lights and zero world illumination. Rock tone depends on world Z and normal Z, invariant under quarter-turns. Lower darkening is material-driven; future Godot contact shadows remain separate. Material inspection is bound to the exact source/project hashes.

The low-camera capture now preserves a full square footing with a documented native projection-space deformation below 0.42 world units. Physical source geometry remains 1×1. Actual evaluated capture geometry is exported for every frame and bound to receipts. It is not a pure 35° camera for the whole object; the page labels the upper-view/footing split explicitly. The continuous front gap is removed; natural edge notches remain. At the sampled near-front row, opaque coverage is 42–75% across facings and identical between camera profiles; projected extremities reach both tile boundaries. This is stronger than the prior low-camera depth, which stopped an entire strip short of the front edge.

All 41 captures pass native audits: source/project/image/geometry hashes, 92.1% top-down physical coverage, 1×1 source bounds, calibrated axes, irregular widths, uneven crowns, three growth bands, alpha margins and front-edge coverage. Maximum 35° vertical rises: 1.03 / 1.67 / 2.26 / 2.81 / 1.90 tiles, all strictly below 3. The same geometry at 70% is shorter. Native angle views, raw captures and final phone patch/shoreline screenshots were visually inspected.

164 engine tests, production build and three responsive browser checks pass at 390×844, 844×390 and 1440×1200. Checks include actual profile switching, unchanged floor registration, every displayed height below three, native image dimensions, layer/facing/patch controls and one document scrollbar. Issue 33 and final visual approval remain open.
