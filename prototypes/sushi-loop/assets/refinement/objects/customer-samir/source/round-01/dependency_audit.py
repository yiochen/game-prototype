import bpy,json,sys,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent.parent;MODE=sys.argv[-1]
rig=json.loads((D/'resources'/('source-'+MODE+'-rig.json')).read_text());root=bpy.data.objects[rig['groundRootObject']];c=next(c for c in bpy.data.collections if root in list(c.all_objects));scene=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=scene
body={};imgs=[];foreign=[]
for o in c.all_objects:
 if o.type=='MESH' and o.get('weighted_character_geometry'):
  key=o.name.split('customer_samir__')[1].split('.')[0];data={'vertices':[[round(float(x),8) for x in v.co] for v in o.data.vertices],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in o.data.polygons],'materials':[m.name for m in o.data.materials],'vertexGroups':[(g.name,g.index) for g in o.vertex_groups],'weights':[[[g.group,round(g.weight,8)] for g in v.groups] for v in o.data.vertices],'modifiers':[(m.type,getattr(m,'width',None),getattr(m,'segments',None)) for m in o.modifiers]};body[key]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 for m in getattr(o.data,'materials',[]):
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
     im=n.image;imgs.append({'owner':o.name,'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None})
for o in scene.objects:
 if o not in list(c.all_objects) and o.type not in ['LIGHT','CAMERA']:foreign.append(o.name)
report={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'mode':MODE,'bodySignatures':body,'images':imgs,'foreignSceneObjects':foreign,'libraries':[l.filepath for l in bpy.data.libraries],'allImagesPacked':all(x['packed'] for x in imgs),'bodyMaterials':['Samir R01' in m.name for o in c.all_objects if o.type=='MESH' and o.get('weighted_character_geometry') for m in o.data.materials],'lights':[{'name':o.name,'location':list(o.location),'color':list(o.data.color),'energy':o.data.energy,'size':o.data.size} for o in scene.objects if o.type=='LIGHT']}
(P/'candidates/round-01'/('dependencies-'+MODE+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(MODE,'BODY',len(body),'PACKED',report['allImagesPacked'],'FOREIGN',foreign)
