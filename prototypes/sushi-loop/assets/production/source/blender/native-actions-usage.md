# Native action library adapter

`native_actions.py` runs inside Blender through Blender MCP. It does not invoke rendering or overwrite the user's working Blender file.

```python
# N is the imported native_actions module; r is capture_runtime.
record = N.bake_asset('chef-lena', r.assets['chef-lena'],
    '/private/tmp/sushi33-production/export/source/native-actions')
r.native_records['chef-lena'] = record

# Assign all native owners belonging to one clip, including rig, held plate,
# utensil visibility, shape keys and material phase. This calls no pose callback.
N.apply_clip(r.assets['chef-lena'], record, 'hold', frame=6, direction='S')

# Incremental batches read and merge their existing library-actions.json.
summary = N.bake_registry(r, ['rock-wall-middle','reef-corner'])
r.native_records.update(summary['assets'])

# All editable models can be retained while motion baking is still partial.
# The export report explicitly lists model-only assets without baked actions.
N.save_production_library(
    '/private/tmp/sushi33-production/export/source/sushi33-library.blend',
    r.assets, r.native_records, production_scene=r.scene(),
    allow_unbaked_models=True)
```

Every clip has its own group of actions, one per animated Blender owner. A character's main rig action is accompanied by any necessary plate, knife and child visibility actions. A conveyor has a native shader-phase action. Animated cable and water meshes use actual sampled shape keys. Static assets remain editable models and are declared static; their lack of motion is not disguised as an animation.

Records retain bone names/rest matrices, original frame counts at12fps, loop closure conventions, source hashes, object/Key/NodeTree owner names, action slot identifiers, frame controls, sockets and feet where the character builder exposes them. Closing keys are native interpolation controls only and never additional runtime sprite frames. Conveyor closing shader values remain unwrapped so interpolation follows travel rather than reversing through the phase wrap.

The adapter samples procedural clips with action bindings detached, then restores the prior visible pose and bindings. A small in-memory bridge keeps procedural shape callbacks usable after native geometry keys have been added. Full scene visual validation remains necessary; native key counts and source records do not establish perceptual quality.

Export creates a temporary scene containing only the supplied production collections, selected S33 camera/lights and their explicitly owned actions. It writes that scene using`bpy.data.libraries.write`, restores the prior scene/visibility and removes only its temporary export scene. Existing user scenes are never included or deleted.

The exact first37-record bake source is preserved in`source-history/native_actions-865658f9deaa.py`. The corrected current version additionally activates the temporary export scene before accessing its view-layer collection tree.
