"""Read-only native closed-surface and exact-port measurement; no scene save."""
import bpy,bmesh,json,math,hashlib
from mathutils import Vector
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03';coll=bpy.data.collections['rock-wall-end__asset'];root=bpy.data.objects['rock-wall-end__root'];root.rotation_euler=(0,0,0);bpy.context.view_layer.update();side=bpy.data.objects['rock-wall-end__continuous_worn_cobalt'].data
refp=BASE/'source/resources/canonical-port-samples.json';ref=json.loads(refp.read_text())['samples'];loops={}
for i,l in enumerate(side.loops):loops.setdefault(l.vertex_index,[]).append(i)
samples=[]
for v in side.vertices:
 if abs(v.co.x+.5)>1e-7:continue
 ns=[side.corner_normals[i].vector for i in loops[v.index]];n=sum((Vector(n) for n in ns),Vector())/len(ns)
 samples.append({'point':list(v.co),'linearColorRGBA':list(side.color_attributes['stone_albedo'].data[v.index].color),'meanCornerNormal':list(n),'cornerNormals':[list(n) for n in ns]})
ports={}
for rev in [False,True]:
 rows=[];rs=ref['W' if rev else 'E']
 for s in samples:
  y,z=s['point'][1:];r=min(rs,key=lambda r:(y-(-r['y'] if rev else r['y']))**2+(z-r['z'])**2)
  rn=Vector(r['meanCornerNormal']);rn=Vector((-rn.x,-rn.y,rn.z)) if rev else rn
  rows.append({'y':y,'z':z,'profileDelta':math.hypot(y-(-r['y'] if rev else r['y']),z-r['z']),'linearColorMaximumChannelDelta':max(abs(a-b) for a,b in zip(s['linearColorRGBA'][:3],r['colorLinearRGBA'][:3])),'meanCornerNormalDelta':(Vector(s['meanCornerNormal'])-rn).length})
 ports['reversed-middle-diagnostic' if rev else 'same-handed-mandatory']={'sampleCount':len(rows),'maxProfileDelta':max(r['profileDelta'] for r in rows),'maxLinearColorChannelDelta':max(r['linearColorMaximumChannelDelta'] for r in rows),'maxMeanCornerNormalDelta':max(r['meanCornerNormalDelta'] for r in rows),'samples':rows}
bm=bmesh.new()
for ob in coll.objects:
 if ob.type=='MESH':bm.from_mesh(ob.data)
pre={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges)}
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update()
closure={'method':'Read-only virtual union of actual three native meshes; merge identical border coordinates at1e-7world solely for measurement; no scene or source changes','before':pre,'after':{'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'wireEdges':sum(e.is_wire for e in bm.edges),'edgesWithoutExactlyTwoFaces':sum(len(e.link_faces)!=2 for e in bm.edges),'windingInconsistentTwoFaceEdges':sum(len(e.link_faces)==2 and not e.is_contiguous for e in bm.edges),'signedVolume':bm.calc_volume(signed=True)}}
bm.free()
(OUT/'port-and-closure-measurements.json').write_text(json.dumps({'projectSHA256':hashlib.sha256((BASE/'source/round-03.blend').read_bytes()).hexdigest(),'referenceSamplesSHA256':hashlib.sha256(refp.read_bytes()).hexdigest(),'actualWestSamples':samples,'continuity':ports,'closure':closure,'reversedScope':'Retained diagnostic; canonical immutable E/W albedo residual is not simultaneous exact equality law.'},indent=2)+'\n');print(json.dumps({'closure':closure['after'],'port':{k:{a:v for a,v in r.items() if a!='samples'} for k,r in ports.items()}}))
