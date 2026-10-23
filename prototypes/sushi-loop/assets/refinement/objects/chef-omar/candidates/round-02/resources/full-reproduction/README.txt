Omar canonical food v3 native reproduction closure

All paths in the native scripts resolve relative to their source directory. Required runtime: Blender5.2.2 with bundled NumPy; PNG/video packaging uses Python+Pillow+NumPy and ffmpeg/ffprobe. GPU capture uses the saved Cycles GPU device settings and the available Metal device; do not change frozen scene renderer settings.

From the enclosing source directory:
blender --background --python build_food_round02.py
blender --background --python capture_audit_food_round02.py
blender --background --python capture_audit_food_round02.py -- --runtime
blender --background --python audit_orientation_food_round02.py
blender --background --python correct_culled_food_audit_round02.py
blender --background --python audit_hidden_meshes_round02.py
blender --background --python replay_food_round02.py -- --output ../candidates/round-02/fresh-replay
python package_food_round02.py
python finalize_food_round02.py
python close_food_round02.py

The separate portable-replay/source directory is the exact copied native source/code closure used by the recorded fresh replay. Its initial helper version is retained. The full reproduction closure includes the completed viewport-only food-transform diagnostic and rigid hidden-knife reconstruction audit. Hidden knife world vertices/normals use native local geometry and actual evaluated utensil parent, without toggling mesh visibility. The reconstruction is separately cross-checked against all actual evaluated visible work knife poses. No hide_render/controller or saved project change is needed for these diagnostics.
