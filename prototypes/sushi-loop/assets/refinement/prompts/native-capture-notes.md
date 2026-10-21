# Native capture notes

These are technical observations, not previous art judgments. Inspect each object's actual source and contract independently.

- The world library may start with an unrelated character camera and excluded object collections. Link the intended asset collection into an isolated scene before measuring evaluated transforms; calling view-layer update on an excluded collection can leave stale matrices.
- Restore the object's recorded camera, using `mathutils.Matrix` for nested matrix values. Verify projected root, X/depth/height calibration and any attachment sockets numerically. Never fit a render to its visible bounds.
- Preserve the publisher's actual cardinal convention. The native world library's `native_actions.apply_clip` uses S0, E+90, N180, W-90 degrees. Do not assume N0. Validate labels against actual source asymmetric details and attachment directions, not just a self-consistent new dictionary.
- Runtime sprites generally use captureScale2; original camera records may describe raw captureScale4. A new scale2 capture needs honestly recalibrated metadata. Preserve logical dimensions/root and every clip/facing override.
- Inspect the exact Blender version and API. Background Blender is available at `/opt/homebrew/bin/blender` (5.2.2 LTS during this run).
- Cycles Metal is available: device `Apple M4 (GPU - 10 cores)`, type `METAL`. For new unsealed rounds, GPU rendering may help full animation export: set Cycles preferences compute_device_type to METAL, refresh_devices, enable the Metal device and set scene.cycles.device to GPU. Record the actual setting; review exact output bytes. Do not rerender an approved round to switch devices.
- For animated deformations, modifier topology can change when a bend crosses a bevel angle threshold. Validate evaluated topology through every frame; bake stable bevel/thickness geometry before shape keys where needed.
- Saved libraries can retain unrelated unused image datablocks. Audit external images/linked libraries after isolating and reopening the saved candidate.
- Use one native material/light configuration for all rotations, no per-facing recoloring or raster correction. Observe the object's seam, rig and shadow constraints. Modular tile edges may deliberately meet the frame; preserve their declared connection planes.
- Handoff raw frame records explicitly as `{clip, direction, index, path}` when possible. Preserve complete native frames and original atlas dimensions/rects; provide actual motion previews for every animated clip/facing.
- Record measured `rootRotationZ` (radians), `rootRotationDegrees`, or the actual `rootMatrix` with each native render entry's `direction` in validation. The coordinator now checks measured rotations against the original publisher before promotion.
- Finish the turn when a complete candidate is ready so other objects can use the agent slot. The coordinator seals its exact files and the independent judge reviews it.
