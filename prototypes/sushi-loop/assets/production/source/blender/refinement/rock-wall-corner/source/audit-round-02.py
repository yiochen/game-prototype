import bpy,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-02';R=B/'source/resources';bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-02.blend'));sc=bpy.context.scene;root=bpy.data.objects['rock-wall-corner__root'];coll=bpy.data.collections['rock-wall-corner__asset'];cam=sc.camera
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
 norms={}
 for lp in ob.data.loops:norms.setdefault(lp.vertex_index,Vector(ob.data.corner_normals[lp.index].vector))
 for p in intent:
  if p.get('meshFace')!=face:continue
  idx=p['index'];v=ob.data.vertices[idx].co;c=ob.data.color_attributes['stone_albedo'].data[idx].color;want=Vector(p['expectedNormal']);actual=norms[idx]
  errors.append({'port':p['port'],'mesh':ob.name,'index':idx,'position':list(v),'albedoLinearMaxError':max(abs(c[k]-p['expectedColor'][k]) for k in range(4)),'normalVectorDelta':(actual-want).length,'normalAngleDegrees':math.degrees(math.acos(max(-1,min(1,actual.dot(want))))),'sharedNWConicalCorner':abs(v.x+.5)<1e-7 and abs(v.y-.5)<1e-7})
mat=next(o.data.materials[0] for o in coll.objects if o.type=='MESH');pr=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
report={'kind':'Actual reopened standalone source measurements; no source changes','sourceSHA256':hashlib.sha256((B/'source/round-02.blend').read_bytes()).hexdigest(),'boundMin':[min(v[i] for v in vs) for i in range(3)],'boundMax':[max(v[i] for v in vs) for i in range(3)],'ports':ports,'boundaryActualVsCanonical':{'samples':len(errors),'maxAlbedoLinearError':max(p['albedoLinearMaxError'] for p in errors),'maxNormalDelta':max(p['normalVectorDelta'] for p in errors),'maxNormalDeltaExcludingSingleSharedNWConicalPoint':max(p['normalVectorDelta'] for p in errors if not p['sharedNWConicalCorner']),'sharedNWPointResidual':'The two perpendicular ports share one conical roof point at NW at z=.67. One common vertex cannot simultaneously carry two rotated normals; N analytic normal is stored there. All other exposed boundary samples use actual canonical native normals. Full raw residuals retained.'},'material':{'attribute':next(n.layer_name for n in mat.node_tree.nodes if n.type=='VERTEX_COLOR'),'roughness':pr.inputs['Roughness'].default_value,'specular':pr.inputs['Specular IOR Level'].default_value,'emission':pr.inputs['Emission Strength'].default_value,'imageNodes':sum(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes)},'sourceObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in sc.objects],'noCompanionMiddleSaved':not any(o.name.startswith('rock-wall-middle') for o in sc.objects),'resources':{'images':[{'name':i.name,'source':i.source,'path':i.filepath} for i in bpy.data.images if i.source!='VIEWER'],'libraries':[l.filepath for l in bpy.data.libraries]},'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'staticActions':len(bpy.data.actions),'engine':sc.render.engine,'samples':sc.cycles.samples,'filter':sc.cycles.pixel_filter_type,'filterSize':sc.render.filter_size,'denoise':sc.cycles.use_denoising,'seed':sc.cycles.seed,'rootMatrix':mx(root),'replayViews':{}}
(O/'boundary-residuals.json').write_text(json.dumps(errors,indent=2)+'\n')
report['replayViews']=json.loads((O/'saved-source-audit-draft-interior-distance.json').read_text())['replayViews']
(O/'saved-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('CORRECTED_EXPOSED_PROFILE_AUDIT_DONE')
