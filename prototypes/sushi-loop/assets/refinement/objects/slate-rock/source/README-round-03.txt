Native slate-rock warm soft candidate round 03

Project: source/round-03.blend
Scene: slate-rock warm soft native round 03
Root: slate-rock__root.001
Collection: S33_PROP_slate-rock.001

Render saved source:
/opt/homebrew/bin/blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output-directory

Capture: native 384x704, logical 192x352, sourceScale 2, root 96,248, static frame 1 at 12 fps. The self-contained project has native meshes and procedural materials, symmetric soft lights, no ground receiver and transparent film. Rotate only the root: N=180, E=90, S=0, W=-90 degrees. This is the original native_actions.py/publish_captures.py convention.
Round-03 recipe reads the immutable hash-checked round-02 project; it preserves geometry/material/light fingerprints and corrects only scene/facing metadata before fresh native captures. The saved round-03 project has no external dependencies. The earlier round-02 recipe remains the full rebuild from the untouched production source. Round 02 and its sealed packet are unchanged. Round 03 is the submitted corrected candidate.
