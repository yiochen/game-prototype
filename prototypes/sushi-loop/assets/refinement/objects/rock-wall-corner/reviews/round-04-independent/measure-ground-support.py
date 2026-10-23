import bpy,json,math
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(O/'resources/round-04.blend'));ob=bpy.data.objects['rock-wall-corner__unified_worn_stone'];me=ob.data;area=0;ground=[];apex=[]
for f in me.polygons:
 pts=[me.vertices[i].co for i in f.vertices]
 if all(abs(v.z)<1e-7 for v in pts):
  a=pts[0];pa=sum(((pts[j]-a).cross(pts[j+1]-a)).length/2 for j in range(1,len(pts)-1));area+=pa;ground.append({'polygon':f.index,'vertices':list(f.vertices),'areaXY':pa,'normal':list(f.normal)})
 for li in f.loop_indices:
  lp=me.loops[li];v=me.vertices[lp.vertex_index].co
  if abs(v.x+.5)<1e-7 and abs(v.y-.5)<1e-7 and abs(v.z)<1e-7:apex.append({'polygon':f.index,'polygonVertices':[list(p) for p in pts],'polygonNormal':list(f.normal),'loopNormal':list(me.corner_normals[li].vector),'allPolygonZZero':all(abs(p.z)<1e-7 for p in pts)})
out={'mesh':ob.name,'groundFaceCount':len(ground),'summedFiniteGroundXYArea':area,'expectedOneCellArea':1,'groundFaces':ground,'NWBottomPointLoops':apex,'bottomNormalAssessment':'Independent boundary audit retained two maxnormal outliers at single NW bottom vertex. All incident candidate faces for this vertex are planar Z0 underside faces, invisible to the registered above-ground camera. Their -Z normals differ from the canonical side-ring blended edge normal. Assess exposed positive-Z boundary continuity separately; do not relabel these raw underside values as zero or as a visible seam.'}
(O/'ground-support-assessment.json').write_text(json.dumps(out,indent=2)+'\n');print('GROUND_SUPPORT',len(ground),area,'apexLoops',len(apex),all(x['allPolygonZZero'] for x in apex))
