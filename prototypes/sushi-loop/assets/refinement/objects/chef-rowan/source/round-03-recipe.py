"""Round03 continuous native billboard occlusion law; exact round01 baseline."""
import bpy,json,hashlib,math
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent;TARGET=HERE/'round-03.blend'
BASESHA='9dffcad37fb5ba662000a919c355fe45e74416078371e82adf2aa012038be024'
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==BASESHA
brief=json.loads((OBJ/'brief-v4-food-occlusion.json').read_text());rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
assert hashlib.sha256((OBJ/'brief-v4-food-occlusion.json').read_bytes()).hexdigest()=='f43e0bd90a39b507cad331129b0b0958d4fff44e96426b59d75121fb0ea41d37'
root=bpy.data.objects[rig['groundRootObject']];plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane']
prior=[dict(path=f.data_path,index=f.array_index,expression=f.driver.expression) for f in plane.animation_data.drivers]
assert len(prior)==3
law='(0.60-0.15*max(0,-cos(facing))**2)'
xy=math.cos(math.radians(35))/root.scale.x;z=math.sin(math.radians(35))/root.scale.x
for f in plane.animation_data.drivers:
 if f.data_path=='location':f.driver.expression=f'-{"sin" if f.array_index==0 else "cos"}(facing)*{xy!r}*{law}'
f=plane.driver_add('location',2);f.driver.type='SCRIPTED';f.driver.expression=f'{z!r}*{law}'
v=f.driver.variables.new();v.name='facing';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='rotation_euler[2]'
for curve in plane.animation_data.drivers:
 if curve.data_path=='location':
  while len(curve.keyframe_points):curve.keyframe_points.remove(curve.keyframe_points[0])
  mod=curve.modifiers.new('GENERATOR');mod.mode='POLYNOMIAL';mod.poly_order=1;mod.coefficients=(0.,1.)
plane['camera_ray_depth_bias_world_cells']='d(f)=0.60-0.15*max(0,-f)^2; f=cos(rootYaw); native XYZ drivers'
plane['food_occlusion_policy_brief']='brief-v4-food-occlusion.json'
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),relative_remap=False)
record=dict(activeBrief='brief-v4-food-occlusion.json',baseline='inputs/baseline-round01.blend',baselineSHA256=BASESHA,project='source/round-03.blend',projectSHA256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),foodOcclusionPolicy=brief['foodOcclusionPolicy'],nativeLawExpression=law,localRayCoefficients=dict(xy=xy,z=z),rootScale=root.scale.x,priorDrivers=prior,currentDrivers=[dict(path=f.data_path,index=f.array_index,expression=f.driver.expression) for f in plane.animation_data.drivers],allowedChanges=['existing plane location X/Y driver expressions and native polynomial identity mapping (remove default keyed identity; generator coefficients0,1)' ,'added plane location Z native driver using the same root yaw input and native polynomial identity mapping coefficients0,1','existing depth provenance replaced with exact law string','new active policy provenance string'],scope='No geometry, rotation/yaw driver, scale, parent, UV, material, rig/action, visibility, camera, light or render changes.',reconstruction='Apply only to exact included round01 baseline; saved-source recapture requires no library reconstruction or external driver namespace.')
(HERE/'round-03-recipe.json').write_text(json.dumps(record,indent=2)+'\n')
