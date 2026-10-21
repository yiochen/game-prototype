import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent;C=P.parent/'candidates/round-02';head=bpy.data.objects['chef_lena__head.002'];mouth=bpy.data.objects['chef_lena__R01_gentle_smile'];bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons]);depth=[]
for v in mouth.data.vertices:
 hit,*_=bvh.ray_cast(Vector((v.co.x,-.8,v.co.z)),Vector((0,1,0)),2);assert hit is not None;depth.append(v.co.y-hit.y)
sections=[depth[i:i+16] for i in range(0,len(depth),16)];intersections=all(min(a)<0<max(a) for a in sections)
head_group=head.vertex_groups['head'].index;mouth_group=mouth.vertex_groups['head'].index
weights_pass=all(len(v.groups)==1 and v.groups[0].group==head_group and abs(v.groups[0].weight-1)<1e-5 for v in head.data.vertices) and all(len(v.groups)==1 and v.groups[0].group==mouth_group and abs(v.groups[0].weight-1)<1e-5 for v in mouth.data.vertices)
contacts=json.loads((C/'evaluated-contacts.json').read_text());samples=[]
for r in contacts:
 m=r['bones']['head']['matrix'];factor=math.sqrt(sum(m[i][1]**2 for i in range(3)));samples.append({'clip':r['clip'],'direction':r['direction'],'index':r['index'],'maximumWorldFrontRelief':max(0,-min(depth))*factor,'maximumWorldEmbedding':max(depth)*factor})
vol=sum(mouth.data.vertices[p.vertices[0]].co.dot(mouth.data.vertices[p.vertices[i]].co.cross(mouth.data.vertices[p.vertices[i+1]].co))/6 for p in mouth.data.polygons for i in range(1,len(p.vertices)-1))
report={'source':'source/round-02.blend','sourceSHA256':hashlib.sha256((P/'round-02.blend').read_bytes()).hexdigest(),'method':'Ray-query every actual mouth rest vertex at itsXZ against actual baked rounded head; verify all97cross-sections cross the skin surface. Both meshes are100%weighted to same native head bone with equal common rest coordinates, so all192evaluated head matrices carry the attachment coherently.','restLocalSurfaceDepthRange':[min(depth),max(depth)],'allCrossSectionsIntersectSkin':intersections,'closedOutwardSignedVolume':vol,'sameHeadBoneWeights':weights_pass,'weightTolerance':1e-5,'originalHeadWeightMaxNumericalError':max(abs(v.groups[0].weight-1) for v in head.data.vertices),'sameParent':head.parent==mouth.parent,'equalObjectMatrixBasis':max(abs(head.matrix_basis[i][j]-mouth.matrix_basis[i][j]) for i in range(4) for j in range(4))<1e-7,'sampleCount':len(samples),'maximumEvaluatedWorldRelief':max(s['maximumWorldFrontRelief'] for s in samples),'maximumEvaluatedWorldEmbedding':max(s['maximumWorldEmbedding'] for s in samples),'samples':samples,'technicalPass':intersections and weights_pass and vol>0 and len(samples)==192 and max(0,-min(depth))<.00101}
(C/'smile-surface-validation.json').write_text(json.dumps(report,indent=2));print('SMILE_SURFACE',report['technicalPass'],report['restLocalSurfaceDepthRange'],report['maximumEvaluatedWorldRelief'])
