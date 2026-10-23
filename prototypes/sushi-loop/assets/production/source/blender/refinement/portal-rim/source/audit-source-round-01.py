"""Read-only dependency/topology audit of exact editable candidate source."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;C=S.parent/'candidates/round-01'
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
col=bpy.data.collections['S33_PROP_portal_rim.002'];own=list(col.all_objects);root=bpy.data.objects['portal_rim__root.002']
meshes=[]
for o in own:
    if o.type!='MESH':continue
    m=o.data;uses={}
    for p in m.polygons:
        for e in p.edge_keys:
            key=tuple(sorted(e));uses[key]=uses.get(key,0)+1
    m.calc_loop_triangles();volume=sum(m.vertices[t.vertices[0]].co.dot(m.vertices[t.vertices[1]].co.cross(m.vertices[t.vertices[2]].co))/6 for t in m.loop_triangles)
    meshes.append({'object':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(m.vertices),'polygons':len(m.polygons),'triangles':len(m.loop_triangles),'boundaryEdges':sum(n==1 for n in uses.values()),'overusedEdges':sum(n>2 for n in uses.values()),'signedLocalVolume':volume,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
images=[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images if im.source not in ['VIEWER','GENERATED']]
materials=sorted({s.material for o in own for s in o.material_slots if s.material},key=lambda m:m.name)
d={'asset':'portal-rim','projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'sceneCount':len(bpy.data.scenes),'collection':col.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'savedFrame':sc.frame_current,'objectCount':len(own),'meshCount':len(meshes),'meshes':meshes,'externalParents':[o.name for o in own if o.parent and o.parent not in own],'libraries':[l.filepath for l in bpy.data.libraries],'externalImages':images,'imageTextureNodes':[{'material':m.name,'node':n.name} for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'materialNodes':{m.name:[n.bl_idname for n in m.node_tree.nodes] for m in materials},'lights':[{'name':o.name,'location':list(o.location),'color':list(o.data.color),'power':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None,'scope':'Read-only exact candidate source; no model save or render. No image nodes, compositing replacement, external library, armature or cards used.'}
(C/'source-audit.json').write_text(json.dumps(d,indent=2)+'\n')
assert not d['externalParents'] and not d['libraries'] and not d['externalImages'] and not d['imageTextureNodes']
assert all(m['boundaryEdges']==0 and m['overusedEdges']==0 and m['signedLocalVolume']>0 for m in meshes)
print(json.dumps({'sourceSHA256':d['projectSHA256'],'meshes':len(meshes),'objects':len(own),'allClosedPositiveVolume':True,'externalDependencies':False}))
