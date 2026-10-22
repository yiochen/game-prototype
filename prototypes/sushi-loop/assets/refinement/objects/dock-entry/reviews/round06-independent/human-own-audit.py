import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';R=B/'source/resources/approved-human-v3';P=B/'source/round-06.blend';F=B/'source/resources/paired-native-v3/dock-floor-round-04.blend';A=R/'customer-rosa-approved.blend';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):H(p) for p in [P,F,A]};bpy.ops.wm.open_mainfile(filepath=str(P));sc=bpy.context.scene;cam=sc.camera;ec=bpy.data.collections['S33_PROP_dock-entry'];er=bpy.data.objects['dock-entry__root'];er.location=(0,-1.5,0)
with bpy.data.libraries.load(str(F),link=False) as(a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc)
with bpy.data.libraries.load(str(A),link=False) as(a,b):b.collections=['S33_CHARACTER_customer_rosa.001'];b.actions=[n for n in a.actions if 'customer-rosa' in n]
hc=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];sc.collection.children.link(hc);hc.hide_render=False;hc.hide_viewport=False
for ob in hc.all_objects:ob.hide_set(False);ob.hide_viewport=False
rig=json.loads((R/'customer-rosa-approved-rig.json').read_text());hr=bpy.data.objects[rig['groundRootObject']];spec=importlib.util.spec_from_file_location('retained_native_actions',R/'independent-floor-audit/native_actions.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def evalmesh(ob,Rinv=None):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];vs=[Rinv@v for v in vs] if Rinv else vs;me.calc_loop_triangles();fs=[list(t.vertices) for t in me.loop_triangles];ev.to_mesh_clear();return vs,fs
def bvh(c):
 vs=[];fs=[]
 for ob in c.all_objects:
  if ob.type!='MESH' or ob.hide_render:continue
  v,f=evalmesh(ob);off=len(vs);vs+=v;fs +=[[i+off for i in p] for p in f]
 return BVHTree.FromPolygons(vs,fs,all_triangles=True)
bpy.context.view_layer.update();st=bvh(ec);dt=bvh(fc)
def support(x,y):
 out=[]
 for name,t in [('entry',st),('deck',dt)]:
  p,n,i,d=t.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),3)
  if p is not None:
   low,_,_,_=t.ray_cast(Vector((x,y,-1)),Vector((0,0,1)),3)
   out.append((p.z,name,low.z if low is not None else p.z))
 return max(out+[(0.,'ground',-100.)])
blocks=[]
for ob in ec.all_objects:
 if ob.type=='MESH' and any(t in ob.name for t in ['__cap_','__post_']):
  vs,fs=evalmesh(ob);blocks.append({'name':ob.name,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]})
def clip(poly,axis,value,greater):
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  dp=(p[axis]-value)*(1 if greater else -1);dq=(q[axis]-value)*(1 if greater else -1)
  if dp>=0:out.append(p)
  if (dp>=0)!=(dq>=0):
   t=dp/(dp-dq);out.append([p[i]+t*(q[i]-p[i]) for i in range(3)])
 return out
path=[(0,-2.1,0),(0,-1.9,.0733333333),(0,-1.75,.1466666667),(0,-1.55,.22),(0,-1.5,.22),(0,-1.3,.22),(.15,-.65,.22),(0,.12,.22),(.78,-.18,.22)];records=[]
for direction,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 rot=Matrix.Rotation(ang,4,'Z');inv=Matrix.Rotation(-ang,4,'Z')
 for idx,pos in enumerate(path):
  mod.apply_clip({'root':hr,'collection':hc},rig,'walk',idx+1,direction,sc);hr.location=rot@Vector(pos);bpy.context.view_layer.update();feet=[];tris=[];allpts=[]
  for ob in hc.all_objects:
   if ob.type!='MESH' or ob.hide_render:continue
   vs,fs=evalmesh(ob,inv);allpts+=vs;tris += [[list(vs[i]) for i in f] for f in fs]
   if 'distinct cocoa shoe' not in ob.name:continue
   lo=[min(v[i] for v in vs) for i in range(3)];hi=[max(v[i] for v in vs) for i in range(3)];ft=BVHTree.FromPolygons(vs,fs,all_triangles=True);samples=[]
   for ix in range(math.ceil((hi[0]-lo[0])/.0025)+1):
    for iy in range(math.ceil((hi[1]-lo[1])/.0025)+1):
     x=lo[0]+ix*.0025;y=lo[1]+iy*.0025
     bottom,n,i,d=ft.ray_cast(Vector((x,y,-1)),Vector((0,0,1)),3)
     if bottom is None:continue
     top,n,i,d=ft.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),4);sz,kind,lower=support(x,y);pen=sz-bottom.z
     samples.append({'xy':[x,y],'shoeBottomZ':bottom.z,'shoeTopZ':top.z if top else None,'supportZ':sz,'supportBottomZ':lower,'support':kind,'penetration':max(0,pen),'gap':max(0,-pen),'solidIntersects':bool(top is not None and bottom.z<sz-1e-5 and top.z>lower+1e-5)})
   feet.append({'name':ob.name,'boundsUnrotatedFloorWorld':[lo,hi],'verticesUnrotatedFloorWorld':[list(v) for v in vs],'triangles':fs,'minSoleRelativeRootZ':lo[2]-pos[2],'sampleSpacing':.0025,'samples':samples,'maxPenetration':max(s['penetration'] for s in samples),'penetratingSoleSamples':sum(s['penetration']>1e-5 for s in samples),'solidIntersectionSamples':sum(s['solidIntersects'] for s in samples),'finiteNearContactSamples':sum(abs(s['supportZ']-s['shoeBottomZ'])<=1e-5 for s in samples)})
  clearance=[]
  for block in blocks:
   lo,hi=block['bounds'];xs=[]
   for tri in tris:
    if max(v[1] for v in tri)<lo[1] or min(v[1] for v in tri)>hi[1] or max(v[2] for v in tri)<lo[2] or min(v[2] for v in tri)>hi[2]:continue
    poly=tri
    for ax,v,g in [(1,lo[1],True),(1,hi[1],False),(2,lo[2],True),(2,hi[2],False)]:poly=clip(poly,ax,v,g) if poly else []
    xs +=[v[0] for v in poly]
   clearance.append({'blocker':block['name'],'actorXExtentInBlockerYZSlab':[min(xs),max(xs)] if xs else None,'conservativeGap':(lo[0]-max(xs) if lo[0]>0 else min(xs)-hi[0]) if xs else None})
  records.append({'direction':direction,'pathIndex':idx,'frame':idx+1,'rootPositionUnrotated':pos,'rootScale':list(hr.scale),'rootMatrix':[list(r) for r in hr.matrix_world],'bodyBoundsUnrotated':[[min(v[i] for v in allpts) for i in range(3)],[max(v[i] for v in allpts) for i in range(3)]],'visibleFeet':feet,'postCapClearance':clearance})
# Re-render first three real poses with fixed environmental camera, all4 facings; entry/floor rendered at same actual native scale.
D=O/'human-native-replay';D.mkdir(exist_ok=True);sc.render.resolution_x=1536;sc.render.resolution_y=1536;cam.data.ortho_scale=6;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*768,(1-q.y)*768]
b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];cam.data.shift_y=(440-b[1])/dy;bpy.context.view_layer.update();renders=[];fr=bpy.data.objects['dock-floor__root']
for direction,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 rot=Matrix.Rotation(ang,4,'Z');er.rotation_euler.z=ang;er.location=rot@Vector((0,-1.5,0));fr.rotation_euler.z=ang
 for idx,pos in enumerate(path[:3]):
  mod.apply_clip({'root':hr,'collection':hc},rig,'walk',idx+1,direction,sc);hr.location=rot@Vector(pos);bpy.context.view_layer.update();f=D/f'human-{direction}-{idx}.png';sc.render.filepath=str(f);bpy.ops.render.render(write_still=True);renders.append({'direction':direction,'pathIndex':idx,'nativeFrame':[1536,1536],'logicalRoot':[384,440],'path':str(f.relative_to(O)),'sha256':H(f)})
rawdir=O/'human-measurements';rawdir.mkdir(exist_ok=True);summaries=[]
for rec in records:
 rawfile=rawdir/f"{rec['direction']}-{rec['pathIndex']}.json";rawfile.write_text(json.dumps(rec,indent=2)+'\n');brief={k:v for k,v in rec.items() if k!='visibleFeet'};brief['visibleFeet']=[{k:v for k,v in f.items() if k not in ['verticesUnrotatedFloorWorld','triangles','samples']} for f in rec['visibleFeet']];brief['rawEvidence']={'path':str(rawfile.relative_to(O)),'sha256':H(rawfile)};summaries.append(brief)
r={'candidatePacketSHA256':'1e1eddc38ea103f5be030b49b870b0f48d8dcd22d304af083f51b243efdf65fc','sourceHashes':before,'nativeSourcesUnchanged':before=={str(p):H(p) for p in [P,F,A]},'method':'Actual approved native actor walk frames1..9 with authored root.scale1.25, no fit or pose edits; actual visible cocoa-shoe triangle lower envelope sampled every.0025 world versus independently evaluated native stair/deck BVHs and ground0. Upward shoe ray finds lowest sole at eachXY; downward environment ray finds actual support top. Solid-intersection samples additionally compare full actual support column bottom/top to actual shoe bottom/top, including a shoe wholly embedded below tread top. Full actual body triangles are clipped to native post/cap YZslabs for conservative lateral clearance. All4facings transformed back to same physical floor space.','records':summaries,'renders':renders};(O/'own-human-contact-clearance.json').write_text(json.dumps(r,indent=2)+'\n');print('OWN_HUMAN',[(r['direction'],r['pathIndex'],max(f['maxPenetration'] for f in r['visibleFeet'])) for r in records],r['nativeSourcesUnchanged'])
