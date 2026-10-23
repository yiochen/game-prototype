import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native
rig=json.loads((P/'rig-round01.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in root.users_collection if 'CHARACTER' in c.name);arm=next(o for o in coll.all_objects if o.type=='ARMATURE');sc=bpy.data.scenes.new('Noor independent source inspection');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update();asset={'collection':coll,'root':root,'armature':arm}
def geom(o,dg):
 e=o.evaluated_get(dg);me=e.to_mesh();coords=[e.matrix_world@v.co for v in me.vertices];r={'vertices':len(me.vertices),'polygons':len(me.polygons),'bounds':[[min(v[i] for v in coords),max(v[i] for v in coords)] for i in range(3)]};e.to_mesh_clear();return r
rows=[]
for c in rig['clips']:
 for d in ['S','E','N','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,c,f,d,sc);dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg);rows.append({'clip':c,'direction':d,'index':f-1,'bones':{b.name:{'head':list(ae.matrix_world@b.head),'tail':list(ae.matrix_world@b.tail),'matrix':[list(v) for v in ae.matrix_world@b.matrix]} for b in ae.pose.bones},'props':{o.name:{'matrix':[list(v) for v in o.evaluated_get(dg).matrix_world],'hide':o.hide_render} for o in coll.all_objects if '__held_' in o.name or '__knife_' in o.name},'rootMatrix':[list(v) for v in root.matrix_world],'rotation':root.rotation_euler.z,'geometry':{o.name:geom(o,dg) for o in coll.all_objects if o.type=='MESH'}})
(P/'source-native-motion-original.json').write_text(json.dumps(rows,separators=(',',':')))
native.apply_clip(asset,rig,'idle',1,'S',sc);arm.data.pose_position='REST';bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones};(P/'source-native-rest-original.json').write_text(json.dumps(rest,indent=2))
obs=[]
for o in coll.all_objects:
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'matrix':[list(r) for r in o.matrix_world],'modifiers':[{ 'name':m.name,'type':m.type,'levels':getattr(m,'levels',None),'segments':getattr(m,'segments',None),'width':getattr(m,'width',None),'object':getattr(m,'object',None).name if getattr(m,'object',None) else None} for m in o.modifiers]}
 if o.type=='MESH':
  row.update(geom(o,dg));row['localBounds']=[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)];row['groups']=[g.name for g in o.vertex_groups];row['materials']=[m.name if m else None for m in o.data.materials];row['shapeKeys']=list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else []
 obs.append(row)
report={'collection':coll.name,'root':root.name,'armature':arm.name,'objects':obs,'blenderVersion':bpy.app.version_string,'sourceSHA256':hashlib.sha256((P/'original-library.blend').read_bytes()).hexdigest(),'clips':rig['clips'],'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]}
(P/'source-inspection.json').write_text(json.dumps(report,indent=2));print('INSPECT',coll.name,root.name,arm.name,len(obs));print('MESHES',[(o['name'],o.get('localBounds'),o.get('groups')) for o in obs if o['type']=='MESH'])
