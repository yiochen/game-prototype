"""Compact complete frozen-body/normal/pose audit and exact native captures for Noor v3."""
import bpy,json,sys,hashlib,math,time,argparse,numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02';sys.path.insert(0,str(P));import native_actions_round02 as NA
args=argparse.ArgumentParser();args.add_argument('--source',action='store_true');args.add_argument('--render',action='store_true');args.add_argument('--controls',action='store_true');args.add_argument('--shared-only',action='store_true');args.add_argument('--controls-only',action='store_true');args.add_argument('--control-source-food',action='store_true');opt=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
role='source' if opt.source else 'candidate';sc=bpy.data.scenes['Noor warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_noor.001'];root=bpy.data.objects['chef_noor__ground_root.001'];arm=bpy.data.objects['chef_noor__armature.001'];plane=next(o for o in coll.all_objects if '__image_plane' in o.name);rig=json.loads((P/'rig-round02.json').read_text());asset={'collection':coll,'root':root,'armature':arm}
brief=json.loads((B/'brief-v3-held-food-semantic-contact.json').read_text());recipe=json.loads((P/'recipe-round02.json').read_text());sourcefile=Path(bpy.data.filepath)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(v):
 if v is None or isinstance(v,(bool,int,float,str)):return v
 if isinstance(v,dict):return {str(k):plain(x) for k,x in v.items()}
 if isinstance(v,bpy.types.ID):return {'idType':v.bl_rna.identifier,'name':v.name}
 try:return [plain(x) for x in v]
 except TypeError:return str(v)
def jhash(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def harray(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def get(collection,prop,width,dtype=np.float32):
 a=np.empty(len(collection)*width,dtype=dtype);collection.foreach_get(prop,a);return a.reshape(-1,width) if width>1 else a
SKIP={'rna_type','name','name_full','users','use_fake_user','use_extra_user','is_embedded_data','is_library_indirect','is_missing','is_evaluated','is_runtime_data','session_uid','original','library','override_library','asset_data','preview','tag'}
def rna(v,skip=()):
 out={}
 for p in v.bl_rna.properties:
  k=p.identifier
  if k in SKIP or k in skip or p.is_readonly:continue
  try:
   x=getattr(v,k)
   if p.type in ['BOOLEAN','INT','FLOAT','STRING','ENUM']:out[k]=plain(x)
   elif p.type=='POINTER' and (isinstance(x,bpy.types.ID) or x is None):out[k]=plain(x)
  except Exception:pass
 return out
def anim(v):
 a=v.animation_data
 if not a:return None
 return {'action':a.action.name if a.action else None,'slot':getattr(a.action_slot,'identifier',None),'drivers':[{'path':f.data_path,'index':f.array_index,'driver':rna(f.driver),'variables':[{'rna':rna(x),'targets':[{'id':plain(t.id),'rna':rna(t)} for t in x.targets]} for x in f.driver.variables],'modifiers':[rna(m) for m in f.modifiers]} for f in a.drivers],'NLA':[{'rna':rna(t),'strips':[{'rna':rna(s),'action':plain(s.action)} for s in t.strips]} for t in a.nla_tracks]}
def mesh_record(me):
 me.update();norm=get(me.vertices,'normal',3);cn=get(me.corner_normals,'vector',3)
 return {'name':me.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'loops':len(me.loops),'vertexCoordinates':harray(get(me.vertices,'co',3)),'vertexNormals':harray(norm),'cornerNormals':harray(cn),'edges':harray(get(me.edges,'vertices',2,np.int32)),'loopVertexIndices':harray(get(me.loops,'vertex_index',1,np.int32)),'polygonLoopStart':harray(get(me.polygons,'loop_start',1,np.int32)),'polygonLoopTotal':harray(get(me.polygons,'loop_total',1,np.int32)),'polygonNormals':harray(get(me.polygons,'normal',3)),'smooth':harray(get(me.polygons,'use_smooth',1,np.bool_)),'materialIndices':harray(get(me.polygons,'material_index',1,np.int32)),'uv':{uv.name:harray(get(uv.data,'uv',2)) for uv in me.uv_layers},'materials':[m.name if m else None for m in me.materials],'hasCustomNormals':me.has_custom_normals,'rna':rna(me),'shapeKeys':plain(me.shape_keys)}
def matrecord(m):
 return {'rna':rna(m),'nodes':[{'name':n.name,'rna':rna(n),'inputs':{s.identifier:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'outputs':{s.identifier:plain(s.default_value) for s in n.outputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links] if m.use_nodes else []}
def static():
 meshes={};objects={}
 for o in coll.all_objects:
  objects[o.name]={'rna':rna(o),'data':plain(o.data),'parent':plain(o.parent),'customProperties':plain(dict(o.items())),'animation':anim(o),'constraints':[rna(x) for x in o.constraints],'modifiers':[rna(x) for x in o.modifiers]}
  if o.type=='MESH':
   meshes[o.name]=mesh_record(o.data);meshes[o.name]['weights']=jhash([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]);meshes[o.name]['groups']=[g.name for g in o.vertex_groups]
 armature={'rna':rna(arm.data),'bones':{b.name:{'rna':rna(b),'matrix':plain(b.matrix_local),'head':plain(b.head_local),'tail':plain(b.tail_local),'parent':b.parent.name if b.parent else None} for b in arm.data.bones},'poseChannels':{b.name:{'rna':rna(b),'constraints':[rna(c) for c in b.constraints]} for b in arm.pose.bones}}
 actions={}
 for name in sorted({x['action'] for c in rig['clips'].values() for x in c['actions']}):
  a=bpy.data.actions[name];actions[name]={'rna':rna(a),'slots':[rna(s) for s in a.slots],'curves':[{'path':f.data_path,'index':f.array_index,'rna':rna(f),'keys':[{'co':plain(k.co),'left':plain(k.handle_left),'right':plain(k.handle_right),'rna':rna(k)} for k in f.keyframe_points],'modifiers':[rna(m) for m in f.modifiers]} for f in NA._fcurves(a)]}
 materials={m.name:matrecord(m) for m in {m for o in coll.all_objects if o.type=='MESH' for m in o.data.materials if m}}
 return {'objects':objects,'meshes':meshes,'armature':armature,'actions':{k:jhash(v) for k,v in actions.items()},'actionCoverage':{name:{'fcurves':len(a['curves']),'keys':sum(len(f['keys']) for f in a['curves']),'slots':len(a['slots']),'coverage':'all fcurve/key coordinates, handles, interpolation/RNA, slots and modifiers included in actionsSHA256'} for name,a in actions.items()},'materials':materials,'camera':{'object':rna(sc.camera),'data':rna(sc.camera.data)},'lights':{o.name:{'object':rna(o),'data':rna(o.data)} for o in sc.objects if o.type=='LIGHT'},'world':{'rna':rna(sc.world),'nodes':matrecord(sc.world)},'scene':rna(sc),'render':rna(sc.render,skip=['filepath']),'imageSettings':rna(sc.render.image_settings),'cycles':rna(sc.cycles),'view':rna(sc.view_settings),'display':rna(sc.display_settings)}
def xy(v):
 q=world_to_camera_view(sc,sc.camera,Vector(v));return [q.x*384,(1-q.y)*640]
def image_record():
 node=next(n for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');im=node.image
 return {'name':im.name,'size':list(im.size),'path':im.filepath,'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest(),'alphaMode':im.alpha_mode,'colorSpace':im.colorspace_settings.name,'interpolation':node.interpolation,'extension':node.extension,'quad':[list(v.co) for v in plane.data.vertices],'faces':[list(p.vertices) for p in plane.data.polygons],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'rayFlags':{k:getattr(plane,k) for k in ['visible_camera','visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']}}
def semantic_local():
 refs=json.loads((P/'support-reference-round02.json').read_text())['references'];return [{'cutoff':r['cutoff'],**r['sourceLocal' if opt.source or opt.control_source_food else 'candidateLocal']} for r in refs]
if opt.control_source_food:
 assert opt.controls_only and not opt.source
 state=json.loads((P/'approved-food-state-round02.json').read_text());node=next(n for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');im=bpy.data.images.load(str(P/'dependencies-round02/source-control-dish-salmon.png'),check_existing=False);im.alpha_mode='STRAIGHT';im.colorspace_settings.name='sRGB';im.pack();node.image=im
 for v,co in zip(plane.data.vertices,state['quad']):v.co=co
 for l,uv in zip(plane.data.uv_layers.active.data,state['uv']):l.uv=uv
 plane.data.update();role='candidate-source-food-control'
local=semantic_local();shared=static();imrec=image_record();sharedpath=C/(role+'-shared.json');(sharedpath if not opt.controls_only else C/(role+'-control-shared.json')).write_text(json.dumps({'projectSHA256':sha(sourcefile),'role':role,'shared':shared,'food':imrec,'semanticLocal':local},sort_keys=True,separators=(',',':'),default=str))
if opt.shared_only:
 print('SHARED_ONLY',role,flush=True);raise SystemExit(0)
# Execute recorded GPU configuration; do not change scene settings.
if sc.render.engine=='CYCLES' and sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for dev in prefs.devices:dev.use=dev.type=='METAL'
physical=sorted([o for o in coll.all_objects if o.type=='MESH' and o!=plane],key=lambda o:o.name);phases=[];start=time.time();controls=[('idle','S',0),('work','S',0),('hold','S',0),('hold','N',0),('hold','N',5),('hold','N',11),('hold','E',5),('hold','W',5),('load','N',5),('load','E',5),('load','W',5),('load','S',11)]
if opt.controls_only:
 for clip,d,i in controls:
  NA.apply_clip(asset,rig,clip,i+1,d,sc)
  for take in ['a','b']:
   fp=C/'controls'/role/(f'{clip}-{d}-{i:03d}-{take}.png');fp.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(fp);bpy.ops.render.render(write_still=True,scene=sc.name)
 (C/(role+'-fresh-replay-settings.json')).write_text(json.dumps({'sourceProjectSHA256':sha(sourcefile),'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'denoising':sc.cycles.use_denoising,'controls':controls,'method':'fresh reopen exact saved source; original unedited scene settings; two same-input renders per representative hidden/active/N/E/W risk phase'},indent=2))
 print('CONTROLS_ONLY',role,len(controls),flush=True);raise SystemExit(0)
for clip in rig['clips']:
 for d in ['N','E','S','W']:
  for i in range(12):
   NA.apply_clip(asset,rig,clip,i+1,d,sc);visibility={o.name:{'render':o.hide_render,'viewport':o.hide_viewport,'hide':o.hide_get(),'rays':{k:getattr(o,k) for k in ['visible_camera','visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']}} for o in coll.all_objects}
   # Preserve actual visibility. Never expose/evaluate dormant food placement as if it were live.
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();geos={};palms={}
   for o in physical:
    e=o.evaluated_get(dg);me=e.to_mesh();co=get(me.vertices,'co',3);vn=get(me.vertices,'normal',3);cn=get(me.corner_normals,'vector',3);pn=get(me.polygons,'normal',3);matrix=np.array(e.matrix_world,dtype=np.float64);world=co@matrix[:3,:3].T+matrix[:3,3]
    nm=np.linalg.inv(matrix[:3,:3]).T;wn=vn@nm.T;norm=np.linalg.norm(wn,axis=1);wn=wn/np.maximum(norm[:,None],1e-30)
    geos[o.name]={'vertices':len(me.vertices),'polygons':len(me.polygons),'loops':len(me.loops),'localCoordinates':harray(co),'worldCoordinates':harray(world),'vertexNormals':harray(vn),'worldVertexNormals':harray(wn),'cornerNormals':harray(cn),'polygonNormals':harray(pn),'matrix':plain(e.matrix_world),'bounds':[[float(world[:,ax].min()),float(world[:,ax].max())] for ax in range(3)],'finite':bool(np.isfinite(co).all() and np.isfinite(vn).all() and np.isfinite(cn).all())}
    if '__palm_' in o.name:palms[o.name.split('__palm_')[1].split('.')[0]]=world.mean(0).tolist()
    e.to_mesh_clear()
   ae=arm.evaluated_get(dg);pose={b.name:plain(ae.matrix_world@b.matrix) for b in ae.pose.bones};pe=plane.evaluated_get(dg);pm=pe.matrix_world.copy();support=[]
   for loc in (local if not plane.hide_render else []):
    w=pm@Vector(loc['pointLocal']);pointpx=xy(w);mid=((np.array(palms['L'])+np.array(palms['R']))*.5).tolist();rel={}
    for name,palm in {**palms,'midpoint':mid}.items():rel[name]={'world':palm,'projected':xy(palm),'rimMinusPalmWorld':(np.array(w)-palm).tolist(),'rimMinusPalmNativePixels':(np.array(pointpx)-xy(palm)).tolist()}
    support.append({'cutoff':loc['cutoff'],'local':loc['pointLocal'],'world':list(w),'projected':pointpx,'occupiedWidthWorld':loc['occupiedWidthLocal']*(pm.col[0].xyz.length),'occupiedWidthNativePixels':loc['occupiedWidthLocal']*(pm.col[0].xyz.length)*256,'palmRelations':rel})
   transforms={o.name:{'world':plain(o.evaluated_get(dg).matrix_world),'localLocation':plain(o.location),'localRotation':plain(o.rotation_euler),'localScale':plain(o.scale),'visibility':visibility[o.name]} for o in coll.all_objects if o!=plane or not plane.hide_render}
   # The hidden plane's animation action and complete drivers are frozen in shared data;
   # dormant driven location/yaw/matrices are deliberately not asserted as active placement.
   if plane.hide_render:transforms[plane.name]={'hidden':True,'visibility':visibility[plane.name],'action':plane.animation_data.action.name if plane.animation_data.action and plane.animation_data else None,'stableLocalZ':plane.location.z,'stableRotationX':plane.rotation_euler.x,'drivers':anim(plane)['drivers']}
   row={'clip':clip,'direction':d,'index':i,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':plain(root.matrix_world),'cameraMatrix':plain(sc.camera.matrix_world),'rootPixel':xy((0,0,0)),'physicalMeshes':geos,'pose':jhash(pose),'nativeTransforms':jhash(transforms),'foodChannels':{name:v for name,v in transforms.items() if '__held_' in name},'semanticSupport':support,'sourceProjectSHA256':sha(sourcefile)}
   if opt.render:
    fp=C/'frames'/(clip+'-'+d)/(f'{i:03d}.png');fp.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(fp);bpy.ops.render.render(write_still=True,scene=sc.name);row['path']=str(fp.relative_to(B));row['sha256']=sha(fp)
   if opt.controls and (clip,d,i) in controls:
    for take in ['a','b']:
     fp=C/'controls'/role/(f'{clip}-{d}-{i:03d}-{take}.png');fp.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(fp);bpy.ops.render.render(write_still=True,scene=sc.name)
   phases.append(row);(C/(role+'-progress.json')).write_text(json.dumps({'done':len(phases),'total':192,'current':[clip,d,i],'seconds':time.time()-start}));print(role,len(phases),clip,d,i,flush=True)
(C/(role+'-phases.json')).write_text(json.dumps(phases,separators=(',',':')))
settings={'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'denoise':sc.cycles.use_denoising,'denoiser':sc.cycles.denoiser,'adaptiveSampling':sc.cycles.use_adaptive_sampling,'adaptiveThreshold':sc.cycles.adaptive_threshold,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'devices':[{'name':dev.name,'type':dev.type,'use':dev.use} for dev in bpy.context.preferences.addons['cycles'].preferences.devices]}
(C/(role+'-capture-settings.json')).write_text(json.dumps({'sourceProject':str(sourcefile),'sourceProjectSHA256':sha(sourcefile),'settings':settings,'physicalObjectCount':len(physical),'phaseCount':len(phases),'controls':controls if opt.controls else [],'representation':'chef/knife physical native meshes; exact packed2D food on original source holder; original all-ray Emission1 behavior retained'},indent=2))
print('COMPLETE',role,len(phases),flush=True)
