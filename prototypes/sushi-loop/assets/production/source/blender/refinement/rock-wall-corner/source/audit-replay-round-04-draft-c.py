import bpy,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';R=B/'source/resources';bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-04.blend'));sc=bpy.context.scene;root=bpy.data.objects['rock-wall-corner__root'];coll=bpy.data.collections['rock-wall-corner__asset'];cam=sc.camera
P=[(-.5,0),(.5,0),(.5,.67),(.45,1.04),(.31,1.15),(-.31,1.15),(-.45,1.04),(-.5,.67)]
def dist(t,z):
 ds=[]
 for a,b in zip(P,P[1:]+P[:1]):
  dx,dz=b[0]-a[0],b[1]-a[1];d=dx*dx+dz*dz;q=max(0,min(1,((t-a[0])*dx+(z-a[1])*dz)/d));ds.append(math.hypot(t-a[0]-q*dx,z-a[1]-q*dz))
 return min(ds)
def mx(o):return [list(r) for r in o.matrix_world]
vs=[o.matrix_world@v.co for o in coll.objects if o.type=='MESH' for v in o.data.vertices];ports={}
for port in ['W','N']:
 pts=[]
 for o in coll.objects:
  if o.type!='MESH':continue
  edgeUse={}
  for poly in o.data.polygons:
   ids=list(poly.vertices)
   for a,b in zip(ids,ids[1:]+ids[:1]):
    key=tuple(sorted((a,b)));edgeUse[key]=edgeUse.get(key,0)+1
  outline=set(v for edge,n in edgeUse.items() if n==1 for v in edge)
  for vi in outline:
   v=o.data.vertices[vi];q=o.matrix_world@v.co
   if abs(q.x+.5)<1e-7 if port=='W' else abs(q.y-.5)<1e-7:pts.append((q.y if port=='W' else -q.x,q.z))
 ports[port]={'plane':-.5 if port=='W' else .5,'actualOpenMeshBoundarySamples':len(pts),'maxExposedBoundaryProfileDistance':max(dist(*p) for p in pts),'crown':max(p[1] for p in pts),'supportTransverseRange':[min(p[0] for p in pts if p[1]<1e-7),max(p[0] for p in pts if p[1]<1e-7)]}
# Compare actual stored roof/exterior exposed boundary attributes and split normals with measured construction reference.
intent=json.loads((O/'boundary-intent.json').read_text());errors=[]
for ob in coll.objects:
 if ob.type!='MESH' or 'connector' in ob.name or 'support' in ob.name:continue
 face='S' if '__S_' in ob.name else 'E' if '__E_' in ob.name else None
 norms={};portNorms={}
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   lp=ob.data.loops[li];n=Vector(ob.data.corner_normals[li].vector);norms.setdefault(lp.vertex_index,n)
   v=ob.data.vertices[lp.vertex_index].co
   for port in ['W','N']:
    on=lambda p:abs(p.x+.5)<1e-7 if port=='W' else abs(p.y-.5)<1e-7
    if on(v) and any(vi!=lp.vertex_index and on(ob.data.vertices[vi].co) for vi in poly.vertices):portNorms[(lp.vertex_index,port)]=n
 for p in intent:
  if p.get('meshFace')!=face:continue
  idx=p['index'];v=ob.data.vertices[idx].co;c=ob.data.color_attributes['stone_albedo'].data[idx].color;want=Vector(p['expectedNormal']);actual=portNorms.get((idx,p['port']),norms[idx])
  errors.append({'port':p['port'],'mesh':ob.name,'index':idx,'position':list(v),'albedoLinearMaxError':max(abs(c[k]-p['expectedColor'][k]) for k in range(4)),'normalVectorDelta':(actual-want).length,'normalAngleDegrees':math.degrees(math.acos(max(-1,min(1,actual.dot(want))))),'sharedNWConicalCorner':abs(v.x+.5)<1e-7 and abs(v.y-.5)<1e-7})
mat=next(o.data.materials[0] for o in coll.objects if o.type=='MESH');pr=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
report={'kind':'Actual reopened standalone source measurements; no source changes','sourceSHA256':hashlib.sha256((B/'source/round-04.blend').read_bytes()).hexdigest(),'boundMin':[min(v[i] for v in vs) for i in range(3)],'boundMax':[max(v[i] for v in vs) for i in range(3)],'ports':ports,'boundaryActualVsCanonical':{'samples':len(errors),'maxAlbedoLinearError':max(p['albedoLinearMaxError'] for p in errors),'maxNormalDelta':max(p['normalVectorDelta'] for p in errors),'maxNormalDeltaExcludingSingleSharedNWConicalPoint':max(p['normalVectorDelta'] for p in errors if not p['sharedNWConicalCorner']),'sharedNWPointTreatment':'Two native triangles carry split face-corner normals at the conical NW apex. Each edge limit is measured against its actual adjacent canonical port normal; no averaging across the two limiting port surfaces.'},'material':{'attribute':next(n.layer_name for n in mat.node_tree.nodes if n.type=='VERTEX_COLOR'),'roughness':pr.inputs['Roughness'].default_value,'specular':pr.inputs['Specular IOR Level'].default_value,'emission':pr.inputs['Emission Strength'].default_value,'imageNodes':sum(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes)},'sourceObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in sc.objects],'noCompanionMiddleSaved':not any(o.name.startswith('rock-wall-middle') for o in sc.objects),'resources':{'images':[{'name':i.name,'source':i.source,'path':i.filepath} for i in bpy.data.images if i.source!='VIEWER'],'libraries':[l.filepath for l in bpy.data.libraries]},'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'staticActions':len(bpy.data.actions),'engine':sc.render.engine,'samples':sc.cycles.samples,'filter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'denoise':sc.cycles.use_denoising,'seed':sc.cycles.seed,'rootMatrix':mx(root),'replayViews':{}}
(O/'boundary-residuals.json').write_text(json.dumps(errors,indent=2)+'\n')
D=O/'replay';D.mkdir(exist_ok=True)
for d,deg in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(D/f'native-static-{d}.png');bpy.ops.render.render(write_still=True);report['replayViews'][d]={'direction':d,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':mx(root),'path':f'candidates/round-04/replay/native-static-{d}.png'}
# Re-measure directly against actual immutable canonical mesh data, independent of editor-intent tables.
with bpy.data.libraries.load(str(R/'approved-middle/project.blend'),link=False) as (available,wanted):wanted.meshes=['rock-wall-middle__continuous_carved_stone']
canon=wanted.meshes[0];cnorm={}
for lp in canon.loops:cnorm.setdefault(lp.vertex_index,Vector(canon.corner_normals[lp.index].vector))
rings={}
for label,ix in [('W',0),('E',128)]:rings[label]=[{'yz':tuple(canon.vertices[ix*279+j].co[1:]),'color':tuple(canon.color_attributes['stone_albedo'].data[ix*279+j].color),'normal':cnorm[ix*279+j]} for j in range(279)]
def directsample(y,z,label):
 rr=rings[label];best=None
 for j in range(279):
  a,b=rr[j],rr[(j+1)%279];ay,az=a['yz'];by,bz=b['yz'];dy,dz=by-ay,bz-az;den=dy*dy+dz*dz;t=0 if den==0 else max(0,min(1,((y-ay)*dy+(z-az)*dz)/den));d=(y-ay-dy*t)**2+(z-az-dz*t)**2
  if best is None or d<best[0]:best=(d,a,b,t)
 _,a,b,t=best;c=tuple(a['color'][k]*(1-t)+b['color'][k]*t for k in range(4));n=(a['normal']*(1-t)+b['normal']*t).normalized();return c,n
actual=[]
for ob in coll.objects:
 if ob.type!='MESH' or 'unified_worn_stone' not in ob.name:continue
 byPort={}
 for poly in ob.data.polygons:
  for li in poly.loop_indices:
   lp=ob.data.loops[li];v=ob.data.vertices[lp.vertex_index].co
   for port in ['W','N']:
    on=lambda p:abs(p.x+.5)<1e-7 if port=='W' else abs(p.y-.5)<1e-7
    if on(v) and any(vi!=lp.vertex_index and on(ob.data.vertices[vi].co) for vi in poly.vertices):byPort[(lp.vertex_index,port)]=Vector(ob.data.corner_normals[li].vector)
 for (idx,port),n in byPort.items():
  v=ob.data.vertices[idx].co
  if v.z<1e-8 and abs(v.x+.5)<1e-7 and abs(v.y-.5)<1e-7:continue
  c,nn=directsample(v.y if port=='W' else -v.x,v.z,'E' if port=='W' else 'W')
  if port=='N':nn=Vector((-nn.y,nn.x,nn.z))
  cc=ob.data.color_attributes['stone_albedo'].data[idx].color
  actual.append({'port':port,'mesh':ob.name,'index':idx,'position':list(v),'albedoLinearMaxError':max(abs(cc[k]-c[k]) for k in range(4)),'normalVectorDelta':(n-nn).length,'profileDistance':dist(v.y if port=='W' else -v.x,v.z),'actualNormal':list(n),'canonicalNormal':list(nn)})
(O/'boundary-direct-canonical-residuals.json').write_text(json.dumps(actual,indent=2)+'\n')
report['boundaryEditorIntentSupplement']=report['boundaryActualVsCanonical']
report['boundaryActualVsCanonical']={'method':'Actual reopened candidate mesh positions/stone_albedo/stored boundary-adjacent loop normals compared directly to actual immutable canonical source mesh E ring and rotated W ring; editor intent tables are not comparison authority.','samples':len(actual),'maxAlbedoLinearError':max(p['albedoLinearMaxError'] for p in actual),'maxNormalDelta':max(p['normalVectorDelta'] for p in actual),'maxProfileDistance':max(p['profileDistance'] for p in actual),'raw':'candidates/round-04/boundary-direct-canonical-residuals.json','source':'source/resources/approved-middle/project.blend'}
(O/'saved-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('AUDIT_REPLAY_DONE')
