"""Read-only audit of new damaged timber solids; no scene or project writes."""
import bpy,bmesh,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-02'
c=bpy.data.collections['S33_PROP_decor-background-wreck.001'];dg=bpy.context.evaluated_depsgraph_get();objects=[]
for obj in c.all_objects:
 if obj.type!='MESH':continue
 ev=obj.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 objects.append({'object':obj.name,'evaluatedVertices':len(bm.verts),'evaluatedFaces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'signedVolume':bm.calc_volume(signed=True),'constraints':len(obj.constraints)})
 bm.free();ev.to_mesh_clear()
assert all(x['boundaryEdges']==x['nonmanifoldEdges']==x['zeroAreaFaces']==0 and x['signedVolume']>0 for x in objects)
(O/'topology-audit.json').write_text(json.dumps({'asset':'decor-background-wreck','round':'round-02','sourceProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'method':'Evaluated native solid topology check only; does not certify visible quality or replace the original judge. No project save.','objects':objects},indent=2)+'\n')
print('Audited closed positive-volume evaluated solids',len(objects))
