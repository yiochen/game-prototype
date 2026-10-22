import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-cover');R=O/'reviews/round-02-independent';S=O/'source/round-02';C=O/'candidates/round-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sc=bpy.context.scene;root=bpy.data.objects['dock-cover__root'];cloth=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'];keys=cloth.data.shape_keys;rig=json.loads((S/'rig.json').read_text());expected=json.loads((C/'native-envelope-measurements.json').read_text());ex={(v['clip'],v['direction'],v['frame']):v for v in expected['samples']}
objects=[o for o in sc.objects if o.type=='MESH' and not o.hide_render and o.visible_camera];mats={m for o in objects for m in o.data.materials if m}
def pose(clip,d,f):
 keys.animation_data.action=None
 for key in keys.key_blocks:key.value=0
 action=bpy.data.actions[rig['clips'][clip]['action']];keys.animation_data.action=action
 if action.slots:keys.animation_data.action_slot=action.slots[0]
 root.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d];sc.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
def geom():
 dg=bpy.context.evaluated_depsgraph_get();pts=[];rec=[]
 for o in objects:
  eo=o.evaluated_get(dg);me=eo.to_mesh();p=[eo.matrix_world@v.co for v in me.vertices];pts+=p;rec.append({'name':o.name,'bounds':[[min(v[i] for v in p)for i in range(3)],[max(v[i]for v in p)for i in range(3)]],'vertexHash':hashlib.sha256(b''.join(__import__('struct').pack('fff',*v) for v in p)).hexdigest()});eo.to_mesh_clear()
 return [[min(v[i]for v in pts)for i in range(3)],[max(v[i]for v in pts)for i in range(3)]],rec
pose('covered','S',1)
def px(v):
 p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
b=px((0,0,0));cal={'root':b,'unitX':[x-y for x,y in zip(px((1,0,0)),b)],'unitDepth':[x-y for x,y in zip(px((0,-1,0)),b)],'unitHeight':[x-y for x,y in zip(px((0,0,1)),b)]}
r={'sourcePath':str(S/'cover.blend'),'sourceSHA256':sha(S/'cover.blend'),'blender':bpy.app.version_string,'filterSize':sc.render.filter_size,'render':{'engine':sc.render.engine,'frame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'transparent':sc.render.film_transparent},'camera':{'matrix':[list(v)for v in sc.camera.matrix_world],'orthographicScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'calibration':cal},'root':{'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale)},'externalLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images if i.source=='FILE'],'visibleObjects':[{'name':o.name,'vertices':len(o.data.vertices),'uvLayers':[u.name for u in o.data.uv_layers],'modifiers':[{'name':m.name,'type':m.type}for m in o.modifiers],'constraints':[x.type for x in o.constraints],'materials':[m.name for m in o.data.materials if m]}for o in objects],'materials':[{'name':m.name,'nodes':[{'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'alpha':[(x.name,x.default_value,x.is_linked)for x in n.inputs if x.name=='Alpha' and hasattr(x,'default_value')]}for n in m.node_tree.nodes],'animation':bool(m.node_tree.animation_data and m.node_tree.animation_data.action)}for m in mats],'lights':[{'name':o.name,'energy':o.data.energy,'location':list(o.location),'size':o.data.size,'color':list(o.data.color)}for o in sc.objects if o.type=='LIGHT' and not o.hide_render],'actions':[],'samples':[],'closure':{},'replays':[]}
for clip in ['covered','uncover']:
 a=bpy.data.actions[rig['clips'][clip]['action']];curves=[fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves];r['actions'].append({'clip':clip,'name':a.name,'paths':sorted(set(fc.data_path for fc in curves)),'interpolations':sorted(set(p.interpolation for fc in curves for p in fc.keyframe_points)),'keyRanges':[[min(p.co.x for p in fc.keyframe_points),max(p.co.x for p in fc.keyframe_points)]for fc in curves]})
 for d in 'NESW':
  for f in [*range(1,14),*[v+.5 for v in range(1,13)],16]:
   pose(clip,d,f);bounds,rec=geom();e=ex[(clip,d,f)]['bounds'];error=max(abs(bounds[j][k]-e[j][k])for j in range(2)for k in range(3));assert error<1e-6,(clip,d,f,error);r['samples'].append({'clip':clip,'direction':d,'frame':f,'bounds':bounds,'boundEvidenceMaximumError':error})
 for f in ([1,13]if clip=='covered'else[12,16]):
  pose(clip,'S',f);bounds,rec=geom();r['closure'].setdefault(clip,[]).append({'frame':f,'objectHashes':{o['name']:o['vertexHash']for o in rec}})
for clip,d,index in [('covered','S',0),('uncover','E',11)]:
 pose(clip,d,index+1);p=R/'native-replay'/f'{clip}-{d}-{index:03d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);r['replays'].append({'path':str(p.relative_to(O)),'sha256':sha(p),'reference':f'candidates/round-02/frames/{clip}-{d}/{index:03d}.png'})
r['closureEqual']={c:rs[0]['objectHashes']==rs[1]['objectHashes']for c,rs in r['closure'].items()};r['maximumEnvelope']=[[min(s['bounds'][0][i]for s in r['samples'])for i in range(3)],[max(s['bounds'][1][i]for s in r['samples'])for i in range(3)]]
(R/'native-independent.json').write_text(json.dumps(r,indent=2)+'\n');print('INDEPENDENT NATIVE',len(r['samples']),r['maximumEnvelope'],r['closureEqual'])
