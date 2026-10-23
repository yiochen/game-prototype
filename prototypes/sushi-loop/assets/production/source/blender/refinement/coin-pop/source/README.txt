Coin Pop round-01 native reproducibility

Run commands from any working directory using absolute script paths. In a copy of the object bundle:
1. blender -b --python source/build_round01.py
   Uses the preserved byte-exact original-library.blend. Rebuilds native geometry, semantic transform actions, one registered camera and symmetric lighting; saves round-01.blend and all48 native frames.
2. Pillow-enabled Python: source/package_round01.py
   Packs exact whole-frame atlases, renders diagnostic canvases and prepares the retained isolated native Godot fixture. Uses its bundled current renderer/registered context resources on replay; repository paths are needed only for first preparation.
3. Pillow-enabled Python: source/capture_runtime_round01.py
   Runs installed Godot import then captures actual viewport frames. Requires a window-capable native renderer for viewport pixels.
4. blender -b source/round-01.blend --python source/audit_native_round01.py
5. Pillow-enabled Python: source/finalize_round01.py
   Encodes native and runtime movies with ffmpeg; computes structural and raster validation. Actual temporal browser observation is retained separately in previews/playback-complete.txt and screenshots.
6. source/complete_handoff_round01.py verifies atlas pixels and updates delivery/resource closure.

Use a separate copy for replay. Do not change any sealed/reviewed round. Independent visual approval is pending. No production files, frozen brief, target, or reviews were changed by this editor.

Draft-01 retained the overbright material/light trial. Draft-02 retained the lower-light trial before a slight stable native face-material lift. Runtime harness drafts preserve two parser repair attempts. All are immutable retained provenance, not candidate art.
