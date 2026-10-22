import bpy, json, math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
O=P.parent.parent
source=P/'resources/source/original-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
def simple(v):
 try:return list(v)
 except:return str(v)
def props(x):return {k:simple(v) if not isinstance(v,(str,int,float,bool)) else v for k,v in x.items() if k!='_RNA_UI'}
roots=[x for x in bpy.data.objects if x.name.startswith('wreck-corner__root')]
info={'source':str(source),'roots':[{'name':x.name,'props':props(x),'collections':[c.name for c in x.users_collection],'matrix':list(map(list,x.matrix_world))} for x in roots], 'collections':[{'name':c.name,'props':props(c),'objects':len(c.all_objects)} for c in bpy.data.collections if 'wreck-corner' in c.name], 'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None} for s in bpy.data.scenes]}
root=next(x for x in roots if x.name=='wreck-corner__root.001')
col=next(c for c in root.users_collection if any(o.type=='MESH' for o in c.all_objects))
inv=root.matrix_world.inverted(); obs=[]
for ob in col.all_objects:
 if ob.type!='MESH':continue
 verts=[inv@ob.matrix_world@v.co for v in ob.data.vertices]
 obs.append({'name':ob.name,'parent':ob.parent.name if ob.parent else None,'props':props(ob),'matrix':list(map(list,inv@ob.matrix_world)),'vertices':[list(v) for v in verts],'polygons':[{'vertices':list(f.vertices),'material':f.material_index,'smooth':f.use_smooth,'normal':list(f.normal)} for f in ob.data.polygons],'materials':[{'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname} for n in m.node_tree.nodes] if m.use_nodes else []} for m in ob.data.materials]})
info['selectedCollection']=col.name;info['objects']=obs
vs=[v for ob in obs for v in ob['vertices']]
info['bounds']={'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]}
info['savedScene']={'name':bpy.context.scene.name,'camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None}
(P/'original-native-inspection.json').write_text(json.dumps(info,indent=2)+'\n')
print('OWN ORIGINAL',json.dumps({'collection':col.name,'root':root.name,'bounds':info['bounds'],'objects':[(o['name'],len(o['vertices'])) for o in obs]}))
