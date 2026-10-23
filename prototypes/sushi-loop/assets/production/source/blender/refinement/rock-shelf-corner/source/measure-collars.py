import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'candidates/round-01'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-01.blend'));co=next(o for o in bpy.context.scene.objects if 'continuous_rounded' in o.name)
with bpy.data.libraries.load(str(BASE/'dependencies/canonical-middle.blend'),link=False) as (fr,to):to.objects=['rock-shelf-middle__sculpted_core']
ref=to.objects[0]
def triangles(m,axis,lo,hi):
 m.calc_loop_triangles();out=[]
 for t in m.loop_triangles:
  if m.polygons[t.polygon_index].material_index in [1,2]:continue
  ps=[m.vertices[i].co for i in t.vertices]
  if min(p[axis] for p in ps)>=lo-1e-6 and max(p[axis] for p in ps)<=hi+1e-6:out.append(t)
 return sorted(out,key=lambda t:m.polygons[t.polygon_index].material_index!=3)
tris={'cornerW':triangles(co.data,0,-.5,-.47499),'cornerN':triangles(co.data,1,.47499,.5),'referenceW':triangles(ref.data,0,-.5,-.43999),'referenceN':triangles(ref.data,0,.43999,.5)}
def eval_point(m,ts,p,kind):
 for t in ts:
  poly=m.polygons[t.polygon_index]
  if kind=='top' and poly.normal.z<.9:continue
  if kind=='bottom' and poly.normal.z>-.9:continue
  if kind=='body' and abs(poly.normal.z)>.9:continue
  a,b,c=[m.vertices[i].co for i in t.vertices];n=(b-a).cross(c-a)
  if n.length<1e-10:continue
  if abs((p-a).dot(n.normalized()))>1e-6:continue
  v0=[float(b[k])-float(a[k]) for k in range(3)];v1=[float(c[k])-float(a[k]) for k in range(3)];v2=[float(p[k])-float(a[k]) for k in range(3)];dot=lambda x,y:sum(x[k]*y[k] for k in range(3));d00=dot(v0,v0);d01=dot(v0,v1);d11=dot(v1,v1);d20=dot(v2,v0);d21=dot(v2,v1);den=d00*d11-d01*d01
  v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;u=1-v-w
  if min(u,v,w)<-1e-5:continue
  weights=[u,v,w];attr=m.color_attributes['rock_shelf_albedo'];col=[sum(weights[j]*attr.data[t.vertices[j]].color[k] for j in range(3)) for k in range(4)];normal=sum((m.corner_normals[t.loops[j]].vector*weights[j] for j in range(3)),Vector()).normalized();geometric=normal.copy();affine=m.attributes.get('canonical_collar_normal')
  if poly.material_index==3:normal=sum((affine.data[t.loops[j]].vector*weights[j] for j in range(3)),Vector()).normalized()
  return {'position':list(p),'normal':list(normal),'encodedGeometricNormal':list(geometric),'material':poly.material_index,'albedo':col,'polygon':t.polygon_index,'weights':weights,'triangleLoops':list(t.loops),'triangleVertices':list(t.vertices)}
 raise ValueError((list(p),kind))
profile=[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]
rows=[]
for port in ['W','N']:
 for longitudinal in [0,.25,.5,.75,1]:
  x= -.5+.025*longitudinal if port=='W' else .5-.025*longitudinal
  for edge in range(6):
   a=profile[edge];b=profile[(edge+1)%6];kind='bottom' if edge==0 else 'top' if edge==3 else 'body'
   for transverse in [0,.125,.25,.5,.75,.875,1]:
    y=(1-transverse)*a[0]+transverse*b[0];z=(1-transverse)*a[1]+transverse*b[1];rp=Vector((x,y,z));cp=rp if port=='W' else Vector((-y,x,z));r=eval_point(ref.data,tris['reference'+port],rp,kind);c=eval_point(co.data,tris['corner'+port],cp,kind);rn=Vector(r['normal']);rn=rn if port=='W' else Vector((-rn.y,rn.x,rn.z));rows.append({'port':port,'longitudinal':longitudinal,'edge':edge,'transverse':transverse,'candidate':c,'canonical':r,'normalError':(Vector(c['normal'])-rn).length,'albedoError':max(abs(c['albedo'][k]-r['albedo'][k]) for k in range(4))})
result={'method':'Actual saved-source triangle interpolation from point-albedo and native CORNER affine-vector attribute, normalized after interpolation as the linked Object→World→Normalize shader does. Encoded geometric custom normals are retained separately. Position on every profile segment, every endpoint and intermediate samples across exact .025 collars.','samples':rows,'summary':{port:{'samples':len([r for r in rows if r['port']==port]),'maxNormalError':max(r['normalError'] for r in rows if r['port']==port),'maxAlbedoError':max(r['albedoError'] for r in rows if r['port']==port)} for port in ['W','N']},'note':'Small encoded custom-normal representation differences are retained as measurements; they provide no waiver for a visible seam.'}
(OUT/'collar-fields.json').write_text(json.dumps(result,indent=2)+'\n');print(result['summary'])
