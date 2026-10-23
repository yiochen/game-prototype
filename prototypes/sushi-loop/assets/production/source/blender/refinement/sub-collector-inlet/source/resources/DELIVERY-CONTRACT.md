# Native delivery interface

Keep native art and measured evidence independent of the catalog/import metadata. Before sealing, check `tools/promote_object.py`, `tools/audit_directions.py`, `tools/save_runtime_variant_approval.py` and `godot/tools/refined_actor_variants.py` against the handoff. Do not repair metadata by changing reviewed pixels or source geometry. If a handoff is already immutable, retain it and create a new versioned delivery/validation adapter that binds the original and every new alias.

Main delivery fields are `asset`, `project` (object-relative editable `.blend`), `recipeScript` (portable native reproduction script), `validation`, `nativeRecords` (`camera`, `assetRecord`, `rig`), `heroes`, `previews`, `rawFrames`, `atlases` and `resources`. All paths are object-relative. Sources, exact native frames, atlases, playback, validation, dependencies and retained failed drafts belong in the packet resource closure. A hash manifest alone does not automatically retain all its referenced files in the packet or Git index. Include actual resource paths, including needed `.blend1` draft sources; exclude caches.

Use explicit raw-frame records; do not rely on filenames to associate clips or facings:

```json
{"clip":"stand","direction":"S","index":0,"path":"candidates/round-01/frames/stand-S/000.png","sha256":"actual SHA256"}
```

Each atlas record has `clip`, `direction`, `path`, `sha256`, `columns`, `rows`, `size`, `rects`, numeric `fps`, boolean `loop`, and `frameOrder`. Preserve the original complete native frame regions and original frame order; adding metadata never rearranges pixels. For customer main/runtime atlases:384×640 native frames,6×2 placement,2304×1280 canvas,12fps, indices0..11. Main nonloop states retain their original loop flags; supplemental `eat-salmon` and `seated-wait-empty` both loop.

The measured camera record exposes logical `frame`, `anchor`, `captureScale`, `fps` and the actual `camera` transform/projection. Current customer values are192×320/root96,248/scale2; retained historical scale4 records are provenance, not current measurements. If using another measured schema, bind it and its native validation explicitly and translate without changing the recorded values.

The direction audit must reach actual measured native phase evidence through the packet-bound validation. Accepted layouts include `renders`/`nativeCaptures` records, `nativeValidation` pointing at another packet-bound audit, or `renderManifest` pointing at measured records. Each phase names its measured `direction` and supplies `rootRotationZ` (radians), `rootRotationDegrees`, `rootMatrix` or `actualRootMatrix`. Never synthesize a rotation from a filename, expected direction or brief; preserve the source audit references and hashes when translating an existing native audit layout.

For existing supplemental actor bundles, `runtimeVariants` includes `project`, `recipe` or `recipeScript`, `validation`, `nativeRecords`, `rawFrames`, `atlases`, `previews`, `publishedSourceScale` and `nativeCaptureScale`. Both scales are2 for the current native customer exports, proved by actual capture records/frame dimensions. Runtime frame/atlas records use the same explicit schema above. Exactly96frames/eight atlases per existing actor bundle; canonical food and original registration/timing are checked again by the import adapter. The runtime receipt can be saved only after that exact main packet and independent review are promoted. Production still requires all four customer bundles.

Deformation checks must cover the actual remodeled surfaces and their intended weights/groups, in addition to unchanged rig/socket paths. Inspect palms/thumbs, soles, seated support and mouth contacts through all required poses and real temporal playback. Source and supplemental models must agree in geometry, materials and deformation weights; similarly named material suffixes are not proof of matching shaders.
