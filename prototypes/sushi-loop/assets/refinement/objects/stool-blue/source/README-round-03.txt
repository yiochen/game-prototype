Native stool-blue warm soft candidate round 03

Project: source/round-03.blend
Scene: stool-blue warm soft native
Root: stool_blue__root.001
Collection: S33_PROP_stool_blue.001

Render saved source without rebuilding:
/opt/homebrew/bin/blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output-directory

Capture: native 384x704, logical 192x352, sourceScale 2, root 96,248, 12 fps, static frame 1. The saved project has neutral symmetric lighting, no ground plane and transparent film. Rotate only the common root for N=180, E=90, S=0, W=-90 degrees. All geometry and procedural material resources are packed in the scene. Full rebuild recipe: source/round-03.py. It opens immutable source/round-02.blend and uses the original native_actions.py:468 direction mapping, both hash-bound in candidates/round-03/validation.json. Original source is never resaved. Source input metadata uses legacy scale 4; delivered camera and asset records use actual capture scale 2.
