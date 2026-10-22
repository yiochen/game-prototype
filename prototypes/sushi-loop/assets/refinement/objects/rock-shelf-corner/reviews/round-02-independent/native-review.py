import bpy,sys,json,pathlib,math,hashlib,bmesh
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;B=P.parents[1];C=B/'candidates/round-02';O=P/'native';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-02.blend'));s=bpy.context.scene;core=next(o for o in s.objects if 'continuous_rounded' in o.name);root=core.parent;cam=s.camera;s.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
with bpy.data.libraries.load(str(B/'source/dependencies/canonical-middle.blend'),link=False) as (fr,to):to.objects=['rock-shelf-middle__sculpted_core','rock-shelf-middle__embedded_stone_A','rock-shelf-middle__embedded_stone_B']
refs=list(to.objects);ref=refs[0];cm=ref.data;cm.calc_loop_triangles();m=core.data;m.calc_loop_triangles();att=m.attributes['canonical_collar_normal'];ca=m.color_attributes['rock_shelf_albedo'];ra=cm.color_attributes['rock_shelf_albedo']
# Actual linked shader chain, not a raw attribute equated to a BSDF normal.
mat=m.materials[3];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');normal=bs.inputs['Normal'].links[0].from_node;transform=normal.inputs[0].links[0].from_node;attr=transform.inputs['Vector'].links[0].from_node
chain={'normalMath':normal.operation,'transformType':transform.vector_type,'from':transform.convert_from,'to':transform.convert_to,'attribute':attr.attribute_name,'domain':att.domain,'dataType':att.data_type}
assert chain=={'normalMath':'NORMALIZE','transformType':'VECTOR','from':'OBJECT','to':'WORLD','attribute':'canonical_collar_normal','domain':'CORNER','dataType':'FLOAT_VECTOR'},chain
assert all(abs(core.scale[i]-1)<1e-6 for i in range(3)) and all(abs(root.scale[i]-1)<1e-6 for i in range(3))
def kind(mesh,tri):
 n=mesh.polygons[tri.polygon_index].normal
 return 'bottom' if n.z<-.9 else 'top' if n.z>.9 else 'body'
def bary(p,a,b,c):
 e=b-a;f=c-a;q=p-a;den=e.dot(e)*f.dot(f)-e.dot(f)**2
 if abs(den)<1e-15:return None
 n=e.cross(f)
 if abs(q.dot(n.normalized()))>2e-6:return None
 v=(f.dot(f)*q.dot(e)-e.dot(f)*q.dot(f))/den;w=(e.dot(e)*q.dot(f)-e.dot(f)*q.dot(e))/den;u=1-v-w
 return (u,v,w) if min(u,v,w)>-2e-5 else None
canonical=[]
for t in cm.loop_triangles:
 if cm.polygons[t.polygon_index].material_index:continue
 ps=[cm.vertices[i].co.copy() for i in t.vertices]
 if all(p.x<=-.4399 for p in ps) or all(p.x>=.4399 for p in ps):canonical.append((t,ps,kind(cm,t)))
weights=[(1,0,0),(0,1,0),(0,0,1),(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6),(.5,.5,0),(0,.5,.5),(.5,0,.5)]
actualMatrices={}
for direction,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle;bpy.context.view_layer.update();actualMatrices[direction]=core.matrix_world.to_3x3().copy()
root.rotation_euler.z=0;bpy.context.view_layer.update()
rows=[];badMappings=[]
for t in m.loop_triangles:
 if m.polygons[t.polygon_index].material_index!=3:continue
 ps=[m.vertices[i].co.copy() for i in t.vertices];port='W' if sum(p.x for p in ps)/3<-.4749 else 'N';inv=lambda p:p.copy() if port=='W' else Vector((p.y,-p.x,p.z));cps=[inv(p) for p in ps];kk=kind(m,t)
 ct=next(((tri,cvs) for tri,cvs,ck in canonical if ck==kk and all(bary(p,*cvs) is not None for p in cps)),None)
 if ct is None:badMappings.append(t.index);continue
 tri,cvs=ct
 for w in weights:
  cp=sum((ps[i]*w[i] for i in range(3)),Vector());rp=inv(cp);bw=bary(rp,*cvs);raw=sum((att.data[t.loops[i]].vector*w[i] for i in range(3)),Vector());cn=sum((cm.corner_normals[tri.loops[i]].vector*bw[i] for i in range(3)),Vector());rawlocal=inv(raw);albedo=[sum(ca.data[t.vertices[i]].color[k]*w[i] for i in range(3)) for k in range(4)];ralbedo=[sum(ra.data[tri.vertices[i]].color[k]*bw[i] for i in range(3)) for k in range(4)];geom=sum((m.corner_normals[t.loops[i]].vector*w[i] for i in range(3)),Vector());gerr=(inv(geom).normalized()-cn.normalized()).length
  for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
   actual=actualMatrices[d]@raw;canonicalLocal=cn if port=='W' else Vector((-cn.y,cn.x,cn.z));reference=actualMatrices[d]@canonicalLocal
   rows.append({'triangle':t.index,'canonicalTriangle':tri.index,'port':port,'direction':d,'weights':w,'position':list(cp),'normalError':(actual.normalized()-reference.normalized()).length,'albedoError':max(abs(albedo[k]-ralbedo[k]) for k in range(4)),'geometricNormalError':gerr})
root.rotation_euler.z=0;bpy.context.view_layer.update();pts=[o.matrix_world@v.co for o in s.objects if o.type=='MESH' for v in o.data.vertices];bm=bmesh.new();bm.from_mesh(m);topology={'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges)};bm.free();groundArea=sum(t.area for t in m.loop_triangles if all(abs(m.vertices[i].co.z)<1e-7 for i in t.vertices));base=cm.materials[0];basebs=next(n for n in base.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def val(i):
 v=i.default_value
 try:return list(v)
 except:return v
baseInputs={i.identifier:i for i in basebs.inputs};paramDiff={i.identifier:[val(i),val(baseInputs[i.identifier])] for i in bs.inputs if hasattr(i,'default_value') and i.identifier!='Normal' and val(i)!=val(baseInputs[i.identifier])}
record={'sourceSHA256':sha(B/'source/round-02.blend'),'canonicalSHA256':sha(B/'source/dependencies/canonical-middle.blend'),'actualNormalShaderChain':chain,'allRootScalesIdentity':True,'collarTriangles':len({r['triangle'] for r in rows}),'samples':len(rows),'unmappedTriangles':badMappings,'maximumRenderedNormalError':max(r['normalError'] for r in rows),'maximumAlbedoError':max(r['albedoError'] for r in rows),'maximumGeometricNormalDifference':max(r['geometricNormalError'] for r in rows),'materialDefaultDifferencesExcludingNormal':paramDiff,'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'groundArea':groundArea,'topology':topology,'animation':{o.name:bool(o.animation_data) for o in s.objects},'materialAnimation':{mm.name:bool(mm.animation_data or (mm.node_tree and mm.node_tree.animation_data)) for o in s.objects if o.type=='MESH' for mm in o.data.materials if mm},'rows':rows}
(P/'native-independent-audit.json').write_text(json.dumps(record,indent=2)+'\n')
# Reopen-source heroes first; exact fixed registration, unchanged material/rig/grade.
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();s.render.filepath=str(O/f'hero-{d}-4x.png');bpy.ops.render.render(write_still=True)
# Independent true native family fixtures, with canonical actual meshes/accents.
branches=[]
for label in ['W','N']:
 rr=bpy.data.objects.new('judge fixture middle '+label,None);s.collection.objects.link(rr);obs=[]
 for original in refs:
  ob=original.copy();ob.data=original.data;s.collection.objects.link(ob);ob.parent=rr;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=original.matrix_basis.copy();obs.append(ob)
 branches.append((rr,obs))
s.render.resolution_x=448*4;s.render.resolution_y=608*4;cam.data.ortho_scale=448/128;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(376*4-base.y)/dy;bpy.context.view_layer.update()
ledger=[]
for fixture in ['L','W','N']:
 for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
  root.rotation_euler.z=a;rot=Matrix.Rotation(a,4,'Z')
  for label,(rr,obs) in zip(['W','N'],branches):
   rr.location=rot@Vector((-1,0,0) if label=='W' else (0,1,0));rr.rotation_euler.z=a+(0 if label=='W' else math.pi/2)
   for ob in obs:ob.hide_render=fixture not in ['L',label]
  bpy.context.view_layer.update();s.render.filepath=str(O/f'family-{fixture}-{d}-4x.png');bpy.ops.render.render(write_still=True);ledger.append({'fixture':fixture,'direction':d,'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':list(px((0,0,0))),'filterSize':s.render.filter_size,'dimensions':[s.render.resolution_x,s.render.resolution_y]})
(P/'native-capture-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k not in ['rows','animation','materialAnimation']},indent=2));print('NATIVE JUDGE CAPTURES COMPLETE')
