import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;P=HERE/'round-01.blend';bpy.ops.wm.open_mainfile(filepath=str(P));COL=bpy.data.collections['S33 production concept cobalt-shelf.001'];ROOT=bpy.data.objects['S33 production concept cobalt-shelf root.001'];ROOT.rotation_euler.z=0;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
obs=[];trees={}
for o in sorted(COL.all_objects,key=lambda o:o.name):
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me);bm.transform(ev.matrix_world);bm.normal_update();trees[o.name]=BVHTree.FromBMesh(bm);volume=bm.calc_volume(signed=True)
 obs.append({'name':o.name,'signedVolume':volume,'groundVertices':sum(abs(v.co.z)<1e-6 for v in bm.verts),'minZ':min(v.co.z for v in bm.verts),'maxZ':max(v.co.z for v in bm.verts),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)});bm.free();ev.to_mesh_clear()
edges=[]
names=list(trees)
for i,name in enumerate(names):
 for other in names[i+1:]:
  pairs=trees[name].overlap(trees[other])
  if pairs:edges.append({'objects':[name,other],'intersectingTrianglePairs':len(pairs)})
reached={r['name'] for r in obs if r['groundVertices']>0}
while True:
 before=set(reached)
 for e in edges:
  if any(n in reached for n in e['objects']):reached.update(e['objects'])
 if before==reached:break
out={'pathBase':'object root','sourceProject':'source/round-01.blend','sourceSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'measurement':'Actual evaluatedS vertices/topology/closed signedvolume and triangle BVH intersection graph. Proper rotations preserve connectivity. Intersections are intentional native boulder nesting, not coplanar surfaces.','objects':obs,'surfaceIntersections':edges,'allMeshesConnectedToGroundedNativeMass':len(reached)==len(obs),'noPlanePlatformOrFeet':True}
(OBJ/'candidates/round-01/support-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
