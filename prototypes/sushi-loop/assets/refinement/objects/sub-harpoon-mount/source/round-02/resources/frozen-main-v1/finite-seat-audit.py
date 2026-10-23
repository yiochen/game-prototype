import bpy,json,pathlib,itertools,math
from mathutils import Vector,Matrix
out=pathlib.Path(__file__).resolve().parent;cand=out/'resources/candidates/stage1-v5';src=out/'resources/source/stage1-v5/resources';sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0);actions=json.loads(root['nativeActions'])
for owner,an in actions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def vv(v):return [float(a) for a in v]
def bb(v):return [[min(p[i] for p in v) for i in range(len(v[0]))],[max(p[i] for p in v) for i in range(len(v[0]))]]
seats=[]
for o in bpy.data.objects:
 if o.type!='MESH' or ('contact_seat' not in o.name):continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];faces=[]
 for f in me.polygons:
  n=(eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()
  if ('collector' in o.name and n.y<-.999) or ('collector' not in o.name and n.z>.999):
   vs=[pts[i] for i in f.vertices];faces.append({'normal':vv(n),'bounds':bb(vs),'areaWorld':float(f.area)})
 seats.append({'name':o.name,'evaluatedBounds':bb(pts),'finiteContactFaces':faces});eo.to_mesh_clear()
mounts=json.loads((cand/'proposed-mounts.json').read_text())['mounts'];reservations=[]
for aid,m in mounts.items():
 actual=bpy.data.objects[m['object']].matrix_local;expected=Matrix(m['matrixLocal']);err=max(abs(actual[r][c]-expected[r][c]) for r in range(4) for c in range(4));b=m['localReservation'];corners=[Vector(v) for v in itertools.product(*[(b[0][i],b[1][i]) for i in range(3)])];cam=json.loads((src/(aid+'-camera.json')).read_text());scale=cam['captureScale'];ux=cam['calibration']['unitX'][0]/scale;uy=-cam['calibration']['unitDepth'][1]/scale;uz=cam['calibration']['unitHeight'][1]/scale;records=[]
 for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
  R=Matrix.Rotation(ang,3,'Z');pp=[R@v for v in corners];xy=[Vector((96+ux*v.x,248+uy*v.y+uz*v.z)) for v in pp];b2=bb(xy);records.append({'direction':d,'logicalBounds':b2,'insideFrame':b2[0][0]>=0 and b2[1][0]<=192 and b2[0][1]>=0 and b2[1][1]<=352})
 reservations.append({'asset':aid,'matrixMaximumError':err,'declaredUniformScale':m['uniformScale'],'integratedNeutralReservation':bb([actual@p for p in corners]),'ownStandaloneProjection':records})
(out/'independent-interface-audit.json').write_text(json.dumps({'actualNativeFiniteSeatFaces':seats,'mountsAndReservations':reservations,'qualification':'Own evaluated finite seat patches and transforms verified. Collector structural overlap with rear bracket is intentional; future component contact/contouring/art and active clips are not certified by an empty reservation.'},indent=2)+'\n')
print('INTERFACES',len(seats),len(reservations),all(p['insideFrame'] for r in reservations for p in r['ownStandaloneProjection']))
