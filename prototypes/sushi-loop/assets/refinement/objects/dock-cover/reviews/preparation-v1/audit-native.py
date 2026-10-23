import bpy,json,hashlib,pathlib,math,sys,importlib.util
from mathutils import Vector
BASE=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OBJ=BASE/'prototypes/sushi-loop/assets/refinement/objects/dock-cover'; OUT=OBJ/'reviews/preparation-v1'; MOD=OUT/'capture-code'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,str(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
actions=load('cover_judge_native_actions',MOD/'native_actions.py'); runtime=load('cover_judge_capture_runtime',MOD/'capture_runtime.py')
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc; bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());asset=json.loads((OBJ/'inputs/source-assetRecord.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));asset.update(root=root,collection=col)
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
camera=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),2,asset.get('camera_elevation_degrees'))
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.image_settings.compression=15;sc.render.use_persistent_data=True
if hasattr(sc,'eevee') and hasattr(sc.eevee,'taa_render_samples'):sc.eevee.taa_render_samples=16
objs=[o for o in col.all_objects if o.type=='MESH'];mats={m for o in objs for m in o.data.materials if m}
def sampled():
 dg=bpy.context.evaluated_depsgraph_get();allpts=[];rec=[]
 for o in objs:
  eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];allpts+=pts
  rec.append({'name':o.name,'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'hideRender':o.hide_render,'matrix':[list(a) for a in eo.matrix_world],'bounds':[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]], 'vertexSHA256':hashlib.sha256(json.dumps([[round(v,7) for v in p] for p in pts]).encode()).hexdigest()})
  eo.to_mesh_clear()
 return {'bounds':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]],'objects':rec,'materials':[{'name':m.name,'alpha':[(n.name,s.name,s.default_value) for n in m.node_tree.nodes for s in n.inputs if s.name=='Alpha' and hasattr(s,'default_value')]} for m in mats]}
audit={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'rigSHA256':hashlib.sha256((OBJ/'inputs/source-rig.json').read_bytes()).hexdigest(),'camera':camera,'configuredCamera':{'name':sc.camera.name,'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'matrix':[list(r) for r in sc.camera.matrix_world]},'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'transparent':sc.render.film_transparent,'fps':sc.render.fps,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'compositorNodes':[{'name':n.name,'type':n.type} for n in getattr(sc,'compositing_node_group',None).nodes] if getattr(sc,'compositing_node_group',None) else []},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':list(o.location),'size':o.data.size} for o in sc.objects if o.type=='LIGHT' and not o.hide_render],'phases':[],'inbetweens':[],'actions':[]}
for clip,data in rig['clips'].items():
 for target in data['actions']:
  a=bpy.data.actions[target['action']]; curves=list(actions._fcurves(a)); audit['actions'].append({'clip':clip,'owner':target['ownerName'],'action':a.name,'curves':[{'dataPath':c.data_path,'index':c.array_index,'keys':[[k.co[0],k.co[1],k.interpolation] for k in c.keyframe_points]} for c in curves]})
 for d in ['N','E','S','W']:
  for i in range(12):
   actions.apply_clip(asset,rig,clip,i+1,d,sc);r=sampled();r.update(clip=clip,direction=d,index=i,frame=i+1)
   p=OUT/'native-frames'/f'{clip}-{d}'/f'{i:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);r['render']=str(p.relative_to(OBJ/'reviews'));r['renderSHA256']=hashlib.sha256(p.read_bytes()).hexdigest();audit['phases'].append(r)
   (OUT/'native-audit-progress.json').write_text(json.dumps({'completed':len(audit['phases']),'total':96})+'\n')
 for f in [1,1.5,3.5,6.5,9.5,11.5,12,12.5,13]:
  actions.apply_clip(asset,rig,clip,1,'S',sc);sc.frame_set(math.floor(f),subframe=f%1);sc.view_layers[0].update();r=sampled();r.update(clip=clip,frame=f,direction='S');audit['inbetweens'].append(r)
(OUT/'native-phase-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('DONE ALL 96 NATIVE FRAMES')
