"""Round02: exact round01 saved-source depth-only repair, no reconstruction."""
import bpy,json,hashlib,math
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent
BASE=OBJ/'inputs/baseline-round01.blend';TARGET=HERE/'round-02.blend';DEPTH=.45
expected='9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024'
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==expected
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane']
assert plane.get('camera_ray_depth_bias_world_cells')==.6
coefficient=DEPTH/root.scale.x*math.cos(math.radians(35));z=DEPTH/root.scale.x*math.sin(math.radians(35))
old=dict(location=list(plane.location),drivers=[dict(path=f.data_path,index=f.array_index,expression=f.driver.expression) for f in plane.animation_data.drivers])
assert len(plane.animation_data.drivers)==3
for f in plane.animation_data.drivers:
 if f.data_path=='location':
  assert f.array_index in [0,1]
  f.driver.expression=f'-{"sin" if f.array_index==0 else "cos"}(facing)*{coefficient!r}'
plane.location.z=z;plane['camera_ray_depth_bias_world_cells']=DEPTH
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),relative_remap=False)
record=dict(activeBrief='brief-v3-food-depth.json',baseline='inputs/baseline-round01.blend',baselineSHA256=expected,
            project='source/round-02.blend',projectSHA256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),
            scope='Only two existing ray-driver coefficients, derived constant planeZ, and existing depth provenance property changed. No body/rig/material/camera/light/action edits.',
            depthWorldCells=DEPTH,rootScale=root.scale.x,localHorizontalCoefficient=coefficient,localPlaneZ=z,
            worldRay=[0,-math.cos(math.radians(35)),math.sin(math.radians(35))],prior=old,
            current=dict(location=list(plane.location),drivers=[dict(path=f.data_path,index=f.array_index,expression=f.driver.expression) for f in plane.animation_data.drivers]),
            selection='Representative N/E/S/W hold01/load06 tested at d0,.15,.30,.45. d0 buries front dish; d.45 retains coherent front/profile plate while removing rear crescent. All192 final evaluations/captures and unchanged projected corners required before submission.',
            reconstruction='Requires exact baseline-round01.blend; this recipe does not rebuild from original library. Saved-source capture uses packed image and local action helper.')
(HERE/'round-02-recipe.json').write_text(json.dumps(record,indent=2)+'\n')
