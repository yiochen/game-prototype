import bpy,json,pathlib,math
from mathutils import Vector
O=pathlib.Path(__file__).resolve().parent;R=O/'resources';bpy.ops.wm.open_mainfile(filepath=str(R/'round-01.blend'));s=bpy.context.scene;root=bpy.data.objects['collector__root'];root.rotation_euler.z=0
ranges={}
for name,path,axis in [('guard_rock','rotation_euler',0),('mouth_pulse','scale',2),('mouth_sleeve','scale',2)]:
 ob=bpy.data.objects['collector__'+name];a=bpy.data.actions[f'INLET_NATIVE__idle__collector__{name}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0];aa=bpy.data.actions[f'INLET_NATIVE__active__collector__{name}'];fc=next(f for l in aa.layers for st in l.strips for bag in st.channelbags for f in bag.fcurves if f.data_path==path and f.array_index==axis);assert all(k.interpolation=='LINEAR' for k in fc.keyframe_points);ranges[ob.name]=[min(k.co.y for k in fc.keyframe_points),max(k.co.y for k in fc.keyframe_points)]
assert all(bpy.data.objects[n].parent==root for n in ranges),'Animated owners must be disjoint direct root children'
s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def trig(A,B,C,lo,hi):
 ts=[lo,hi];t0=math.atan2(B,A)
 for k in range(-3,4):
  t=t0+k*math.pi
  if lo<=t<=hi:ts.append(t)
 vs=[C+A*math.cos(t)+B*math.sin(t) for t in ts];return min(vs),max(vs)
parts=[]
for ob in bpy.data.collections['REFINED__sub-collector-inlet'].all_objects:
 if ob.type!='MESH':continue
 owner=ob
 while owner and owner.name not in ranges:owner=owner.parent
 eo=ob.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];intervals=[]
 for p in pts:
  if owner:
   q=owner.matrix_world.inverted()@p;lo,hi=ranges[owner.name];pos=owner.matrix_world.translation
   if owner.name=='collector__guard_rock':
    y=trig(q.y,-q.z,pos.y,lo,hi);z=trig(q.z,q.y,pos.z,lo,hi);iv=[[p.x,y[0],z[0]],[p.x,y[1],z[1]]]
   else:
    zs=[pos.z+q.z*t for t in [lo,hi]];iv=[[p.x,p.y,min(zs)],[p.x,p.y,max(zs)]]
  else:iv=[list(p),list(p)]
  intervals.append(iv)
 parts.append({'name':ob.name,'movingOwner':owner.name if owner else None,'continuousBounds':[[min(i[0][j] for i in intervals) for j in range(3)],[max(i[1][j] for i in intervals) for j in range(3)]]});eo.to_mesh_clear()
b=[[min(p['continuousBounds'][0][i] for p in parts) for i in range(3)],[max(p['continuousBounds'][1][i] for p in parts) for i in range(3)]]
(O/'continuous-envelope.json').write_text(json.dumps({'method':'Exact continuous extrema per saved evaluated neutral vertex. Guard owner is one-axis rotationX with native LINEAR angle interpolation: endpoint and all interior atan2 derivative extrema evaluated. Pulse owners have native LINEAR scaleZ: both interval endpoints evaluated. Saved owner topology is disjoint; no nested animated owner. No sampled-extrema assumption.','nativeChannelRanges':ranges,'canonicalContinuousBounds':b,'groundNonnegative':b[0][2]>=0,'within1x1FootprintAndHeight55':all(b[0][i]>=-.5 and b[1][i]<=.5 for i in [0,1]) and b[0][2]>=0 and b[1][2]<=.55,'parts':parts},indent=2)+'\n');print('CONTINUOUS',b)
