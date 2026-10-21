"""Wall-inner-corner native warm-family reconstruction, immutable round 01.
Uses approved wall-middle round06 exact material/light/capture and cut profiles.
Continuous swept L construction; no connector extension or painted output.
"""
import bpy,math,json,hashlib,shutil,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];F=B.parent/'wall-middle';OUT=B/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
D=json.loads((B/'inputs/family-settings.json').read_text());FAMILY=F/D['project']['path']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(FAMILY)==D['project']['sha256'];assert sha(B/'inputs/family-settings.json')=='690f0ee33c4ff18f02f4352fd91f326f0c42610e335c16a802222c4f216357ef'
bpy.ops.wm.open_mainfile(filepath=str(FAMILY));scene=bpy.context.scene;cam=scene.camera
family_col=next(c for c in bpy.data.collections if 'wall-middle' in c.name);family_root=next(o for o in family_col.all_objects if o.type=='EMPTY')
family_root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
# Data-only profile/normal/material references; images and external libraries absent.
parts={}
for o in family_col.all_objects:
 if o.type!='MESH':continue
 key=o.name.split('__')[1];cut='camera_cut_planes' in o.name
 if cut:continue
 cnt=sum(abs(v.co.x+.5)<1e-6 for v in o.data.vertices);profile=[tuple(v.co[1:])for v in o.data.vertices[:cnt]]
 assert len(profile)==cnt
 normals={}
 for loop,cn in zip(o.data.loops,o.data.corner_normals):
  vi=loop.vertex_index
  if vi<cnt:normals.setdefault(vi,[]).append(Vector(cn.vector))
 ns=[sum(normals[i],Vector()).normalized()for i in range(cnt)]
 cutobj=next(q for q in family_col.all_objects if q.name==o.name+'__camera_cut_planes')
 cv=[tuple(v.co)for v in cutobj.data.vertices];cf=[list(p.vertices)for p in cutobj.data.polygons if all(abs(cv[i][0]+.5)<1e-6 for i in p.vertices)]
 parts[key]={'profile':profile,'normals':ns,'material':o.data.materials[0],'cutMaterial':cutobj.data.materials[0],'cutVerts':cv,'cutFaces':cf}
# Native source rig/root comes from locked source records, not the straight model.
original=json.loads((B/'candidates/inspection/source.json').read_text())
for o in list(family_col.all_objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(family_col)
c=bpy.data.collections.new('S33_PROP_wall-inner-corner_refined');scene.collection.children.link(c)
root=bpy.data.objects.new('wall-inner-corner__root',None);c.objects.link(root)
root['asset_id']='wall-inner-corner';root['ports']=json.dumps(json.loads((B/'inputs/source-assetRecord.json').read_text())['ports']);root['footprint']=json.dumps([1,1]);root['height']=1.02
# Shared broad wood grain is evaluated along the bent board's longitudinal path.
# min(X,-Y) is X at the W cut and -Y at the N cut. Both are -.5, exactly the
# shared periodic end phase. Smooth structure only; no per-facing changes.
wood_mats={}
def wood_map(mat):
 if mat.name in wood_mats:return wood_mats[mat.name]
 if not any(n.type=='TEX_COORD'for n in mat.node_tree.nodes):wood_mats[mat.name]=mat;return mat
 m=mat.copy();m.name=mat.name+' corner longitudinal mapping';n=m.node_tree.nodes;l=m.node_tree.links
 tc=next(v for v in n if v.type=='TEX_COORD');sep=next(v for v in n if v.type=='SEPXYZ')
 xy=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],xy.inputs[0]);neg=n.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-1;l.new(xy.outputs['Y'],neg.inputs[0]);mn=n.new('ShaderNodeMath');mn.operation='MINIMUM';l.new(xy.outputs['X'],mn.inputs[0]);l.new(neg.outputs[0],mn.inputs[1]);vec=n.new('ShaderNodeCombineXYZ');l.new(mn.outputs[0],vec.inputs['X']);l.new(xy.outputs['Y'],vec.inputs['Y']);l.new(xy.outputs['Z'],vec.inputs['Z']);l.new(vec.outputs[0],sep.inputs[0]);wood_mats[mat.name]=m;return m
intervals=[(.07,.12),(.145,.34),(.365,.56),(.585,.78),(.805,.89)]
# One sweep grid with tangent outer-elbow rounding. For positive transverse
# depths the turn stays sharp, retaining the original concave opening.
NST=24;ARC=12
stations=[('w',i/NST)for i in range(NST+1)]+[('a',i/ARC)for i in range(1,ARC+1)]+[('n',i/NST)for i in range(1,NST+1)]
def point(mode,t,v,z,h,key):
 r=(.028 if key=='blue_coping'else .017 if key=='wood_cap'else .010)*max(0,min(1,(h-v)/(2*h)))
 bx=-v-r;by=v+r
 if mode=='w':x=-.5+(bx+.5)*t;y=v;u=.5*t;angle=0
 elif mode=='a':angle=t*math.pi/2;x=bx+r*math.sin(angle);y=by-r*math.cos(angle);u=.5
 else:x=-v;y=by+(.5-by)*t;u=.5+.5*t;angle=math.pi/2
 # Profile relief vanishes smoothly on both exact cut planes.
 fade=math.sin(math.pi*u)**2
 if key=='wall_panel':
  relief=0
  for lo,hi in intervals:
   if lo<z<hi:relief=.017*math.sin(math.pi*(z-lo)/(hi-lo))**2
  off=math.copysign(relief*fade,v);x-=math.sin(angle)*off;y+=math.cos(angle)*off
 if key=='blue_coping' and abs(z-1.01)<1e-5:
  z+=.008*fade*max(0,1-(abs(v)/.12)**4)
 return (x,y,z),angle
reports=[]
for key,part in parts.items():
 profile=part['profile'];cnt=len(profile);h=max(abs(v)for v,z in profile);verts=[];angles=[]
 for mode,t in stations:
  for v,z in profile:
   p,a=point(mode,t,v,z,h,key);verts.append(p);angles.append(a)
 faces=[]
 for k in range(len(stations)-1):
  for j in range(cnt):
   f=(k*cnt+j,k*cnt+(j+1)%cnt,(k+1)*cnt+(j+1)%cnt,(k+1)*cnt+j)
   p0,p1,p2,p3=[Vector(verts[i])for i in f]
   if (p1-p0).cross(p2-p0).length+(p2-p0).cross(p3-p0).length>1e-13:faces.append(f)
 me=bpy.data.meshes.new(key+' continuous bent native surface');me.from_pydata(verts,[],faces);me.update()
 o=bpy.data.objects.new('wall-inner-corner__'+key,me);c.objects.link(o);o.parent=root;me.materials.append(wood_map(part['material']))
 for p in me.polygons:p.use_smooth=True
 # Native analytical cross-section normals exactly match the approved family
 # on every cut. Face relief elsewhere uses measured mesh normals.
 normal_values=[]
 for loop,cn in zip(me.loops,me.corner_normals):
  vi=loop.vertex_index;station=vi//cnt;j=vi%cnt
  if key=='wall_panel' and station not in [0,len(stations)-1]:no=Vector(cn.vector)
  else:
   base=part['normals'][j];a=angles[vi];no=Vector((-math.sin(a)*base.y,math.cos(a)*base.y,base.z)).normalized()
  normal_values.append(no)
 me.normals_split_custom_set(normal_values)
 o['construction']='Native continuous profile sweep, exact unextended W/N cut planes, tangent outside elbow, original concave opening'
 # One camera cut closure per connector. The N blue field uses X transverse
 # instead of Y; the same shared q^0..q^4 radiance coefficients are unchanged.
 for port in ['W','N']:
  cv=[];cf=[]
  for face in part['cutFaces']:
   start=len(cv)
   for vi in face:
    x,y,z=part['cutVerts'][vi];cv.append((-.5,y,z)if port=='W'else(-y,.5,z))
   cf.append(tuple(range(start,len(cv))))
  cutme=bpy.data.meshes.new(key+' '+port+' exact cut');cutme.from_pydata(cv,[],cf);cutme.update();cut=bpy.data.objects.new('wall-inner-corner__'+key+'__cut_'+port,cutme);c.objects.link(cut);cut.parent=root
  cm=wood_map(part['cutMaterial'])
  if key=='blue_coping' and port=='N':
   cm=cm.copy();cm.name+=' N transverse X'
   sep=next(n for n in cm.node_tree.nodes if n.type=='SEPXYZ')
   for link in list(cm.node_tree.links):
    if link.from_node==sep and link.from_socket==sep.outputs['Y']:
     dest=link.to_socket;cm.node_tree.links.remove(link);cm.node_tree.links.new(sep.outputs['X'],dest)
  cutme.materials.append(cm);cut['purpose']='Exact source cut; approved native family ray/material treatment; no geometric extension'
 # All source end profile coordinates must remain present in body section.
 checks={}
 for port in ['W','N']:
  current=[(v.co.y,v.co.z)if port=='W'else(-v.co.x,v.co.z)for v in me.vertices if abs((v.co.x+.5)if port=='W'else(v.co.y-.5))<1e-6]
  maxerr=max(min((Vector(p)-Vector(q)).length for q in current)for p in profile)
  checks[port]={'sourceProfileVertices':len(profile),'currentCutVertices':len(current),'maximumSourceVertexDistance':maxerr,'passed':maxerr<1e-6}
  assert maxerr<1e-6
 reports.append({'part':key,'profileCount':cnt,'vertices':len(verts),'faces':len(faces),'ports':checks})
# All family datablocks now used are native and internal. Remove unused originals.
for im in list(bpy.data.images):bpy.data.images.remove(im)
bpy.data.orphans_purge(do_recursive=True)
scene.name='Wall inner corner warm family round01';scene['asset_id']='wall-inner-corner';scene['round']='round-01';scene['family']='restaurant-wall-wood-blue-v2'
# Ensure exactly approved real camera matrix, not a list masquerading as a matrix.
cam.matrix_world=Matrix(D['capture']['camera']['worldMatrix']);cam.data.ortho_scale=D['capture']['camera']['orthoScale'];cam.data.shift_x=0;cam.data.shift_y=D['capture']['camera']['shift'][1]
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=dev.type=='METAL'
scene.cycles.device='GPU';root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def rows(m):return[list(r)for r in m]
def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y))
def register(w,h,anchor):
 scene.render.resolution_x=w;scene.render.resolution_y=h;cam.data.ortho_scale=w/256;cam.data.shift_y=0;bpy.context.view_layer.update();p=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-p.y;cam.data.shift_y=(anchor[1]-p.y)/dy;bpy.context.view_layer.update()
def bounds(col):
 dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in col.all_objects:
  if o.type=='MESH':
   ev=o.evaluated_get(dg);me=ev.to_mesh();pts += [ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 return[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
register(384,704,(192,512));initial_bounds=bounds(c)
cal={k:list(pixel(v))for k,v in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()};cal={k:(p if k=='root'else[p[i]-cal['root'][i]for i in range(2)])for k,p in cal.items()}
project=B/'source/round-01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project),check_existing=False)
# Store the exact approved straight model as immutable evidence dependency.
dep=OUT/'dependencies/family-straight.blend';dep.parent.mkdir(exist_ok=True);shutil.copy2(FAMILY,dep);shutil.copy2(B/'inputs/family-settings.json',OUT/'family-settings.json')
# Append straight family geometry only after saving the standalone candidate.
with bpy.data.libraries.load(str(dep),link=False)as(df,dt):dt.collections=[n for n in df.collections if 'wall-middle' in n]
straight=dt.collections[0];scene.collection.children.link(straight);straight.hide_render=True;straight.hide_viewport=False
sroot=next(o for o in straight.all_objects if o.type=='EMPTY');sroot.rotation_euler=(0,0,0);bpy.context.view_layer.update()
records=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();register(384,704,(192,512));p=OUT/'raw'/('static-'+direction+'-0000.png');p.parent.mkdir(exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 rec={'kind':'single','clip':'static','direction':direction,'index':0,'path':str(p.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'cameraWorldMatrix':rows(cam.matrix_world),'rootPixel':list(pixel((0,0,0))),'bounds':bounds(c)};records.append(rec)
 # Every facing receives two real straight neighbors: W canonical S and N
 # canonical E. Apply whole-assembly rotation around the authored corner root.
 copies=[];placements=[];rot=Matrix.Rotation(math.radians(degrees),4,'Z')
 for port,loc,turn in [('W',(-1,0,0),0),('N',(0,1,0),90)]:
  trans=rot@Matrix.Translation(Vector(loc))@Matrix.Rotation(math.radians(turn),4,'Z');placements.append({'port':port,'canonicalPosition':loc,'canonicalDegrees':turn,'worldMatrix':rows(trans),'straightFacing':{0:'S',90:'E',180:'N',270:'W'}[(turn+degrees)%360]})
  for o in straight.all_objects:
   if o.type!='MESH':continue
   dup=o.copy();dup.data=o.data;dup.parent=None;dup.matrix_world=trans@o.matrix_world;scene.collection.objects.link(dup);copies.append(dup)
 register(896,1216,(448,768));p=OUT/'native-joins'/('static-'+direction+'-both-ports.png');p.parent.mkdir(exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 records.append({'kind':'native-join','direction':direction,'path':str(p.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'cameraWorldMatrix':rows(cam.matrix_world),'resolution':[896,1216],'rootPixel':list(pixel((0,0,0))),'placements':placements,'pixelPitch':256,'portsCovered':['W','N']})
 if direction=='S':bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/round-01-join-context.blend'),check_existing=False)
 for o in copies:bpy.data.objects.remove(o,do_unlink=True)
root.rotation_euler.z=0;bpy.context.view_layer.update();register(384,704,(192,512))
validation={'asset':'wall-inner-corner','round':'round-01','blender':bpy.app.version_string,'projectSha256':sha(project),'source':{'path':original['source'],'sha256':original['sha256'],'unchanged':sha(original['source'])==original['sha256'],'selectedCollection':c.name},'family':{'settings':str((OUT/'family-settings.json').relative_to(B)),'settingsSha256':sha(OUT/'family-settings.json'),'approvedProjectSha256':sha(dep),'approvedPacketSha256':'8330022d2b5db61306810839b47782f8da317f7e77543f950016e2b80e7bae46','materialPolicy':'Exact approved material datablocks; wood Object coordinate longitudinal bend mapping only; N blue cut field changes transverse Y to X, exact common coefficients unchanged.','captureLightingRender':'Exact approved family scene world, lights, camera, Cycles512 Metal, box filter1, AgX Medium High Contrast exposure.35; no denoise, no ground receiver'},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'cellSize':128,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'worldMatrix':rows(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1))},'calibration':cal,'actualRoot':root.name,'facings':D['capture']['facingDegrees'],'footprint':[1,1],'functionalHeight':1.02,'boundsLocal':initial_bounds,'ports':json.loads(root['ports'])},'geometry':{'parts':reports,'selectedObjectOnly':True,'construction':'Seven continuous swept native L bands. Tangent rounded outside elbow. Broad timber face relief and gently crowned coping vanish at exact source join profiles. Sharp concave L boundary retained at source widths.','noConnectorExtension':True,'sourceEndProfilesPreserved':True,'envelopeWithinOneCell':initial_bounds[0][0]>=-.500001 and initial_bounds[1][1]<=.500001 and initial_bounds[2][1]<=1.020001},'render':D['render'],'renders':records,'dependencies':{'externalImages':[],'linkedLibraries':[],'selfContained':True,'nativeAssemblyDependency':{'path':str(dep.relative_to(B)),'sha256':sha(dep)}} ,'status':'candidate-awaiting-independent-judge'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
camrec=json.loads((B/'inputs/source-camera.json').read_text());camrec['captureScale']=2;camrec['camera'].update(validation['capture']['camera']);camrec['calibration']=cal;(OUT/'native-camera.json').write_text(json.dumps(camrec,indent=2))
a=json.loads((B/'inputs/source-assetRecord.json').read_text());a['scale']=2;(OUT/'native-assetRecord.json').write_text(json.dumps(a,indent=2));rig=json.loads((B/'inputs/source-rig.json').read_text());rig['groundRootObject']=root.name;(OUT/'native-rig.json').write_text(json.dumps(rig,indent=2))
print('COMPLETE',OUT)
