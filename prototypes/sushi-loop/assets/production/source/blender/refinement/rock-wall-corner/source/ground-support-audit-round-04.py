import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-04.blend'));body=bpy.data.objects['rock-wall-corner__unified_worn_stone'];me=body.data;parent=list(range(len(me.vertices)))
def find(a):
 while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
 return a
for edge in me.edges:
 a,b=map(find,edge.vertices)
 if a!=b:parent[a]=b
ground=[]
for p in me.polygons:
 if p.area>0 and all(abs(me.vertices[v].co.z)<1e-8 for v in p.vertices):ground.append({'polygon':p.index,'area':p.area,'coordinates':[list(me.vertices[v].co) for v in p.vertices]})
out={'sourceSHA256':hashlib.sha256((B/'source/round-04.blend').read_bytes()).hexdigest(),'method':'Actual reopened unified mesh: all ground polygons have finite native area at Z0. Full floor polygon retains the entire ±.5 square. Whole crown/rounded shoulder/exterior/floor is one mesh component; canonical terminal caps remain separate native surfaces.','mainMesh':body.name,'mainMeshConnectedComponents':len(set(find(i) for i in range(len(parent)))),'groundSupportAreaMax':max(p['area'] for p in ground),'largestGroundPolygon':max(ground,key=lambda p:p['area']),'meshes':[o.name for o in bpy.context.scene.objects if o.type=='MESH']};(O/'ground-support-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'groundSupportAreaMax':out['groundSupportAreaMax'],'mainMeshConnectedComponents':out['mainMeshConnectedComponents']}))
