"""Wall outer corner round 01. Native L construction; approved family shaders and rig."""
import bpy, math, json, hashlib, shutil, bmesh
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];OUT=B/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
F=B.parent/'wall-middle';FAMILY=F/'source/round-06.blend'
SOURCE=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(FAMILY)=='13a7d057b1e0650582b60f4404ca1bb9b316774feb467c781730c7e43a25f723'
assert sha(B/'inputs/family-settings.json')=='690f0ee33c4ff18f02f4352fd91f326f0c42610e335c16a802222c4f216357ef'
original=json.loads((B/'source/source-inspection.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(FAMILY));scene=bpy.context.scene
template=bpy.data.collections['S33_PROP_wall-middle.001']
troot=next(o for o in template.all_objects if o.type=='EMPTY');troot.rotation_euler=(0,0,0);bpy.context.view_layer.update()
templates=[o for o in template.all_objects if o.type=='MESH']
template.hide_render=True;template.hide_viewport=True
collection=bpy.data.collections.new('Refined wall outer corner');scene.collection.children.link(collection)
root=bpy.data.objects.new('wall-outer-corner__root',None);collection.objects.link(root)
root['asset_id']='wall-outer-corner';root['ports']=json.dumps(json.loads((B/'inputs/source-assetRecord.json').read_text())['ports'])
# Copy family materials without changing BSDF, palette, radiance coefficients or parameters.
# Corner-native path coordinates replace unbent Object coordinates. On W/S cuts
# these coordinates equal the approved straight's exact corresponding coordinates.
materials={}
for o in templates:
 for m in o.data.materials:
  if m.name in materials:continue
  cm=m.copy();cm.name=m.name+' | convex corner coordinate'
  n=cm.node_tree.nodes;l=cm.node_tree.links
  for tc in list(n):
   if tc.type!='TEX_COORD':continue
   outgoing=[link for link in list(l) if link.from_node==tc and link.from_socket.name=='Object']
   if outgoing:
    attr=n.new('ShaderNodeAttribute');attr.attribute_name='family_coordinate';attr.name='Native corner path coordinates'
    for link in outgoing:l.new(attr.outputs['Vector'],link.to_socket)
  cm['family_source_material']=m.name;cm['changes']='Only coordinate source remapped to native longitudinal/transverse/height attribute.'
  materials[m.name]=cm
wood=next(m for name,m in materials.items()if name=='Warm wall · honey timber')
strip=next(m for name,m in materials.items()if name=='Warm wall · slender timber bead')
capwood=next(m for name,m in materials.items()if name=='Warm wall · cap undercut')
blue=next(m for name,m in materials.items()if name=='Warm wall · soft blue enamel')
# Mitered W/S path, softened only on the outside of the convex turn. The inner
# cut-out remains precisely the original clearance, and neither port extends.
A=.075
def bend(u,t):
 r=max(0,t)*.36
 if u < -A:
  q=(u+.5)/(.5-A);e=q*q*(3-2*q)
  return u+(t-r+A)*e,t
 if u > A:
  q=(.5-u)/(.5-A);e=q*q*(3-2*q)
  return t,-u+(t-r+A)*e
 theta=math.pi/2-(u+A)/(2*A)*math.pi/2
 return t-r+r*math.cos(theta),t-r+r*math.sin(theta)
def angle(u):
 return 0 if u<=-A else math.pi/2 if u>=A else (u+A)/(2*A)*math.pi/2

def extrusion(name,profile,material,kind):
 dense=[]
 if kind in ('bead','woodcap'):
  for a,b in zip(profile,profile[1:]+profile[:1]):
   av=Vector(a);bv=Vector(b);f=min(.22,.006/(bv-av).length)
   for t in (0,f,1-f):dense.append(tuple(av.lerp(bv,t)))
  profile=dense
 # More samples on the real corner than on the broad straight sections.
 us=sorted(set([-.5+i/64 for i in range(65)]+[-A+i*(2*A)/16 for i in range(17)]+[-A,A,0]))
 count=len(profile);verts=[];coords=[];normal_specs=[]
 # Analytical profile normal, as used by the approved straight beads/cap.
 profile_ns=[]
 for j,(t,z) in enumerate(profile):
  a=Vector((t,z))-Vector(profile[j-1]);b=Vector(profile[(j+1)%count])-Vector((t,z))
  profile_ns.append((Vector((a.y,-a.x)).normalized()+Vector((b.y,-b.x)).normalized()).normalized())
 for u in us:
  for j,(t,z)in enumerate(profile):
   tt,zz=t,z
   effective_u=0 if t<=0 and abs(u)<=A else u
   if kind=='panel':
    for low,high in[(.07,.12),(.145,.34),(.365,.56),(.585,.78),(.805,.89)]:
     if low<z<high:tt+=math.copysign(.017*math.sin(math.pi*(z-low)/(high-low))**2*math.cos(math.pi*effective_u)**2,t)
   if kind=='blue' and abs(z-1.01)<1e-5:
    zz+=.008*math.cos(math.pi*effective_u)**2*max(0,1-(abs(t)/.12)**4)
   x,y=bend(u,tt);verts.append((x,y,zz));coords.append((effective_u,t,z));normal_specs.append((u,j))
 faces=[]
 for k in range(len(us)-1):
  for j in range(count):
   f=(k*count+j,k*count+(j+1)%count,(k+1)*count+(j+1)%count,(k+1)*count+j)
   ps=[Vector(verts[i])for i in f]
   if (ps[1]-ps[0]).cross(ps[2]-ps[0]).length+(ps[2]-ps[0]).cross(ps[3]-ps[0]).length>1e-11:faces.append(f)
 # Weld collapsed inner-turn samples into actual continuous native topology.
 # Identical points use identical path coordinates there. Preserve custom loop
 # treatment after welding; no render geometry extension or image correction.
 vnew=[];cnew=[];nnew=[];remap={};canonical={}
 for i,v in enumerate(verts):
  key=tuple(round(k,7)for k in v)
  if key not in canonical:
   canonical[key]=len(vnew);vnew.append(v);cnew.append(coords[i]);nnew.append(normal_specs[i])
  remap[i]=canonical[key]
 fnew=[]
 for f in faces:
  f2=[]
  for i in f:
   j=remap[i]
   if not f2 or f2[-1]!=j:f2.append(j)
  if len(f2)>1 and f2[0]==f2[-1]:f2.pop()
  if len(set(f2))>=3:fnew.append(tuple(f2))
 verts,coords,normal_specs,faces=vnew,cnew,nnew,fnew
 mesh=bpy.data.meshes.new(name+' native continuous bend surface');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('wall-outer-corner__'+name,mesh);collection.objects.link(o);o.parent=root;o.data.materials.append(material)
 attr=mesh.attributes.new('family_coordinate','FLOAT_VECTOR','POINT')
 for a,v in zip(attr.data,coords):a.vector=v
 for p in mesh.polygons:p.use_smooth=True
 # Smooth evaluated normals for relief, analytically constrained source end normals.
 # Flat top-facing normals eliminate triangulation scars without a shader overlay.
 mesh.update();ns=[]
 for loop,corner in zip(mesh.loops,mesh.corner_normals):
  u,j=normal_specs[loop.vertex_index];t,z=profile[j]
  no=Vector(corner.vector)
  if kind in('bead','woodcap'):
   ny,nz=profile_ns[j];th=(math.pi/4 if t<=0 and abs(u)<=A else angle(u));no=Vector((ny*math.sin(th),ny*math.cos(th),nz))
  if kind=='blue':
   # Top broad plane keeps real shallow crown normals; boundary lateral facets
   # use the geometric profile instead of averaging across an L triangulation.
   if z<1.009 or abs(t)>=.119:
    ny,nz=profile_ns[j];th=(math.pi/4 if t<=0 and abs(u)<=A else angle(u));no=Vector((ny*math.sin(th),ny*math.cos(th),nz))
   elif abs(t)<.119:
    no=Vector((0,0,1))
  if abs(abs(u)-.5)<1e-6:
   # Profile tangent for the panel matches the approved straight's ends.
   if u<0:no.x=0
   else:no.y=0
  if no.length:no.normalize()
  ns.append(no)
 mesh.normals_split_custom_set(ns)
 o['construction']='Continuous native convex W/S bend. Exact source terminal rings; outside-only turn rounding; source inside clearance retained.'
 return o
zs=sorted(set(round(z,6)for z in[.07,.89,.145,.34,.365,.56,.585,.78,.805]+[.07+i*.82/64 for i in range(65)]))
profile=list(reversed([(-.105,z)for z in zs]+[(.105,z)for z in reversed(zs)]))
extrusion('wall_panel',profile,wood,'panel')
for i,z in enumerate((.12,.34,.56,.78)):
 extrusion('horizontal_board_'+str(i),[(-.115,z),(.115,z),(.115,z+.025),(-.115,z+.025)],strip,'bead')
extrusion('wood_cap',[(-.15,.86),(.15,.86),(.15,.935),(-.15,.935)],capwood,'woodcap')
profile=[(-.18,.93),(.18,.93),(.18,.97),(.12,1.01)]+[(y,1.01)for y in[.09,.06,.03,0,-.03,-.06,-.09]]+[(-.12,1.01),(-.18,.97)]
extrusion('blue_coping',profile,blue,'blue')
# Exact source terminal closures are rebuilt from original corner polygons.
for part in original['objects']:
 key=part['name'].split('__')[1].replace('.001','')
 ref=next(o for o in templates if '__'+key+'__camera_cut_planes' in o.name)
 verts=[];faces=[];coords=[]
 sv=part['vertices']
 for f in part['faces']:
  isW=all(abs(sv[i][0]+.5)<1e-6 for i in f)
  isS=all(abs(sv[i][1]+.5)<1e-6 for i in f)
  if not(isW or isS):continue
  start=len(verts)
  for i in f:
   x,y,z=sv[i];verts.append((x,y,z));coords.append((-.5,y,z)if isW else(.5,x,z))
  faces.append(tuple(range(start,len(verts))))
 mesh=bpy.data.meshes.new(key+' source terminal cuts');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('wall-outer-corner__'+key+'__camera_cut_planes',mesh);collection.objects.link(o);o.parent=root;o.data.materials.append(materials[ref.data.materials[0].name])
 attr=mesh.attributes.new('family_coordinate','FLOAT_VECTOR','POINT')
 for a,v in zip(attr.data,coords):a.vector=v
 o['purpose']='Original exact W/S cut faces, approved camera cut material/radiance; no secondary-ray closure shadow.'
cam=scene.camera;camrec=json.loads((B/'inputs/source-camera.json').read_text())
cam.matrix_world=Matrix(camrec['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL'
def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y))
def register(width,height,rootpixel):
 scene.render.resolution_x=width;scene.render.resolution_y=height;cam.data.ortho_scale=width/256;cam.data.shift_y=0;bpy.context.view_layer.update();base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-base.y;cam.data.shift_y=(rootpixel[1]-base.y)/dy;bpy.context.view_layer.update()
register(384,704,(192,512))
# All capture settings, lights, world and base materials are exact approved family.
scene['asset_id']='wall-outer-corner';scene['round']='round-03';scene['family']='restaurant-wall-wood-blue-v2'
scene.render.fps=12
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU'
def rows(m):return[list(r)for r in m]
def bounds(objects):
 dg=bpy.context.evaluated_depsgraph_get();pts=[o.matrix_world@v.co for o in objects if o.type=='MESH'for v in o.evaluated_get(dg).data.vertices]
 return [[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
root.rotation_euler.z=0;bpy.context.view_layer.update()
localbounds=bounds(collection.all_objects)
# Compare source-profile polygon per part; arbitrary collinear refinement is legal.
checks=[];sections={}
for side,axis in[('W',0),('S',1)]:
 sections[side]={}
 for part in original['objects']:
  key=part['name'].split('__')[1].replace('.001','');obj=next(o for o in collection.all_objects if o.name=='wall-outer-corner__'+key)
  trans=1-axis
  actual=sorted(set((round(v.co[trans],7),round(v.co.z,7))for v in obj.data.vertices if abs(v.co[axis]+.5)<1e-6))
  sv=part['vertices'];segments=[];sourcepoints=set()
  for f in part['faces']:
   if all(abs(sv[i][axis]+.5)<1e-6 for i in f):
    for a,b in zip(f,f[1:]+f[:1]):
     pa=Vector((sv[a][trans],sv[a][2]));pb=Vector((sv[b][trans],sv[b][2]));segments.append((pa,pb));sourcepoints.add(tuple(pa))
  def dist(p):
   p=Vector(p);ds=[]
   for a,b in segments:
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared))if d.length_squared else 0;ds.append((p-a-t*d).length)
   return min(ds)
  error=max(dist(p)for p in actual);contains=all(min((Vector(p)-Vector(q)).length for q in actual)<1e-6 for p in sourcepoints)
  checks.append({'port':side,'part':key,'sourcePoints':[list(v)for v in sorted(sourcepoints)],'currentPointCount':len(actual),'maxDistanceToSourceProfile':error,'containsEverySourceCorner':contains,'passed':error<1e-6 and contains});sections[side][key]=actual
assert all(v['passed']for v in checks),checks
assert localbounds[0][0]>=-.500001 and localbounds[1][0]>=-.500001 and localbounds[0][1]<=.180001 and localbounds[1][1]<=.180001 and localbounds[2][1]<=1.020001,localbounds
cal={k:list(pixel(v))for k,v in{'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()}
cal={k:(p if k=='root'else[p[i]-cal['root'][i]for i in range(2)])for k,p in cal.items()}
bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/round-03.blend'),check_existing=False)
records=[];directions=[('N',180),('E',90),('S',0),('W',-90)]
for direction,degrees in directions:
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update()
 path=OUT/'raw'/('static-'+direction+'-0000.png');path.parent.mkdir(exist_ok=True)
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'kind':'single','clip':'static','direction':direction,'index':0,'path':str(path.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'cameraWorldMatrix':rows(cam.matrix_world),'resolution':[384,704],'rootPixel':list(pixel((0,0,0))),'bounds':bounds(collection.all_objects)})
 for joined in [('W',),('S',),('W','S')]:
  copies=[];placements=[]
  rot=Matrix.Rotation(math.radians(degrees),4,'Z')
  for port in joined:
   localpos=Vector((-1,0,0)if port=='W'else(0,-1,0));localrot=0 if port=='W'else math.pi/2
   placement=rot@Matrix.Translation(localpos)@Matrix.Rotation(localrot,4,'Z')
   placements.append({'port':port,'localPosition':list(localpos),'relativeStraightRotationDegrees':math.degrees(localrot),'worldMatrix':rows(placement),'straightFacingDegrees':degrees+math.degrees(localrot)})
   for o in templates:
    dup=o.copy();dup.data=o.data;dup.parent=None;dup.hide_render=False;dup.hide_viewport=False;dup.matrix_world=placement@o.matrix_world;scene.collection.objects.link(dup);copies.append(dup)
  register(896,1216,(448,768));p=OUT/'native-joins'/('static-'+direction+'-'+''.join(joined)+'.png');p.parent.mkdir(exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  records.append({'kind':'native-join','direction':direction,'ports':list(joined),'path':str(p.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'placements':placements,'resolution':[896,1216],'rootPixel':list(pixel((0,0,0))),'cameraWorldMatrix':rows(cam.matrix_world),'pixelPitch':256,'joinPlanesLocal':{'W':'x=-.5','S':'y=-.5'}})
  for o in copies:bpy.data.objects.remove(o,do_unlink=True)
  register(384,704,(192,512))
root.rotation_euler.z=0;bpy.context.view_layer.update()
topology=[]
for o in collection.all_objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 topology.append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'edges':len(o.data.edges),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-11 for f in bm.faces),'modifiers':[m.type for m in o.modifiers]});bm.free()
validation={'asset':'wall-outer-corner','round':'round-03','blender':bpy.app.version_string,'source':{'path':str(SOURCE),'sha256':sha(SOURCE),'unchanged':sha(SOURCE)=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','collection':original['collection'],'originalMeshes':original['objects']},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'sourceRecordedCaptureScale':4,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'worldMatrix':rows(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1))},'calibration':cal,'actualRoot':root.name,'rootMatrix':rows(root.matrix_world),'footprint':[1,1],'functionalHeight':1.02,'boundsLocal':localbounds,'ports':json.loads(root['ports']),'facings':{'S':0,'E':90,'N':180,'W':-90}},'geometry':{'selectedObjectOnly':True,'meshCount':len(topology),'topology':topology,'boundaryChecks':checks,'boundarySections':sections,'insideClearance':'Original concave negative-transverse miter retained; only positive-transverse outside turn is rounded. Maximum .017 shallow relief between source beads, tapering exactly to zero at both ports.','construction':'Native continuous W/S L surfaces; outside turning radius=.36*positive transverse distance; shallow native coping crown <=1.018; source terminal closure polygons unchanged. No extension outside ports/envelope.','intentionalBoundaryEdges':'Modular extrusions intentionally open with separate camera cut closures; collapsed inner-turn station coordinates preserve a sharp concave miter with no occupied clearance change.'},'family':{'settingsPath':'inputs/family-settings.json','settingsSHA256':sha(B/'inputs/family-settings.json'),'sourcePath':str(FAMILY),'sourceSHA256':sha(FAMILY),'materials':'Copied approved materials unchanged except native family_coordinate attribute replacing unbent Object coordinates. The attribute is longitudinal/transverse/height and exactly matches family coordinates at W/S cuts. Base BSDF/radiance coefficients and palette unaltered.','straightTemplates':'Saved hidden approved straight collection, source bound in dependencies; copies rendered with unchanged native family materials.'},'render':{'engine':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'denoise':scene.cycles.use_denoising,'filter':scene.cycles.pixel_filter_type,'filterSize':scene.render.filter_size,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'horizontalSymmetry':4,'noGroundReceiver':True,'perViewChanges':'Common root rotation only; joined previews expand canvas without changing 256px/unit pitch. Approved world/light/material configuration reused.'},'renders':records,'dependencies':{'externalImages':[{'name':i.name,'path':i.filepath}for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'selfContained':not bpy.data.libraries and not any(i.source=='FILE'for i in bpy.data.images)},'status':'candidate-awaiting-independent-judge'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
(OUT/'native-camera.json').write_text(json.dumps({**camrec,'captureScale':2,'calibration':cal,'camera':{**camrec['camera'],**validation['capture']['camera']}},indent=2))
asset=json.loads((B/'inputs/source-assetRecord.json').read_text());asset['scale']=2;(OUT/'native-assetRecord.json').write_text(json.dumps(asset,indent=2));shutil.copy2(B/'inputs/source-rig.json',OUT/'native-rig.json')
print('OUTER CORNER ROUND COMPLETE',OUT)

