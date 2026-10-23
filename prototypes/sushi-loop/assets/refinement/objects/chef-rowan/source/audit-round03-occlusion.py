"""Compact saved-source semantic,192-pose and intermediate-angle occlusion audit."""
import bpy,math,json,hashlib,importlib.util,ast
from pathlib import Path
from mathutils import Vector,Matrix,Euler
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';OUT.mkdir(exist_ok=True)
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());brief=json.loads((OBJ/'brief-v4-food-occlusion.json').read_text())
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze(v):return json.loads(json.dumps(v,default=lambda x:list(x)))
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def flat(o):
 result={}
 for p in o.bl_rna.properties:
  if p.identifier=='rna_type' or p.is_readonly:continue
  try:
   v=getattr(o,p.identifier)
   if p.type in ['BOOLEAN','INT','FLOAT','STRING','ENUM']:result[p.identifier]=list(v) if p.is_array else sorted(v) if isinstance(v,set) else v
   elif p.type=='POINTER':result[p.identifier]=v.name if isinstance(v,bpy.types.ID) else None
  except (AttributeError,TypeError,ValueError):pass
 return freeze(result)
def custom(o):
 return freeze({k:o[k].to_list() if hasattr(o[k],'to_list') else o[k].to_dict() if hasattr(o[k],'to_dict') else o[k] for k in o.keys() if k!='_RNA_UI' and not (o.name.endswith('__image_plane') and k in ['camera_ray_depth_bias_world_cells','food_occlusion_policy_brief'])})
def driver(f):return dict(path=f.data_path,index=f.array_index,settings=flat(f),type=f.driver.type,expression=f.driver.expression,mappingKeyframes=[dict(co=list(k.co),interpolation=k.interpolation,left=list(k.handle_left),right=list(k.handle_right),leftType=k.handle_left_type,rightType=k.handle_right_type) for k in f.keyframe_points],mappingModifiers=[dict(type=m.type,coefficients=list(m.coefficients) if hasattr(m,'coefficients') else None,settings=flat(m)) for m in f.modifiers],variables=[dict(name=v.name,type=v.type,settings=flat(v),targets=[dict(object=getattr(t.id,'name',None),dataPath=t.data_path,settings=flat(t)) for t in v.targets]) for v in f.driver.variables])
def drivers(o):
 result=[]
 if not o.animation_data:return result
 for f in o.animation_data.drivers:
  if o.name.endswith('__image_plane') and f.data_path=='location' and f.array_index==2:continue # Only explicitly permitted new Z driver, audited in full separately.
  d=driver(f)
  if o.name.endswith('__image_plane') and f.data_path=='location' and f.array_index in [0,1]:
   d['expression']='PERMITTED_XY_RAY_EXPRESSION_ONLY'
   d['mappingKeyframes']='PERMITTED_KEYED_TO_GENERATOR_IDENTITY_MAP'
   d['mappingModifiers']='PERMITTED_NATIVE_IDENTITY_GENERATOR_ONLY'
  result.append(d)
 return result
def node_tree(t):
 return freeze(dict(nodes=[dict(name=n.name,type=n.bl_idname,settings=flat(n),inputs=[dict(name=s.name,identifier=s.identifier,value=s.default_value) for s in n.inputs if hasattr(s,'default_value')]) for n in t.nodes],links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links])) if t else None
def semantic():
 root=bpy.data.objects[rig['groundRootObject']];plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];arm=bpy.data.objects[rig['armatures'][0]['object']];objects=[]
 for o in bpy.context.scene.objects:
  props=flat(o)
  if o==plane:
   props['location']=['PERMITTED_RAY_X','PERMITTED_RAY_Y','PERMITTED_RAY_Z']
   for key in ['matrix_basis','matrix_local','matrix_world']:
    if key in props:
     assert len(props[key])==4 and all(len(row)==4 for row in props[key])
     for i in range(3):props[key][i][3]='DERIVED_RAY_TRANSLATION_ONLY'
  objects.append(dict(name=o.name,settings=props,custom=custom(o),parentInverse=[list(r) for r in o.matrix_parent_inverse],modifiers=[flat(m) for m in o.modifiers],constraints=[flat(c) for c in o.constraints],groups=[flat(g) for g in o.vertex_groups],drivers=drivers(o)))
 meshes=[dict(name=m.name,vertices=[dict(co=list(v.co),weights=[(g.group,g.weight) for g in v.groups]) for v in m.vertices],edges=[list(e.vertices) for e in m.edges],polygons=[dict(vertices=list(p.vertices),material=p.material_index,smooth=p.use_smooth) for p in m.polygons],uv=[dict(name=l.name,values=[list(v.uv) for v in l.data]) for l in m.uv_layers],materials=[m.name for m in m.materials],attributes=[(a.name,a.data_type,a.domain) for a in m.attributes]) for m in bpy.data.meshes]
 actions=[dict(name=a.name,settings=flat(a),slots=[flat(s) for s in a.slots],fcurves=[dict(path=f.data_path,index=f.array_index,settings=flat(f),keys=[flat(k) for k in f.keyframe_points],modifiers=[flat(m) for m in f.modifiers]) for f in native._fcurves(a)]) for a in bpy.data.actions]
 bones=[dict(name=b.name,settings=flat(b),matrix=[list(r) for r in b.matrix_local],head=list(b.head_local),tail=list(b.tail_local),parent=b.parent.name if b.parent else None) for b in arm.data.bones]
 bindings=[dict(object=o.name,action=o.animation_data.action.name if o.animation_data and o.animation_data.action else None,slot=o.animation_data.action_slot.identifier if o.animation_data and o.animation_data.action_slot else None,nla=[dict(settings=flat(t),strips=[flat(s) for s in t.strips]) for t in o.animation_data.nla_tracks] if o.animation_data else []) for o in bpy.context.scene.objects]
 pose_constraints=[dict(bone=p.name,constraints=[flat(c) for c in p.constraints]) for p in arm.pose.bones]
 return freeze(dict(objects=objects,meshes=meshes,actions=actions,bones=bones,animationBindings=bindings,poseConstraints=pose_constraints,materials=[dict(name=m.name,settings=flat(m),nodes=node_tree(m.node_tree)) for m in bpy.data.materials],lights=[dict(name=l.name,settings=flat(l),nodes=node_tree(l.node_tree)) for l in bpy.data.lights],cameras=[dict(name=c.name,settings=flat(c)) for c in bpy.data.cameras],worlds=[dict(name=w.name,settings=flat(w),nodes=node_tree(w.node_tree)) for w in bpy.data.worlds],render=flat(bpy.context.scene.render),view=flat(bpy.context.scene.view_settings),display=flat(bpy.context.scene.display_settings),images=[dict(name=i.name,settings=flat(i),packedSHA256=hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None) for i in bpy.data.images if i.source in ['FILE','TILED']]))
ANGLES=sorted(set([-180,-179.999,-179.99,-170,-150,-120,-90.1,-90.01,-90.001,-90,-89.999,-89.99,-89.9,-45,0,45,89.9,89.99,89.999,90,90.001,90.01,90.1,120,150,170,179.99,179.999,180]))
def measure(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));snapshot=semantic();scene=bpy.context.scene;root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];arm=bpy.data.objects[rig['armatures'][0]['object']]
 plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];food=plane.parent;utensil=bpy.data.objects[root.name+'__utensil'];asset=dict(root=root,collection=col)
 plane_channels=dict(location=list(plane.location),rotation=list(plane.rotation_euler),scale=list(plane.scale),drivers=[driver(f) for f in plane.animation_data.drivers],custom={k:plane[k] for k in plane.keys() if k!='_RNA_UI'})
 col.hide_viewport=False;col.hide_render=False;arm.hide_set(False)
 def vis(lc):
  lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
  for c in lc.children:vis(c)
 vis(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update()
 R=(scene.camera.matrix_world.to_3x3()@Vector((0,0,1))).normalized();H=Vector((R.x,R.y,0)).normalized()
 assert max(abs(v) for v in plane.delta_location)<1e-9 and max(abs(v) for v in plane.delta_rotation_euler)<1e-9 and max(abs(v-1) for v in plane.delta_scale)<1e-9
 def project(p):
  q=world_to_camera_view(scene,scene.camera,p);return [q.x*384,(1-q.y)*640]
 def evaluate():
  bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rm=root.evaluated_get(dg).matrix_world;fm=food.evaluated_get(dg).matrix_world;ea=arm.evaluated_get(dg)
  yaw=float(root.rotation_euler.z);F=rm.to_3x3()@Vector((0,-1,0));F.z=0;F.normalize();f=max(-1.,min(1.,F.dot(H)));wanted=.60-.15*max(0,-f)**2
  loc=list(plane.location);rot=list(plane.rotation_euler)
  for curve in plane.animation_data.drivers:
   val=eval(curve.driver.expression,{'__builtins__':{}},{'sin':math.sin,'cos':math.cos,'max':max,'facing':yaw})
   if curve.data_path=='location':loc[curve.array_index]=val
   elif curve.data_path=='rotation_euler':rot[curve.array_index]=val
   else:raise AssertionError('Unexpected plane driver')
  basis=Matrix.Translation(loc)@Euler(rot,plane.rotation_mode).to_matrix().to_4x4()@Matrix.Diagonal((*plane.scale,1.))
  m=fm@plane.matrix_parent_inverse@basis;em=plane.evaluated_get(dg).matrix_world
  points=[m@v.co for v in plane.data.vertices]+[m@Vector((0,0,0))];epoints=[em@v.co for v in plane.data.vertices]+[em@Vector((0,0,0))]
  composed=[project(p) for p in points];evaluated=[project(p) for p in epoints];offset=m.translation-fm.translation
  contacts={}
  for side in ['L','R']:
   pb=ea.pose.bones['hand_'+side];rb=ea.data.bones['hand_'+side]
   contacts['palm_'+side]=list(ea.matrix_world@pb.matrix@rb.matrix_local.inverted()@(rb.head_local+Vector((0,-.002,-.046))))
   contacts['foot_'+side]=list(ea.matrix_world@ea.pose.bones['foot_'+side].head)
  body=[]
  for o in col.objects:
   if o.type=='MESH' and o!=plane:
    eo=o.evaluated_get(dg);mesh=eo.to_mesh();body.append(dict(name=o.name,vertices=[[float(x) for x in eo.matrix_world@v.co] for v in mesh.vertices],visible=not o.hide_render));eo.to_mesh_clear()
  matrices={o.name:[list(r) for r in o.evaluated_get(dg).matrix_world] for o in [root,arm,food,utensil]};matrices['pose']=[[list(r) for r in p.matrix] for p in ea.pose.bones]
  return dict(f=f,expectedD=wanted,composedD=offset.dot(R),evaluatedD=(em.translation-fm.translation).dot(R),cameraRayResidual=(offset-R*offset.dot(R)).length,composedPixels=composed,evaluatedVsComposedPixelError=max(abs(a-b) for p,q in zip(composed,evaluated) for a,b in zip(p,q)),visible=not plane.hide_render,worldPoints=[list(p) for p in points],worldWidth=(m.to_3x3()@Vector((.28,0,0))).length,worldHeight=(m.to_3x3()@Vector((0,.28*505/731,0))).length,worldRotation=[list(r) for r in m.to_3x3().normalized()],contacts=contacts,foodRoot=list(fm.translation),bodyKnifeSHA256=h(body),rigFoodUtensilSHA256=h(matrices))
 records=[]
 for clip in rig['clips']:
  for direction in ['N','E','S','W']:
   for frame in range(1,13):
    native.apply_clip(asset,rig,clip,frame,direction,scene);record=evaluate();record.update(clip=clip,direction=direction,index=frame-1);records.append(record)
 intermediates=[]
 native.apply_clip(asset,rig,'hold',1,'S',scene)
 for angle in ANGLES:
  root.rotation_euler.z=math.radians(angle);scene.frame_set(scene.frame_current);record=evaluate();record.update(angleDegrees=angle);intermediates.append(record)
 return snapshot,plane_channels,records,intermediates
baseline=OBJ/'inputs/baseline-round01.blend';candidate=HERE/'round-03.blend';a,ap,old,old_angles=measure(baseline);b,bp,new,new_angles=measure(candidate)
counts=dict(objects=len(a['objects']),meshes=len(a['meshes']),vertices=sum(len(m['vertices']) for m in a['meshes']),polygons=sum(len(m['polygons']) for m in a['meshes']),weightedVertexEntries=sum(len(v['weights']) for m in a['meshes'] for v in m['vertices']),uvLoops=sum(len(u['values']) for m in a['meshes'] for u in m['uv']),actions=len(a['actions']),bones=len(a['bones']),materials=len(a['materials']),lights=len(a['lights']),cameras=len(a['cameras']),packedImages=len(a['images']),poseConstraints=sum(len(p['constraints']) for p in a['poseConstraints']),objectConstraints=sum(len(o['constraints']) for o in a['objects']),modifiers=sum(len(o['modifiers']) for o in a['objects']))
sections={k:dict(baselineSHA256=h(a[k]),candidateSHA256=h(b[k]),equal=a[k]==b[k],recordCount=len(a[k]) if hasattr(a[k],'__len__') else 1) for k in a}
def compare(x,y):
 return dict(f=y['f'],d=y['expectedD'],nativeComposedD=y['composedD'],nativeEvaluatedD=y['evaluatedD'],lawDepthError=abs(y['composedD']-y['expectedD']),worldRayResidual=y['cameraRayResidual'],projectedQuadCornersAndPlateBottom=y['composedPixels'],baselineProjectedQuadCornersAndPlateBottom=x['composedPixels'],maximumNativePixelError=max(abs(a-b) for p,q in zip(x['composedPixels'],y['composedPixels']) for a,b in zip(p,q)),maximumContactError=max(abs(a-b) for k in x['contacts'] for a,b in zip(x['contacts'][k],y['contacts'][k])),foodRootError=max(abs(a-b) for a,b in zip(x['foodRoot'],y['foodRoot'])),evaluatedVsComposedNativePixelError=y['evaluatedVsComposedPixelError'],bodyKnifeEqual=x['bodyKnifeSHA256']==y['bodyKnifeSHA256'],rigFoodUtensilEqual=x['rigFoodUtensilSHA256']==y['rigFoodUtensilSHA256'],visibilityEqual=x['visible']==y['visible'],foodVisible=y['visible'],width=y['worldWidth'],height=y['worldHeight'],orientationError=max(abs(x['worldRotation'][i][j]-y['worldRotation'][i][j]) for i in range(3) for j in range(3)))
records=[dict(clip=y['clip'],direction=y['direction'],index=y['index'],**compare(x,y)) for x,y in zip(old,new)]
angles=[dict(angleDegrees=y['angleDegrees'],**compare(x,y)) for x,y in zip(old_angles,new_angles)]
# Native yaw is the sole variable on all four saved drivers; exact original yaw driver retained.
old_yaw=[f for f in ap['drivers'] if f['path']=='rotation_euler'];new_yaw=[f for f in bp['drivers'] if f['path']=='rotation_euler'];xyz=[f for f in bp['drivers'] if f['path']=='location']
driver_vars_ok=all(len(f['variables'])==1 and f['variables'][0]['name']=='facing' and f['variables'][0]['type']=='SINGLE_PROP' and f['variables'][0]['targets'][0]['object']==rig['groundRootObject'] and f['variables'][0]['targets'][0]['dataPath']=='rotation_euler[2]' for f in bp['drivers'])
for f in xyz:
 names={n.id for n in ast.walk(ast.parse(f['expression'],mode='eval')) if isinstance(n,ast.Name)};assert names<=set(['sin','cos','max','facing'])
 assert not f['mappingKeyframes'] and len(f['mappingModifiers'])==1 and f['mappingModifiers'][0]['type']=='GENERATOR' and f['mappingModifiers'][0]['coefficients']==[0.,1.]
near={a['angleDegrees']:a for a in angles};transition=[]
for center in [-90,90]:
 lo=near[center-.01];mid=near[center];hi=near[center+.01];hangle=math.radians(.01)
 transition.append(dict(angle=center,leftNativeSlopePerRadian=(mid['nativeEvaluatedD']-lo['nativeEvaluatedD'])/hangle,rightNativeSlopePerRadian=(hi['nativeEvaluatedD']-mid['nativeEvaluatedD'])/hangle,maximumDepthJump=max(abs(lo['nativeEvaluatedD']-mid['nativeEvaluatedD']),abs(hi['nativeEvaluatedD']-mid['nativeEvaluatedD']))))
checks=[dict(name='compact semantic sections equal except exact permitted depth fields',passed=all(v['equal'] for v in sections.values())),dict(name='native yaw cancellation driver unchanged',passed=old_yaw==new_yaw),dict(name='exactly three native location drivers, yaw input only, no external namespace',passed=len(xyz)==3 and {f['index'] for f in xyz}=={0,1,2} and driver_vars_ok),dict(name='192 registered native comparisons',passed=len(records)==192),dict(name='all192 screen corners/platebottom invariant under .001 native pixel',passed=max(r['maximumNativePixelError'] for r in records)<.001),dict(name='all192 exact law and orthographic ray',passed=all(r['lawDepthError']<1e-6 and r['worldRayResidual']<1e-6 for r in records)),dict(name='visible descendant evaluated matrix agrees with composed native geometry',passed=all(r['evaluatedVsComposedNativePixelError']<.001 for r in records if r['foodVisible'])),dict(name='all192 body/knife/root/rig/contact/visibility unchanged',passed=all(r['bodyKnifeEqual'] and r['rigFoodUtensilEqual'] and r['visibilityEqual'] and r['maximumContactError']<1e-6 and r['foodRootError']<1e-6 for r in records)),dict(name='all192 canonical width/aspect/orientation retained',passed=all(abs(r['width']-.35)<1e-6 and abs(r['height']-.35*505/731)<1e-6 and r['orientationError']<1e-6 for r in records)),dict(name='native intermediate-angle law/ray/projection and visible matrix checks',passed=all(r['lawDepthError']<1e-6 and r['worldRayResidual']<1e-6 and r['maximumNativePixelError']<.001 and r['evaluatedVsComposedNativePixelError']<.001 for r in angles)),dict(name='native depth slopes join continuously at f0',passed=all(abs(r['leftNativeSlopePerRadian'])<.001 and abs(r['rightNativeSlopePerRadian'])<.001 and r['maximumDepthJump']<1e-6 for r in transition))]
result=dict(activeBrief='brief-v4-food-occlusion.json',baseline='inputs/baseline-round01.blend',baselineSHA256=sha(baseline),source='source/round-03.blend',sourceSHA256=sha(candidate),serializer='source/audit-round03-occlusion.py',serializerSHA256=sha(Path(__file__)),foodOcclusionPolicy=brief['foodOcclusionPolicy'],counts=counts,semanticSections=sections,allowedNarrowDeltas=dict(locationXYZ='Only driver-computed translation components and corresponding derived matrix translation columns masked; all rotation/scale/matrix3x3/parent inverse and all other plane fields are compared.',driverExpressions='Only existing locationX/Y expression strings and identity-map representation (default keyed identity replaced by native polynomial generator0+1*x) masked; types/variables/targets/settings retained. Original mapping and exact replacement inspected explicitly in planeBefore/After. New locationZ driver inspected in full; original yaw driver including original mapping compared exactly.',provenanceKeys=['camera_ray_depth_bias_world_cells','food_occlusion_policy_brief']),planeBefore=ap,planeAfter=bp,hiddenMatrixPolicy='Projected points use the original composed native food parent matrix, saved yaw/XYZ driver expressions, unchanged rotation/scale/parent inverse and original plane vertices. Hidden authored descendants may have stale evaluated matrices; visible96 are separately checked against actual evaluated matrix. No hidden evaluated matrix is relabeled rendered geometry.',maximumNativePixelError=max(r['maximumNativePixelError'] for r in records),maximumVisibleEvaluatedVsComposedNativePixelError=max(r['evaluatedVsComposedNativePixelError'] for r in records if r['foodVisible']),maximumHiddenEvaluatedVsComposedNativePixelError=max(r['evaluatedVsComposedNativePixelError'] for r in records if not r['foodVisible']),checks=checks,allChecksPassed=all(c['passed'] for c in checks),records=records,intermediateAngles=angles,C1=dict(analytic='d prime=-.30*f on f<0 and0 on f>=0, meeting at0; native intermediate angle samples validate exact saved expression and approach slopes.',nativeTransitionSlopes=transition,evaluationPolicy='After each root orientation assignment, scene.frame_set(currentFrame) invokes normal native animation/driver evaluation, matching native.apply_clip capture. Location drivers use a saved native polynomial identity generator0+1*x, avoiding the default keyed identity endpoint snap for tiny outputs. Original yaw mapping remains unchanged.'))
(OUT/'occlusion-native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['records','intermediateAngles','planeBefore','planeAfter','foodOcclusionPolicy']},indent=2));assert result['allChecksPassed']
