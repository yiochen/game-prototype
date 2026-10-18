# Experimental height projection comparison

An isolated camera study for issue #33. No height ratio has been adopted, and the production sprite library and both restaurant/underwater scenes are unchanged.

The five standalone environment examples are the wooden stool, wooden crate, east conveyor, rock wall middle, and underwater boulder. Lena uses one frozen south-facing held-dish pose (native frame 6). The context assembly contains a straight–corner–straight conveyor with a stool, crate and boulder. This study has no animation.

Every group is captured at 100%, 70%, 50% and 40% projected height. The geometry, material values, world transforms, pose, horizontal scale, ground depth, frame and ground root are identical across those captures. `screenX = 128*x`, `screenY = 128*(depth - k*height)`. The camera elevation and pixel aspect change together, preserving 128×128 logical-pixel square floor cells. No finished sprite is squashed, fitted or cropped. All 29 retained RGBA PNGs are direct 4× Blender captures.

Lena also has a separately labeled ordinary orthographic 35° reference using the same frozen pose. That is the existing character-camera profile; the 100% environment projection is not her production baseline. As with any camera change, reduced height changes which modeled surfaces are visible. It does not redesign the character proportions.

`projection-study.blend` is an isolated editable Blender library containing only study geometry, materials, rig, camera and lighting. It was saved with `bpy.data.libraries.write` so the unrelated project open in the user's Blender was not overwritten. The existing rig action cohort was copied to a separate rig, evaluated at frame 6 and frozen. Original rigged/animated source remains in the production source library.

`study.json` identifies the native project and per-group images. `cameras/` records actual camera matrices, root/axis calibration, source mesh bindings, pose, geometry, material and world-transform identities, and PNG SHA256 receipts. The original creation script fingerprint and the later schema-compatible capture script fingerprint are recorded separately. Before/after production presentation checks cover transforms, mesh data, poses and visibility at study creation; material records verify the frozen study consistently across captures. They do not retroactively add materials to the earlier presentation snapshot.

Re-render the unchanged frozen project from this folder (Blender 5.2.2):

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background projection-study.blend --python source/capture_projection_study.py -- --capture --manifest study.json
python3 source/audit_projection_study.py study.json --expect-groups 7 --require-alpha --report native-audit.json
```

The audit needs Pillow for alpha-bound checks. It independently derives projection from the retained 4×4 camera matrices, verifies actual file dimensions and hashes, checks unchanged geometry/material/placement identities and frame/root registration, and rejects alpha-edge clipping. The render script verifies the frozen `.blend` SHA before rendering.

The study keeps existing form shading and lighting. Runtime ground-contact shadows and ambient lighting remain a separate future Godot pass.
