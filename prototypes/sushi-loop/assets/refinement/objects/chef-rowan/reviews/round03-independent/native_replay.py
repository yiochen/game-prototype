import bpy,json,pathlib,importlib.util,hashlib,math,struct,shutil
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).parents[2];O=pathlib.Path(__file__).parent;C=O/'closed';C.mkdir(exist_ok=True)
for src,dst in [(B/'source/round-03.blend',C/'rowan.blend'),(B/'source/resources/original-native-actions.py',C/'native_actions.py'),(B/'inputs/source-rig.json',C/'rig.json')]:
 if not dst.exists():shutil.copyfile(src,dst)
spec=importlib.util.spec_from_file_location('judge_native',C/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);rig=json.loads((C/'rig.json').read_text())
def hashdata(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def conv(x):
 if isinstance(x,(str,int,float,bool))or x is None:return x
 if isinstance(x,set):return sorted(conv(v)for v in x)
 if isinstance(x,bpy.types.ID):return {'id':x.name,'type':x.bl_rna.identifier}
 if hasattr(x,'bl_rna'):return {'rna':x.bl_rna.identifier,'props':props(x)}
 try:return [conv(v)for v in x]
 except:return str(x)
def props(x):
 d={}
 for p in x.bl_rna.properties:
  if p.identifier in ['rna_type','id_data','name','name_full','original','users','use_fake_user','is_evaluated','library','override_library','preview','animation_data','session_uid']:continue
  if p.type in ['BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER']:
   try:d[p.identifier]=conv(getattr(x,p.identifier))
   except:pass
 return d
def nodes(tree):return {'nodes':[{'name':n.name,'type':n.bl_idname,'props':props(n),'inputs':[{'name':s.name,'value':conv(getattr(s,'default_value',None))}for s in n.inputs]}for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name)for l in tree.links]}
def drivers(o):
 return [{'path':d.data_path,'index':d.array_index,'expression':d.driver.expression,'type':d.driver.type,'mute':d.mute,'variables':[(v.name,v.type,[(t.id.name if t.id else None,t.data_path,t.transform_type,t.transform_space)for t in v.targets])for v in d.driver.variables],'keyframes':[(list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right),k.handle_left_type,k.handle_right_type)for k in d.keyframe_points],'modifiers':[{'type':m.type,'properties':props(m)}for m in d.modifiers]}for d in o.animation_data.drivers]if o.animation_data else []
def setup(path):
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);sc=bpy.context.scene;bpy.context.window.scene=sc
 col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];root=bpy.data.objects['chef_rowan__ground_root.001'];arm=bpy.data.objects['chef_rowan__armature.001']
 def unhide(l):
  l.exclude=False;l.hide_viewport=False;l.collection.hide_viewport=False
  for c in l.children:unhide(c)
 unhide(bpy.context.view_layer.layer_collection);col.hide_viewport=False;col.hide_render=False
 for o in col.all_objects:o.hide_set(False)
 bpy.context.view_layer.update()
 a={'root':root,'collection':col,'armature':arm};native.apply_clip(a,rig,'idle',1,'S',sc);bpy.context.view_layer.update()
 return sc,col,root,arm,a

def sections(sc,col,root,arm):
 plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];objs={};meshes={};mats={};ds={}
 for o in sorted(col.all_objects,key=lambda o:o.name):
  matrix=conv(o.matrix_local)
  if o==plane:
   for i in range(3):matrix[i][3]='allowed camera-ray location'
  cp={k:conv(v)for k,v in o.items()if not(o==plane and k in ['camera_ray_depth_bias_world_cells','food_occlusion_policy_brief'])}
  objs[o.name]={'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixLocal':matrix,'parentInverse':conv(o.matrix_parent_inverse),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'groups':[(g.name,g.lock_weight)for g in o.vertex_groups],'mods':[{'name':m.name,'type':m.type,'props':props(m)}for m in o.modifiers],'constraints':[props(c)for c in o.constraints],'custom':cp}
  ds[o.name]=drivers(o)
  if o.type=='MESH':
   me=o.data;meshes[o.name]={'vertices':[[conv(v.co),[(g.group,g.weight)for g in v.groups]]for v in me.vertices],'edges':[list(e.vertices)for e in me.edges],'polygons':[(list(p.vertices),p.material_index,p.use_smooth)for p in me.polygons],'uv':{u.name:[conv(x.uv)for x in u.data]for u in me.uv_layers},'materials':[m.name if m else None for m in me.materials]}
   for m in me.materials:
    if m:mats[m.name]={'props':props(m),'nodes':nodes(m.node_tree)if m.use_nodes else None}
 acts={a.name:[{'path':f.data_path,'index':f.array_index,'keys':[(conv(k.co),k.interpolation,conv(k.handle_left),conv(k.handle_right),k.handle_left_type,k.handle_right_type)for k in f.keyframe_points],'modifiers':[props(m)for m in f.modifiers]}for f in native._fcurves(a)]for a in bpy.data.actions}
 bones=[{'name':x.name,'parent':x.parent.name if x.parent else None,'matrix':conv(x.matrix_local),'deform':x.use_deform}for x in arm.data.bones]
 images=[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file),'packedSHA':hashlib.sha256(bytes(i.packed_file.data)).hexdigest()if i.packed_file else None,'alphaMode':i.alpha_mode,'colorspace':i.colorspace_settings.name}for i in bpy.data.images if i.name not in ['Render Result','Viewer Node']]
 data={'objects':objs,'meshes':meshes,'materials':mats,'actions':acts,'bones':bones,'lights':{o.name:{'matrix':conv(o.matrix_world),'props':props(o.data)}for o in sc.objects if o.type=='LIGHT'},'camera':{'matrix':conv(sc.camera.matrix_world),'props':props(sc.camera.data)},'world':{'props':props(sc.world),'nodes':nodes(sc.world.node_tree)},'render':props(sc.render),'view':props(sc.view_settings),'images':images}
 return data,ds

def physical(arm,food,knife,col,dg):
 ae=arm.evaluated_get(dg);hands={}
 for side,sign in [('L',-1),('R',1)]:
  bone=ae.pose.bones['hand_'+side];p=Vector((sign*.267,-.025,.165));hands[side]=ae.matrix_world@bone.matrix@ae.data.bones['hand_'+side].matrix_local.inverted()@p
 contacts={'hands':{s:conv(v)for s,v in hands.items()},'feet':{s:conv(ae.matrix_world@ae.pose.bones['foot_'+s].head)for s in ['L','R']},'head':conv(ae.matrix_world@ae.pose.bones['head'].head),'foodRoot':conv(food.evaluated_get(dg).matrix_world),'utensilRoot':conv(knife.evaluated_get(dg).matrix_world)}
 H=hashlib.sha256();points=[];kpoints=[]
 for o in sorted(col.all_objects,key=lambda o:o.name):
  if o.type!='MESH'or '__image_plane'in o.name or o.hide_render:continue
  e=o.evaluated_get(dg);me=e.to_mesh();target=kpoints if o.parent==knife else points
  for v in me.vertices:
   p=e.matrix_world@v.co;H.update(struct.pack('<3f',*p));target.append(p)
  e.to_mesh_clear()
 def env(ps):return [[min(p[i]for p in ps)for i in range(3)],[max(p[i]for p in ps)for i in range(3)]]if ps else None
 return contacts,H.hexdigest(),env(points),env(kpoints),hands

def evaluate(sc,col,root,arm,asset,intermediate=False):
 food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane'];knife=bpy.data.objects[root.name+'__utensil'];cam=sc.camera
 ray=(cam.matrix_world.to_3x3()@Vector((0,0,1))).normalized();hc=Vector((ray.x,ray.y,0)).normalized();rows=[]
 angles=[-180,-179,-150,-135,-120,-100,-90.01,-90.001,-90,-89.999,-89.99,-60,-45,-30,0,30,45,60,89.99,89.999,90,90.001,90.01,100,120,135,150,179,180]
 todo=[('hold','S',0,ang)for ang in angles]if intermediate else [(clip,d,i,None)for clip in ['idle','work','hold','load']for d in ['S','E','N','W']for i in range(12)]
 for clip,d,i,ang in todo:
  native.apply_clip(asset,rig,clip,i+1,d,sc)
  if ang is not None:root.rotation_euler.z=math.radians(ang);sc.frame_set(sc.frame_current)
  bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pe=plane.evaluated_get(dg);fe=food.evaluated_get(dg)
  fw=root.matrix_world.to_3x3()@Vector((0,-1,0));fw.z=0;fw.normalize();f=max(-1,min(1,fw.dot(hc)));dep=.6-.15*max(0,-f)**2
  # Composed chain for authored hidden objects; direct evaluated matrix for every visible held/load frame.
  loc=plane.location.copy();rot=plane.rotation_euler.copy()
  for fc in plane.animation_data.drivers:
   raw=eval(fc.driver.expression,{'__builtins__':{},'sin':math.sin,'cos':math.cos,'max':max,'min':min},{'facing':float(root.rotation_euler.z)})
   if fc.data_path=='location':loc[fc.array_index]=raw
   elif fc.data_path=='rotation_euler':rot[fc.array_index]=raw
  composed=fe.matrix_world@plane.matrix_parent_inverse@Matrix.LocRotScale(loc,rot.to_quaternion(),plane.scale);actual=pe.matrix_world if not plane.hide_render else composed
  def screen(point):
   q=world_to_camera_view(sc,cam,point);return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
  lp=[v.co for v in plane.data.vertices]+[Vector((0,0,0))]
  projected=[screen(actual@v)for v in lp];comp=[screen(composed@v)for v in lp]
  off=actual.translation-fe.matrix_world.translation;nd=off.dot(ray);res=(off-nd*ray).length
  contacts,gh,bounds,kbounds,hands=physical(arm,food,knife,col,dg)
  expected=(hands['L']+hands['R'])/2+root.matrix_world.to_3x3()@Vector((0,0,.018));palm=(fe.matrix_world.translation-expected).length
  rows.append({'clip':clip,'facing':d,'index':i,'angleDegrees':ang,'f':f,'expectedDepth':dep,'nativeDepth':nd,'rayResidual':res,'projected':projected,'evaluatedComposedPixelError':max(abs(a-b)for p,q in zip(projected,comp)for a,b in zip(p,q)),'contacts':contacts,'geometrySHA256':gh,'bodyBounds':bounds,'knifeBounds':kbounds,'palmMidpointError':palm,'foodVisible':not plane.hide_render,'knifeVisible':[not o.hide_render for o in knife.children]})
 return rows

sc,col,root,arm,asset=setup(B/'source/round-01.blend');base_data,base_drivers=sections(sc,col,root,arm);base_rows=evaluate(sc,col,root,arm,asset);base_angles=evaluate(sc,col,root,arm,asset,True)
sc,col,root,arm,asset=setup(C/'rowan.blend');new_data,new_drivers=sections(sc,col,root,arm);new_rows=evaluate(sc,col,root,arm,asset);new_angles=evaluate(sc,col,root,arm,asset,True)
def diff(a,b,path='',out=None):
 if out is None:out=[]
 if type(a)!=type(b):out.append([path,a,b]);return out
 if isinstance(a,dict):
  for k in set(a)|set(b):
   if k not in a or k not in b:out.append([path+'/'+k,a.get(k),b.get(k)])
   elif a[k]!=b[k]:diff(a[k],b[k],path+'/'+k,out)
 elif isinstance(a,list):
  for i,(x,y)in enumerate(zip(a,b)):
   if x!=y:diff(x,y,path+'/'+str(i),out)
  if len(a)!=len(b):out.append([path+'/length',len(a),len(b)])
 else:out.append([path,a,b])
 return out
semantic_differences={k:diff(base_data[k],v)[:30]for k,v in new_data.items()if base_data[k]!=v}
sec={k:{'baselineSHA256':hashdata(base_data[k]),'candidateSHA256':hashdata(v),'equal':base_data[k]==v}for k,v in new_data.items()}
plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];plane_name=plane.name
other_drivers_equal={k:v for k,v in base_drivers.items()if k!=plane_name}=={k:v for k,v in new_drivers.items()if k!=plane_name}
yaw_equal=[d for d in base_drivers[plane_name]if d['path']=='rotation_euler']==[d for d in new_drivers[plane_name]if d['path']=='rotation_euler']
rows=[]
for a,z in zip(base_rows,new_rows):
 rows.append({'clip':z['clip'],'facing':z['facing'],'index':z['index'],'f':z['f'],'expectedDepth':z['expectedDepth'],'nativeDepth':z['nativeDepth'],'lawError':abs(z['nativeDepth']-z['expectedDepth']),'rayResidual':z['rayResidual'],'maxProjectionNativePixels':max(abs(v-w)for p,q in zip(a['projected'],z['projected'])for v,w in zip(p,q)),'contactsExact':a['contacts']==z['contacts'],'bodyKnifeEvaluatedGeometryExact':a['geometrySHA256']==z['geometrySHA256'],'bodyBoundsExact':a['bodyBounds']==z['bodyBounds'],'knifeBoundsExact':a['knifeBounds']==z['knifeBounds'],'visibilityExact':a['foodVisible']==z['foodVisible']and a['knifeVisible']==z['knifeVisible'],'foodVisible':z['foodVisible'],'palmMidpointError':z['palmMidpointError']})
angles=[]
for a,z in zip(base_angles,new_angles):angles.append({'angleDegrees':z['angleDegrees'],'f':z['f'],'expectedDepth':z['expectedDepth'],'nativeDepth':z['nativeDepth'],'lawError':abs(z['nativeDepth']-z['expectedDepth']),'rayResidual':z['rayResidual'],'maxProjectionNativePixels':max(abs(v-w)for p,q in zip(a['projected'],z['projected'])for v,w in zip(p,q))})
foreign=[]
for o in col.all_objects:
 if o.parent and o.parent not in col.all_objects[:]:foreign.append([o.name,'parent',o.parent.name])
 for m in o.modifiers:
  t=getattr(m,'object',None)
  if t and t not in col.all_objects[:]:foreign.append([o.name,'modifier',t.name])
 for c in o.constraints:
  t=getattr(c,'target',None)
  if t and t not in col.all_objects[:]:foreign.append([o.name,'constraint',t.name])
checks={'allSemanticSectionsEqualOutsidePlaneRayTranslation':all(x['equal']for x in sec.values()),'otherDriversExact':other_drivers_equal,'originalYawDriverExact':yaw_equal,'192Rows':len(rows)==192,'allContactsExact':all(r['contactsExact']for r in rows),'allEvaluatedBodyKnifeExact':all(r['bodyKnifeEvaluatedGeometryExact']and r['bodyBoundsExact']and r['knifeBoundsExact']for r in rows),'visibilityExact':all(r['visibilityExact']for r in rows),'projectionBelowPoint001':max(r['maxProjectionNativePixels']for r in rows)<.001,'lawErrorBelow1eMinus6':max(r['lawError']for r in rows+angles)<1e-6,'rayResidualBelow1eMinus6':max(r['rayResidual']for r in rows+angles)<1e-6,'noForeignDependencies':not foreign,'packedCanonical':len(new_data['images'])==1 and new_data['images'][0]['packedSHA']=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'}
output={'candidateSHA256':sha(C/'rowan.blend'),'baselineSHA256':sha(B/'source/round-01.blend'),'method':'Transient Blender session_uid values excluded; they are process-local IDs, not authored material/light/camera/world data. Hidden quads are composed from saved native driver expressions and unchanged parent inverse/basis, never stale hidden matrices. Fresh own script; saved sources reopened with scripts disabled, active scene/collection unhidden and depsgraph updated. Own semantic section hashes plus all192 evaluated body/knife world-vertex hashes, physical contacts, exact orthographic ray/projection and29 intermediate native angles. No source saved. Only reviews artifacts written.','semanticSections':sec,'semanticDifferences':semantic_differences,'planeDriversBefore':base_drivers[plane_name],'planeDriversAfter':new_drivers[plane_name],'images':new_data['images'],'foreignDependencies':foreign,'checks':checks,'allPassed':all(checks.values()),'rows':rows,'angles':angles}
(O/'native-replay.json').write_text(json.dumps(output,indent=2)+'\n');print('JUDGE_CHECKS',json.dumps(checks),flush=True)
# The candidate shader must survive a nonexistent external image path using its packed bytes.
import sys
if '--no-render' in sys.argv:raise SystemExit(0)
for im in bpy.data.images:
 if im.packed_file:im.filepath='/__rowan_judge_missing_external__/canonical-salmon.png';im.reload()
recaptures=[]
for clip,d,i in [('idle','S',0),('work','N',5),('hold','N',0),('hold','E',0),('hold','S',0),('hold','W',0),('load','N',5),('load','E',5),('load','W',5),('load','S',11)]:
 native.apply_clip(asset,rig,clip,i+1,d,sc);bpy.context.view_layer.update();p=O/f'{clip}-{d}-{i:02d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);recaptures.append({'path':p.name,'candidateFrame':f'frames/{p.name}','sha256':sha(p)})
(O/'recaptures.json').write_text(json.dumps({'source':str(C/'rowan.blend'),'sourceSHA256':sha(C/'rowan.blend'),'packedImagesReloadedFromMissingExternalPath':True,'renders':recaptures},indent=2)+'\n');print('JUDGE_RENDERED',len(recaptures),flush=True)
