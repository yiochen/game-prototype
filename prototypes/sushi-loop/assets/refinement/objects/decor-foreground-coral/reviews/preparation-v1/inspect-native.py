import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent; R=P/'resources';sys.path.insert(0,str(R/'native'))
import native_actions as na
D=json.loads((R/'inputs/source-assetRecord.json').read_text()); rig=json.loads((R/'inputs/source-rig.json').read_text())
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));asset={**D,'root':root,'collection':col}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
prior={'activeScene':sc.name,'camera':sc.camera.name,'cameraMatrix':[list(x) for x in sc.camera.matrix_world],'cameraOrtho':sc.camera.data.ortho_scale,'cameraShift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'collectionHidden':[col.hide_render,col.hide_viewport],'viewLayers':[{'name':v.name,'use':v.use} for v in sc.view_layers]}
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
sc.view_layers[0].update()
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
def bounds(pts):return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]] if pts else None
def evaluated():
 dg=bpy.context.evaluated_depsgraph_get();out={}
 for o in col.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();pts=[e.matrix_world@v.co for v in m.vertices];out[o.name]=[tuple(p) for p in pts];e.to_mesh_clear()
 return out
objects=[]
for o in col.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world],'custom':{k:plain(o[k]) for k in o.keys()},'constraints':[c.type for c in o.constraints],'modifiers':[m.type for m in o.modifiers],'animationData':bool(o.animation_data),'dataAnimation':bool(o.data and o.data.animation_data)}
 if o.type=='MESH':d.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),uvLayers=list(o.data.uv_layers.keys()),shapeKeys=list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],materials=[m.name for m in o.data.materials if m],localBounds=bounds([v.co for v in o.data.vertices]),flatFaces=sum(not p.use_smooth for p in o.data.polygons),meshUsers=o.data.users)
 objects.append(d)
matset={m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m};mats=[]
for m in matset:
 mats.append({'name':m.name,'objectOwners':[o.name for o in bpy.data.objects if o.type=='MESH' and m in list(o.data.materials)],'users':m.users,'animation':bool(m.animation_data),'treeAnimation':bool(m.node_tree and m.node_tree.animation_data),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked}} for n in m.node_tree.nodes] if m.node_tree else [],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links] if m.node_tree else []})
actions=[]
for cl,rec in rig['clips'].items():
 for tar in rec['actions']:
  a=bpy.data.actions[tar['action']];actions.append({'clip':cl,'owner':tar['ownerName'],'action':a.name,'frameRange':list(a.frame_range),'curves':[{'path':c.data_path,'index':c.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation} for k in c.keyframe_points]} for c in na._fcurves(a)]})
samples=[];closures=[]
for direction in ['N','E','S','W']:
 for clip,frames in [('static',[1,2,13]),('idle',range(1,14))]:
  first=None
  for f in frames:
   na.apply_clip(asset,rig,clip,f,direction,sc);ev=evaluated();pts=[p for v in ev.values() for p in v]
   if f==1:first=ev
   diff=max((Vector(p)-Vector(q)).length for n in ev for p,q in zip(ev[n],first[n]))
   samples.append({'direction':direction,'clip':clip,'frame':f,'bounds':bounds(pts),'rootMatrix':[list(x) for x in root.matrix_world],'rootRotationDegrees':math.degrees(root.rotation_euler.z),'objects':[{'name':n,'bounds':bounds(v),'rotation':list(bpy.data.objects[n].rotation_euler)} for n,v in ev.items()],'maxWorldVertexDeltaFromFirst':diff})
   if f==13:closures.append({'direction':direction,'clip':clip,'frame1vs13MaxVertexDelta':diff})
report={'status':'preparation source discovery only','sourceSHA256':hashlib.sha256((R/'native/original.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scene':sc.name,'collection':col.name,'savedState':prior,'root':root.name,'objects':objects,'materials':mats,'actions':actions,'samples':samples,'closureAndStaticHolds':closures,'externalLibraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'usersWithinAsset':any(n.type=='TEX_IMAGE' and n.image==i for m in matset for n in m.node_tree.nodes)} for i in bpy.data.images],'worldImages':[]}
(P/'evidence/native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'scene':sc.name,'collection':col.name,'savedState':prior,'objects':[{k:o.get(k) for k in ['name','type','location','rotation','scale','localBounds','vertices','faces','materials','uvLayers','shapeKeys']} for o in objects],'closures':closures},indent=2))
