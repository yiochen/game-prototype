"""Evaluated native support surfaces, independently of unchanged socket matrices."""
import bpy,json,sys,math,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;MODE=sys.argv[sys.argv.index('--')+1]
rec=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text());base=json.loads((HERE/'resources'/f'original-{MODE}-audit.json').read_text());old={(s['clip'],s['direction'],s['frame']):s for s in base['samples']};inv=json.loads((HERE/'native-inventory.json').read_text());original={o['name'].split('customer_ellis__')[-1]:o for o in inv}
spec=importlib.util.spec_from_file_location('ellis_native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
root=bpy.data.objects[rec['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=next(c for c in sc.collection.children if root.name in c.all_objects);asset={'root':root,'collection':coll};arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
rest={b['name']:Matrix(b['matrix']) for b in base['armature']['rest']}
probes=[]
for o in coll.all_objects:
 key=o.name.split('customer_ellis__')[-1]
 if key not in original or o.type!='MESH':continue
 source=original[key];box=[Vector(x) for x in source['bounds']];lo=Vector([min(x[i] for x in box) for i in range(3)]);hi=Vector([max(x[i] for x in box) for i in range(3)]);point=(lo+hi)/2;kind=None
 if key.startswith(('palm_','thumb_')):point.z=hi.z;kind='hand-top-support'
 elif key.startswith('minimal_foot_'):point.z=lo.z;kind='sole-ground-support'
 elif key.startswith('pelvis.'):point.z=lo.z;kind='seat-underside-support'
 elif key.startswith('head.'):point=Vector((0,lo.y,.543));kind='mouth-skin-carrier'
 if kind:probes.append({'object':o,'kind':kind,'point':point,'bone':source['groups'][0]})
report={'asset':'customer-ellis','mode':MODE,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'method':'For each of all native poses: transform the original functional face-center witness through the original source pose/rest bone into world space; find nearest point on the actual evaluated remodeled native mesh BVH. Palm/thumb top centers, sole bottom centers, pelvis underside, mouth skin carrier. Bone/socket trajectory equality is audited separately.','toleranceWorld':.005,'maxSurfaceErrorWorld':0,'failures':[],'samples':[],'intendedGroups':{p['object'].name:{'expectedSourceBone':p['bone'],'actualGroups':[g.name for g in p['object'].vertex_groups],'sourceLocalWitness':list(p['point']),'kind':p['kind']} for p in probes}}
for clip,c in rec['clips'].items():
 for direction in 'NESW':
  for frame in range(1,13):
   native.apply_clip(asset,rec,clip,frame,direction,sc);dg=bpy.context.evaluated_depsgraph_get();source=old[(clip,direction,frame)];samples=[]
   for p in probes:
    o=p['object'];e=o.evaluated_get(dg);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];polygons=[list(f.vertices) for f in me.polygons];tree=BVHTree.FromPolygons(points,polygons,all_triangles=False)
    expected=Matrix(source['contacts'][p['bone']]['matrix']) @ rest[p['bone']].inverted() @ arm.matrix_world.inverted() @ root.matrix_world @ p['point'];nearest,normal,index,distance=tree.find_nearest(expected);e.to_mesh_clear()
    sample={'object':o.name,'kind':p['kind'],'sourceWorldWitness':list(expected),'nativeNearestSurface':list(nearest),'surfaceErrorWorld':distance};samples.append(sample);report['maxSurfaceErrorWorld']=max(report['maxSurfaceErrorWorld'],distance)
    if distance>.005:report['failures'].append({'clip':clip,'direction':direction,'frame':frame,**sample})
   report['samples'].append({'clip':clip,'direction':direction,'frame':frame,'surfaceWitnesses':samples})
report['sampleCount']=len(report['samples']);out=OBJ/'candidates/round-03'/(MODE+'-surface-audit.json');out.write_text(json.dumps(report,separators=(',',':'))+'\n');print('ELLIS_SURFACE_AUDIT',MODE,report['sampleCount'],report['maxSurfaceErrorWorld'],len(report['failures']),flush=True)
