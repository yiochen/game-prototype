"""Portable, read-only source-only audit. Run blender -b --python this_file.
Arrays are held in memory only; output is hashes/counts/maxima, never vertex dumps.
"""
import bpy,json,sys,hashlib,math,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-03';sys.path.insert(0,str(P));import native_actions_round03 as native
R=json.loads((P/'rig-round03.json').read_text());FOOD='chef_lena__ground_root.002__held_dish-salmon__image_plane'
sha=lambda b:hashlib.sha256(b).hexdigest()
def jhash(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def arr(items,attr,n,dtype=np.float32):
 a=np.empty(len(items)*n,dtype=dtype);items.foreach_get(attr,a);return a.reshape((-1,n)) if n>1 else a

def simple(x):
 if x is None or isinstance(x,(str,bool,int,float)):return x
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 try:return [simple(v) for v in x]
 except:return str(x)
def rna(x):
 out={}
 for p in x.bl_rna.properties:
  k=p.identifier
  if k=='rna_type' or p.is_readonly or p.type=='COLLECTION':continue
  try:
   val=getattr(x,k)
   if p.type=='POINTER' and val is not None and not isinstance(val,bpy.types.ID):out[k]=rna(val)
   else:out[k]=simple(val)
  except (TypeError,ValueError,AttributeError):pass
 return out

def tree(t,ignore_image=False):
 return {'nodes':[{'name':n.name,'rna':{k:v for k,v in rna(n).items() if not(ignore_image and k=='image')},'inputs':[(s.identifier,s.name,simple(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,s.name,simple(s.default_value)) for s in n.outputs if hasattr(s,'default_value')]} for n in sorted(t.nodes,key=lambda n:n.name)],'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links)}
def drivers(o):
 return [{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'boneTarget':t.bone_target,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in f.driver.variables]} for f in (o.animation_data.drivers if o.animation_data else [])]
def arrayhash(a):return sha(a.tobytes())
def topology(me):return {'counts':[len(me.vertices),len(me.edges),len(me.polygons),len(me.loops)],'edgeVertices':arrayhash(arr(me.edges,'vertices',2,np.int32)),'loopVertices':arrayhash(arr(me.loops,'vertex_index',1,np.int32)),'polyStarts':arrayhash(arr(me.polygons,'loop_start',1,np.int32)),'polyTotals':arrayhash(arr(me.polygons,'loop_total',1,np.int32)),'polyMaterial':arrayhash(arr(me.polygons,'material_index',1,np.int32)),'smooth':arrayhash(arr(me.polygons,'use_smooth',1,np.bool_))}
def select(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;co=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];asset={'collection':co,'root':root,'armature':arm};native.apply_clip(asset,R,'idle',1,'S',sc);return sc,co,root,arm,asset

def semantic(sc,co,root,arm):
 objects={};materials={};foodmat=bpy.data.objects[FOOD].data.materials[0]
 for o in sorted(sc.objects,key=lambda o:o.name):
  d={'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'basis':simple(o.matrix_basis),'parentInverse':simple(o.matrix_parent_inverse),'rotationMode':o.rotation_mode,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'drivers':drivers(o),'constraints':[rna(c) for c in o.constraints],'custom':{k:simple(o[k]) for k in o.keys()}}
  if o.type=='MESH':
   me=o.data;d['dataRNA']=rna(me);d['dataCustom']={k:simple(me[k]) for k in me.keys()};d['topology']=topology(me);d['coordinates']=arrayhash(arr(me.vertices,'co',3));d['normals']=arrayhash(arr(me.vertices,'normal',3));d['groups']=[g.name for g in o.vertex_groups];d['weights']=jhash([[(g.group,g.weight) for g in v.groups] for v in me.vertices]);d['modifiers']=[rna(m) for m in o.modifiers];d['materials']=[m.name for m in me.materials];d['uv']={uv.name:arrayhash(arr(uv.data,'uv',2)) for uv in me.uv_layers};d['shapeKeys']={k.name:{'value':k.value,'coordinates':arrayhash(arr(k.data,'co',3)),'relative':k.relative_key.name,'interpolation':k.interpolation} for k in me.shape_keys.key_blocks} if me.shape_keys else None
   for m in me.materials:
    if m:materials[m.name]={'rna':rna(m),'tree':tree(m.node_tree,ignore_image=m==foodmat) if m.use_nodes else None}
  elif o.type=='ARMATURE':d['dataRNA']=rna(arm.data);d['dataCustom']={k:simple(arm.data[k]) for k in arm.data.keys()};d['bones']={b.name:{'matrix':simple(b.matrix_local),'head':simple(b.head_local),'tail':simple(b.tail_local),'parent':b.parent.name if b.parent else None,'deform':b.use_deform,'rna':rna(b)} for b in arm.data.bones}
  elif o.type in ('LIGHT','CAMERA'):d['data']=rna(o.data)
  objects[o.name]=d
 actions={}
 for config in R['clips'].values():
  for target in config['actions']:
   ac=bpy.data.actions[target['action']];actions[ac.name]=[{'dataPath':fc.data_path,'index':fc.array_index,'extrapolation':fc.extrapolation,'keys':[(simple(k.co),k.interpolation,k.easing,simple(k.handle_left),simple(k.handle_right),k.handle_left_type,k.handle_right_type) for k in fc.keyframe_points],'modifiers':[rna(m) for m in fc.modifiers]} for fc in native._fcurves(ac)]
 return {'objects':objects,'materials':materials,'actions':actions,'world':{'rna':rna(sc.world),'tree':tree(sc.world.node_tree)},'cameraObject':sc.camera.name,'render':rna(sc.render),'cycles':rna(sc.cycles),'view':rna(sc.view_settings),'compositor':tree(sc.compositing_node_group) if getattr(sc,'compositing_node_group',None) else None}

def capture(sc,co,root,arm):
 props=[o for o in co.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name];visibility={o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in props}
 for o in props:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();meshes={}
 for o in sorted(co.all_objects,key=lambda o:o.name):
  if o.type!='MESH' or o.name==FOOD:continue
  e=o.evaluated_get(dg);me=e.to_mesh();local=arr(me.vertices,'co',3);normals=arr(me.vertices,'normal',3);mat=np.array(e.matrix_world,dtype=np.float32);world=local@mat[:3,:3].T+mat[:3,3];wn=normals@np.linalg.inv(mat[:3,:3]);length=np.linalg.norm(wn,axis=1,keepdims=True);wn=np.divide(wn,length,out=np.zeros_like(wn),where=length!=0)
  meshes[o.name]={'local':local,'world':world,'normal':normals,'worldNormal':wn,'topology':topology(me),'matrix':mat};e.to_mesh_clear()
 ae=arm.evaluated_get(dg);pose=np.array([ae.matrix_world@b.matrix for b in ae.pose.bones],dtype=np.float32);boneNames=[b.name for b in ae.pose.bones]
 plane=bpy.data.objects[FOOD];e=plane.evaluated_get(dg);corners=[e.matrix_world@v.co for v in e.data.vertices];px=[]
 for q in corners:
  n=world_to_camera_view(sc,sc.camera,q);px.append([n.x*384,(1-n.y)*640])
 food={'worldCorners':[list(v) for v in corners],'pixelCorners':px,'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'matrix':simple(e.matrix_world),'visible':not visibility[FOOD][0] and not visibility[plane.parent.name][0],'visibility':visibility,'rootMatrix':simple(root.matrix_world),'boneNames':boneNames,'boneDeterminants':[float((ae.matrix_world@b.matrix).determinant()) for b in ae.pose.bones]}
 for o in props:o.hide_render,o.hide_viewport,h=visibility[o.name];o.hide_set(h)
 bpy.context.view_layer.update()
 return meshes,pose,food

def summarymesh(d):return {'counts':d['topology']['counts'],'topologySHA256':jhash(d['topology']),**{k+'SHA256':arrayhash(d[k]) for k in ['local','world','normal','worldNormal','matrix']}}
start=time.time();sourcepath=P/'round-02.blend';candidatepath=P/'round-03.blend';sourceSHA=sha(sourcepath.read_bytes());candidateSHA=sha(candidatepath.read_bytes());assert sourceSHA=='4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073'
sc,co,root,arm,asset=select(sourcepath);sourceSemantic=semantic(sc,co,root,arm);baseline={};sourceLedger=[]
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   native.apply_clip(asset,R,clip,i+1,d,sc);m,p,f=capture(sc,co,root,arm);baseline[(clip,d,i)]=(m,p,f);sourceLedger.append({'clip':clip,'direction':d,'index':i,'meshes':{n:summarymesh(v) for n,v in m.items()},'poseSHA256':arrayhash(p),'food':f})
 print('SOURCE',clip,len(baseline),flush=True)
sc,co,root,arm,asset=select(candidatepath);candidateSemantic=semantic(sc,co,root,arm);semanticChanges=[]
for section in sourceSemantic:
 if section in ('objects','materials','actions'):
  for n in sourceSemantic[section]:
   a=sourceSemantic[section][n];b=candidateSemantic[section][n]
   if jhash(a)!=jhash(b):semanticChanges.append({'section':section,'name':n,'changedFields':[k for k in a if jhash(a[k])!=jhash(b[k])] if isinstance(a,dict) else ['fcurves'],'sourceSHA256':jhash(a),'candidateSHA256':jhash(b)})
 elif jhash(sourceSemantic[section])!=jhash(candidateSemantic[section]):semanticChanges.append({'section':section,'sourceSHA256':jhash(sourceSemantic[section]),'candidateSHA256':jhash(candidateSemantic[section])})
rows=[];mismatches=[];maxima={k:0. for k in ['local','world','normal','worldNormal','matrix','pose','bottomWorld','bottomPixels','rootMatrix']};boneDet=[]
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   native.apply_clip(asset,R,clip,i+1,d,sc);m,p,f=capture(sc,co,root,arm);a,ap,af=baseline.pop((clip,d,i));details={}
   for n,v in m.items():
    errs={k:float(np.max(np.abs(v[k].astype(np.float64)-a[n][k].astype(np.float64)))) for k in ['local','world','normal','worldNormal','matrix']};changed={k:int(np.count_nonzero(v[k]!=a[n][k])) for k in errs};details[n]={**summarymesh(v),'deltaMax':errs,'unequalScalarCounts':changed,'sourceHashesIdentical':summarymesh(v)==summarymesh(a[n])}
    for k,z in errs.items():maxima[k]=max(maxima[k],z)
    if not details[n]['sourceHashesIdentical']:mismatches.append([clip,d,i,n])
   err=float(np.max(np.abs(p.astype(np.float64)-ap.astype(np.float64))));bw=float(np.max(np.abs(np.array(f['worldCorners'][:2])-np.array(af['worldCorners'][:2]))));bp=float(np.max(np.abs(np.array(f['pixelCorners'][:2])-np.array(af['pixelCorners'][:2]))));rm=float(np.max(np.abs(np.array(f['rootMatrix'])-np.array(af['rootMatrix']))));maxima['pose']=max(maxima['pose'],err);maxima['bottomWorld']=max(maxima['bottomWorld'],bw);maxima['bottomPixels']=max(maxima['bottomPixels'],bp);maxima['rootMatrix']=max(maxima['rootMatrix'],rm);boneDet.extend(f['boneDeterminants'])
   rows.append({'clip':clip,'direction':d,'index':i,'meshes':details,'poseSHA256':arrayhash(p),'sourcePoseSHA256':arrayhash(ap),'poseMaxDifference':err,'bottomWorldMaxDifference':bw,'bottomPixelMaxDifference':bp,'visibilityIdentical':f['visibility']==af['visibility'],'food':f});
 print('CANDIDATE',clip,len(rows),flush=True)
# Exact food closure and data changes, independent of rendered appearance.
plane=bpy.data.objects[FOOD];image=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');external=C/'resources/dish-salmon.png';pixels=arr(image.pixels,'',1) if False else np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
food={'image':{'name':image.name,'size':list(image.size),'packedSHA256':sha(image.packed_file.data),'externalSHA256':sha(external.read_bytes()),'blenderDecodedFloatRGBA_SHA256':arrayhash(pixels),'alphaMode':image.alpha_mode,'colorspace':image.colorspace_settings.name,'filepath':image.filepath},'vertices':[list(v.co) for v in plane.data.vertices],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'drivers':drivers(plane),'localWidth':plane.data.vertices[1].co.x-plane.data.vertices[0].co.x,'worldWidth':(plane.data.vertices[1].co.x-plane.data.vertices[0].co.x)*root.scale.x,'worldHeight':plane.data.vertices[2].co.y*root.scale.x,'cameraRayOffsetWorld':.6,'localZOffset':plane.location.z,'foodShaderExcludingImageSame':sourceSemantic['materials'][plane.data.materials[0].name]==candidateSemantic['materials'][plane.data.materials[0].name],'driversSame':sourceSemantic['objects'][FOOD]['drivers']==candidateSemantic['objects'][FOOD]['drivers']}
assert food['image']['packedSHA256']==food['image']['externalSHA256']=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
report={'schemaVersion':1,'source':'source/round-02.blend','sourceSHA256':sourceSHA,'candidate':'source/round-03.blend','candidateSHA256':candidateSHA,'script':'source/semantic_audit_round03.py','scriptSHA256':sha(Path(__file__).read_bytes()),'frames':192,'physicalMeshes':len(rows[0]['meshes']),'physicalMeshFrameComparisons':sum(len(x['meshes']) for x in rows),'hashPolicy':'IEEE754 float32 bytes from evaluated Blender coordinates/normals, exact integer topology; no rounding. World transforms evaluated identically by NumPy float32. Pose matrices exact Blender float32. In-memory arrays discarded after comparison, no raw vertex JSON.','sourceSemanticHashes':{s:({n:jhash(v) for n,v in x.items()} if s in ('objects','materials','actions') else jhash(x)) for s,x in sourceSemantic.items()},'candidateSemanticHashes':{s:({n:jhash(v) for n,v in x.items()} if s in ('objects','materials','actions') else jhash(x)) for s,x in candidateSemantic.items()},'changedNativeSemanticRecords':semanticChanges,'allowedFoodProvenanceChanges':{'root':['held_food_source'],'plane':['source_image','source_sha256','fixed_alpha_rectangle','representation'],'imageBinding':{'from':'dish-salmon.png (1254x1254)','to':'Lena canonical salmon round03 (731x505)','oldImageRemovedIfUnused':True},'physicalSemanticFieldsIdenticalExceptListedFoodRecords':all(x.get('section')=='objects' and x.get('name') in [FOOD,'chef_lena__ground_root.002'] for x in semanticChanges)},'physicalMismatchRows':mismatches,'maximumAbsoluteDifferences':maxima,'food':food,'boneDeterminantRange':[min(boneDet),max(boneDet)],'hiddenSampling':'Food/utensil temporarily exposed for current evaluated matrices/geometry, exact render and viewport states restored before render.','allVisibilityIdentical':all(r['visibilityIdentical'] for r in rows),'elapsedSeconds':time.time()-start,'rows':rows,'sourceRows':sourceLedger}
report['physicalExact']=not mismatches and all(maxima[k]==0 for k in ['local','world','normal','worldNormal','matrix','pose','rootMatrix']);report['bottomAnchorExact']=maxima['bottomWorld']==maxima['bottomPixels']==0
(C/'semantic-parity.json').write_text(json.dumps(report,separators=(',',':')));print('AUDIT',json.dumps({k:v for k,v in report.items() if k in ['physicalExact','bottomAnchorExact','maximumAbsoluteDifferences','changedNativeSemanticRecords','allVisibilityIdentical','elapsedSeconds']}),flush=True)
