"""Read-only source-law feasibility audit; no source/candidate modifications or renders."""
import bpy,sys,pathlib,json,hashlib,importlib.util,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parents[2];R=B/'reviews/held-food-v3';H=B.parents[2]/'production/source/blender'
s=importlib.util.spec_from_file_location('omar_v3_source_native',H/'native_actions.py');native=importlib.util.module_from_spec(s);sys.modules[s.name]=native;s.loader.exec_module(native)
brief=json.loads((B/'brief-v3-held-food-occlusion.json').read_text());out={}
for name,project,rp,gp,key in [('salmon',B/'../../../production/source/blender/refinement/chef-omar/source/round-01.blend',B/'source/recipe-round01.json',B/'source/rig-round01.json','foodDependency'),('cucumber',B/'source/runtime-round-01.blend',B/'source/runtime-recipe-round01.json',B/'source/runtime-rig-round01.json','runtimeVariantFoodDependency')]:
 bpy.ops.wm.open_mainfile(filepath=str(project.resolve()));recipe=json.loads(rp.read_text());rig=json.loads(gp.read_text());sc=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=bpy.data.collections[recipe['collection']];root=bpy.data.objects[recipe['root']];asset={'root':root,'collection':coll};plane=next(o for o in coll.all_objects if '__image_plane' in o.name);parent=plane.parent;cameraToward=(sc.camera.matrix_world.to_3x3()@Vector((0,0,1))).normalized();camHorizontal=Vector((cameraToward.x,cameraToward.y,0)).normalized();semanticLocalForward=Vector((0,-1,0));w,h=brief[key]['canonicalSize'];localWidth=max(v.co.x for v in plane.data.vertices)-min(v.co.x for v in plane.data.vertices);localHeight=localWidth*h/w;localPoints=[Vector((-localWidth/2,0,0)),Vector((localWidth/2,0,0)),Vector((localWidth/2,localHeight,0)),Vector((-localWidth/2,localHeight,0)),Vector((0,0,0))];rows=[];d0s=[];parentBasisErrors=[]
 def px(v):
  p=world_to_camera_view(sc,sc.camera,v);return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 def observe(clip,frame,theta,direction):
  native.apply_clip(asset,rig,clip,frame,direction,sc);root.rotation_euler.z=theta
  props=[parent,plane];vis=[(o.hide_render,o.hide_viewport,o.hide_get()) for o in props]
  for o in props:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
  sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();pm=parent.evaluated_get(dg).matrix_world.copy();M=plane.evaluated_get(dg).matrix_world.copy();origin=M@Vector((0,0,0));offset=origin-pm.translation;d0=offset.dot(cameraToward);d0s.append(d0);perp=(offset-cameraToward*d0).length;forward=(root.matrix_world.to_3x3()@semanticLocalForward).normalized();f=Vector((forward.x,forward.y,0)).normalized().dot(camHorizontal);points=[M@v for v in localPoints];errors=[]
  for ratio in [0,.5,1]:
   dmin=d0*ratio;d=d0-(d0-dmin)*max(0,-f)**2;delta=cameraToward*(d-d0)
   errors.append({'dMinFractionOfD0':ratio,'depth':d,'maxProjectedVertexOrBottomDeltaNativePx':max((px(p+delta)-px(p)).length for p in points),'offRayDisplacement':delta.cross(cameraToward).length})
  expected=(root.matrix_world.to_3x3());actual=pm.to_3x3();basis=max(abs(expected[i][j]-actual[i][j]) for i in range(3) for j in range(3));parentBasisErrors.append(basis)
  record={'clip':clip,'index':frame-1,'direction':direction,'rootDegrees':math.degrees(theta),'semanticForwardDotCameraHorizontal':f,'sourceD0World':d0,'sourceOffsetOffRayWorld':perp,'parentLinearBasisDifferenceToRoot':basis,'rangeBoundaryTests':errors}
  for o,v in zip(props,vis):o.hide_render=v[0];o.hide_viewport=v[1];o.hide_set(v[2])
  return record
 for clip in rig['clips']:
  for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
   for i in range(12):rows.append(observe(clip,i+1,math.radians(degrees),direction))
 transitions=[]
 angles=[-180,-135,-91,-90.1,-90.01,-90,-89.99,-89.9,-89,-45,0,45,89,89.9,89.99,90,90.01,90.1,91,135,180]
 for deg in angles:transitions.append(observe('hold-cucumber' if name=='cucumber' else 'hold',6,math.radians(deg),'S'))
 out[name]={'sourceSHA256':hashlib.sha256(project.read_bytes()).hexdigest(),'semanticLocalGroundForward':[0,-1,0],'derivation':'Actual source S front has its face/mouth toward local-Y; root source phases are S0,E+90,N180,W-90. Fixed camera horizontal points-Y. Thus f=cos(rootYaw) for this source, independent of action phase.','fixedCameraTowardUnit':list(cameraToward),'fixedCameraHorizontalUnit':list(camHorizontal),'sourceD0RangeWorld':[min(d0s),max(d0s)],'shippingFrameCount':len(rows),'shippingFrames':rows,'intermediateAngleSamples':transitions,'maxProjectedErrorNativePx':max(e['maxProjectedVertexOrBottomDeltaNativePx'] for r in rows+transitions for e in r['rangeBoundaryTests']),'maxSourceOffsetOffRayWorld':max(r['sourceOffsetOffRayWorld'] for r in rows+transitions),'maxParentLinearBasisDifferenceToRoot':max(parentBasisErrors),'noCandidateOrSourceWrite':True}
(R/'source-policy-feasibility.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:{n:v[n] for n in ['sourceD0RangeWorld','shippingFrameCount','maxProjectedErrorNativePx','maxSourceOffsetOffRayWorld','maxParentLinearBasisDifferenceToRoot']} for k,v in out.items()},indent=2))
