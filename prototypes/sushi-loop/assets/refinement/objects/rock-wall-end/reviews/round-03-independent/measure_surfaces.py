import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d
OUT=Path(__file__).resolve().parent
side=bpy.data.objects['rock-wall-end__continuous_worn_cobalt'].data
rings={}
for v in side.vertices:rings.setdefault(round(v.co.x,8),[]).append((v.co.y,v.co.z))
intersections=[];areas=[]
def possible(a,b,c,d):
 return not(max(a[0],b[0])<min(c[0],d[0]) or max(c[0],d[0])<min(a[0],b[0]) or max(a[1],b[1])<min(c[1],d[1]) or max(c[1],d[1])<min(a[1],b[1]))
for x,pts in rings.items():
 n=len(pts);areas.append(sum(pts[i][0]*pts[(i+1)%n][1]-pts[(i+1)%n][0]*pts[i][1] for i in range(n))/2)
 for i in range(n):
  a,b=pts[i],pts[(i+1)%n]
  for j in range(i+2,n):
   if i==0 and j==n-1:continue
   c,d=pts[j],pts[(j+1)%n]
   if possible(a,b,c,d) and intersect_line_line_2d(Vector(a),Vector(b),Vector(c),Vector(d)) is not None:intersections.append({'x':x,'segments':[i,j]})
caps=[]
for o in bpy.data.collections['rock-wall-end__asset'].objects:
 if o.type=='MESH' and o.data!=side:
  s=1 if 'finished_E' in o.name else -1
  vals=[s*p.normal.x for p in o.data.polygons]
  caps.append({'name':o.name,'triangles':len(vals),'minimumOutwardNormalX':min(vals),'reversedOrFoldedYZTriangles':sum(v<=0 for v in vals),'nonTriangularFaces':sum(len(p.vertices)!=3 for p in o.data.polygons)})
result={'purpose':'Read-only geometry diagnostics supplementary to closed-solid audit and direct rendered all4 inspection.','sideRings':len(rings),'samplesPerRing':sorted(set(len(p) for p in rings.values())),'minimumSignedYZRingArea':min(areas),'maximumSignedYZRingArea':max(areas),'ringSegmentIntersections':intersections,'caps':caps,'limits':'Cross-section intersection and cap projection tests supplement, rather than replace, direct visible defect inspection. No mesh/source mutation or fitting.'}
(OUT/'surface-diagnostics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
