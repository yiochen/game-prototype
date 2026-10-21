import sys
sys.dont_write_bytecode=True
"""Read-only audit: generated native surfaces are closed, manifold and outward.
The native build recipe welds collapsed poles and uses periodic closed piping.
"""
import bpy,bmesh,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'candidates/round02'
scene=bpy.data.scenes['Mateo warm soft native round02'];bpy.context.window.scene=scene
rows=[]
for o in scene.objects:
 if o.type!='MESH' or '__refined_' not in o.name:continue
 bm=bmesh.new();bm.from_mesh(o.data)
 result={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True)}
 assert result['boundaryEdges']==0 and result['nonManifoldEdges']==0,(o.name,result)
 assert result['signedVolume']>0,(o.name,result)
 bm.free();rows.append({'object':o.name,'measured':result})
(OUT/'topology-cleanup.json').write_text(json.dumps({'candidateSHA256':hashlib.sha256((HERE/'round02.blend').read_bytes()).hexdigest(),'scope':'Actual generated native mesh audit; no project save or geometry mutation. Cleanup lives in build_round02.py.','meshes':rows,'allClosedManifoldPositiveVolume':True},indent=2)+'\n')
print('MATEO_TOPOLOGY_CLEAN',len(rows))
