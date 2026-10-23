import sys,json,math,hashlib,time
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-01';rig=json.loads((O/'source/round-01-records/rig.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def mat(m):return [list(r)for r in m]
def bounds(v):return {'min':[min(p[i]for p in v)for i in range(3)],'max':[max(p[i]for p in v)for i in range(3)]}
def plain(v):
 try:return list(v)
 except:return v
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=bpy.data.collections['S33_CFX_attack-reef-fragments.001'];root=bpy.data.objects['attack-reef-fragments__ground_root.001'];cam=sc.camera
# Unhide the actual selected ancestry; leave source camera/material/light bytes alone.
def layer(l):
 l.exclude=False;l.hide_viewport=False;l.collection.hide_render=False;l.collection.hide_viewport=False
 for c in l.children:layer(c)
layer(sc.view_layers[0].layer_collection)
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def px(v):
 q=world_to_camera_view(sc,cam,v);return(q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y,q.z)
materials=[]
for m in sorted({s.material for o in col.all_objects for s in o.material_slots if s.material},key=lambda m:m.name):
 materials.append({'name':m.name,'properties':dict(m.items()),'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:plain(s.default_value)for s in n.inputs if hasattr(s,'default_value')},'images':n.image.filepath if hasattr(n,'image') and n.image else None}for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name]for l in m.node_tree.links]})
inventory={'sourceSHA256':sha(Path(bpy.data.filepath)),'blender':bpy.app.version_string,'scene':sc.name,'collections':[c.name for c in sc.collection.children],'ownedCollection':col.name,'root':{'name':root.name,'matrix':mat(root.matrix_world),'parent':root.parent.name if root.parent else None,'constraints':[x.name for x in root.constraints]},'sceneObjects':[{'name':o.name,'type':o.type,'collections':[c.name for c in o.users_collection]}for o in sc.objects],'meshes':[],'materials':materials,'actions':[{'name':a.name,'slots':[s.identifier for s in a.slots],'frameRange':list(a.frame_range),'fakeUser':a.use_fake_user}for a in bpy.data.actions],'camera':{'name':cam.name,'matrix':mat(cam.matrix_world),'projection':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'rootProjection':px(Vector((0,0,0))),'unitX':px(Vector((1,0,0))),'unitDepth':px(Vector((0,-1,0))),'unitHeight':px(Vector((0,0,1)))},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'transparent':sc.render.film_transparent,'dither':sc.render.dither_intensity,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filterSize':sc.render.filter_size,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None},'lights':[{'name':o.name,'matrix':mat(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shadow':getattr(o.data,'use_shadow',None)}for o in sc.objects if o.type=='LIGHT'],'worldNodes':[{'name':n.name,'type':n.type,'inputs':{s.name:plain(s.default_value)for s in n.inputs if hasattr(s,'default_value')}}for n in sc.world.node_tree.nodes]}
for o in col.all_objects:
 if o.type!='MESH':continue
 edges={tuple(sorted(e.vertices)):0 for e in o.data.edges}
 for f in o.data.polygons:
  for e in f.edge_keys:edges[tuple(sorted(e))]+=1
 inventory['meshes'].append({'name':o.name,'parent':o.parent.name if o.parent else None,'rawCounts':[len(o.data.vertices),len(o.data.polygons)],'nonmanifoldRawEdges':sum(v!=2 for v in edges.values()),'modifiers':[{'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None),'render':m.show_render,'viewport':m.show_viewport}for m in o.modifiers],'shapeKeys':list(o.data.shape_keys.key_blocks.keys())if o.data.shape_keys else [],'constraints':[c.name for c in o.constraints],'scale':list(o.scale),'materialSlots':[s.material.name if s.material else None for s in o.material_slots]})
dump(P/'native/saved-source-inventory.json',inventory)
def apply(clip,direction,frame):
 for o in col.all_objects:
  if o.animation_data:
   o.animation_data.action=None
   for tr in o.animation_data.nla_tracks:tr.mute=True
 for r in rig['clips'][clip]['actions']:
  ob=bpy.data.objects[r['ownerName']];a=bpy.data.actions[r['action']];ob.animation_data_create();ob.animation_data.action=a
  ob.animation_data.action_slot=next(s for s in a.slots if s.identifier==r['slotIdentifier'])
 root.rotation_euler.z=math.radians({'S':0,'E':90,'N':180,'W':-90}[direction]);sc.frame_set(frame);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def measure(clip,direction,index):
 dg=bpy.context.evaluated_depsgraph_get();raw=[];ev=[];canon=[];proj=[];objects=[];coords={};inv=root.matrix_world.inverted()
 for o in col.all_objects:
  if o.type!='MESH':continue
  r=[o.matrix_world@v.co for v in o.data.vertices];eo=o.evaluated_get(dg);me=eo.to_mesh();v=[eo.matrix_world@p.co for p in me.vertices];count=len(v);eo.to_mesh_clear();raw+=r;ev+=v;canon +=[inv@p for p in v];proj +=[px(p)for p in v];coords[o.name]=[list(p)for p in v];objects.append({'name':o.name,'matrix':mat(o.matrix_world),'rawBounds':bounds(r),'evaluatedBounds':bounds(v),'rawCount':len(r),'evaluatedCount':count,'activeAction':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'scale':list(o.scale),'visible':o.visible_get()})
 b=bounds(canon);p=bounds(proj);rec={'clip':clip,'direction':direction,'index':index,'nativeFrame':index+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(ev),'canonicalSBounds':b,'projectedBoundsNative':p,'objects':objects,'evaluatedCoordinatesSHA256':hashlib.sha256(json.dumps(coords,separators=(',',':')).encode()).hexdigest(),'clearancePass':all(b['min'][j]>=lo-1e-5 and b['max'][j]<=hi+1e-5 for j,(lo,hi)in enumerate([(-1.2,1.2),(-1.2,1.2),(.04,.9)])),'containmentPass':p['min'][0]>0 and p['max'][0]<1280 and p['min'][1]>0 and p['max'][1]<1792 and p['min'][2]>0,'positiveScales':all(all(q>0 for q in x['scale'])for x in objects),'rootStationary':all(abs(root.matrix_world.translation[i])<1e-6 for i in range(3))};return rec,coords
records=[]
for clip in ['windup','active','recovery']:
 for direction in ['N','E','S','W']:
  for i in range(12):
   apply(clip,direction,i+1);rec,_=measure(clip,direction,i);folder=P/'native/replay'/clip/direction;folder.mkdir(parents=True,exist_ok=True);dest=folder/f'{i:03d}.png';sc.render.filepath=str(dest);began=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name);rec.update(path=str(dest.relative_to(P)),sha256=sha(dest),renderSeconds=time.monotonic()-began);records.append(rec);dump(P/'native/replay-validation.json',{'sourceSHA256':inventory['sourceSHA256'],'captureRecords':records});print('INDEPENDENT_REPLAY',clip,direction,i,flush=True)
def error(a,b):return max(abs(x-y)for n in a for aa,bb in zip(a[n],b[n])for x,y in zip(aa,bb))
term=[];trans=[]
for d in ['N','E','S','W']:
 for c in ['windup','active','recovery']:
  apply(c,d,12);_,base=measure(c,d,11)
  for f in [13,24]:apply(c,d,f);_,test=measure(c,d,f-1);term.append({'clip':c,'direction':d,'testedNativeFrame':f,'maxEvaluatedVertexDelta':error(base,test)})
 for a,b in [('windup','active'),('active','recovery')]:
  apply(a,d,12);_,aa=measure(a,d,11);apply(b,d,1);_,bb=measure(b,d,0);trans.append({'from':a,'to':b,'direction':d,'maxEvaluatedVertexDelta':error(aa,bb)})
dump(P/'native/terminal-boundary-validation.json',{'terminals':term,'boundaries':trans})
print('INDEPENDENT_COMPLETE144',flush=True)
