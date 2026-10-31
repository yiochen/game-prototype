"""Rebuild the authorized slate source into a native three-boulder rockery.
No reference image is loaded into Blender. Original camera and five lights remain exact.
Run: blender --background --threads 4 --python source/build-draft-01.py
"""
import bpy,bmesh,hashlib,json,math,random
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'candidates/draft-01';OUT.mkdir(parents=True,exist_ok=True)
PROJECT=BASE/'source/draft-01.blend'
BRIEF=json.loads((BASE/'brief.json').read_text())
assert BRIEF['qualityCriteria']
SOURCE=Path(BRIEF['source']['project'])
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE)==BRIEF['source']['projectSHA256']
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
oldroot=bpy.data.objects['slate-rock__root.001']
root=oldroot;root.name='perimeter-rockery__root';root.rotation_euler=(0,0,0)
originalCamera={'matrixWorld':[list(r) for r in scene.camera.matrix_world],'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y],'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]}
originalLights=[{'name':o.name,'matrixWorld':[list(r) for r in o.matrix_world],'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in scene.objects if o.type=='LIGHT']
for o in list(scene.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
collection=next(c for c in root.users_collection)
collection.name='PERIMETER_ROCKERY_NATIVE'

def mat(name,color,rough=.87):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.18
 m.diffuse_color=(*color,1)
 return m

# Fixed face palette in linear RGB. Diffuse faceted volume supplies the larger value shifts.
rocks=[mat('Slate violet large plane %02d'%i,c) for i,c in enumerate([
 (.105,.124,.225),(.120,.140,.250),(.134,.148,.267),(.112,.130,.236),
 (.158,.174,.300),(.143,.159,.278),(.126,.145,.259),(.172,.185,.310)])]
leafm=[mat('Crevice foliage folded face %02d'%i,c,.73) for i,c in enumerate([
 (.095,.370,.019),(.185,.490,.029),(.043,.245,.018),(.070,.320,.022),(.240,.550,.040),(.032,.205,.023)])]

def mesh(name,verts,faces,materials):
 me=bpy.data.meshes.new(name+'__mesh');me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);collection.objects.link(ob);ob.parent=root
 for m in materials:me.materials.append(m)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 return ob

def boulder(name,center,rx,ry,h,phase,seed):
 rng=random.Random(seed);n=8
 # Offset uneven octagonal shoulders, quieter broad sides and an asymmetric crown.
 angles=[phase+2*math.pi*i/n+rng.uniform(-.07,.07) for i in range(n)]
 radii=[rng.uniform(.91,1.04) for i in range(n)]
 # Normalized radial profile remains inside declared per-boulder design bounds.
 xy=[(math.cos(a)*r,math.sin(a)*r) for a,r in zip(angles,radii)]
 mx=max(abs(x) for x,y in xy);my=max(abs(y) for x,y in xy)
 xy=[(x/mx,y/my) for x,y in xy]
 verts=[]
 for layer,(scale,z) in enumerate([(.87,0),(1,.29),(.94,.72),(.69,.92)]):
  for i,(x,y) in enumerate(xy):
   zz=0 if layer==0 else h*(z+rng.uniform(-.035,.035))
   # Slightly shifted crown avoids identical nested rings.
   dx=(.045*rx if layer==3 else 0);dy=(-.065*ry if layer==3 else 0)
   verts.append((center[0]+rx*x*scale+dx,center[1]+ry*y*scale+dy,zz))
 faces=[tuple(reversed(range(n)))]
 for layer in range(3):
  for i in range(n):
   j=(i+1)%n
   # One long side is deliberately broken into large uneven planar facets.
   if layer==1 and i in (1,5):
    faces.extend([(layer*n+i,layer*n+j,(layer+1)*n+j),(layer*n+i,(layer+1)*n+j,(layer+1)*n+i)])
   else:faces.append((layer*n+i,layer*n+j,(layer+1)*n+j,(layer+1)*n+i))
 # Three broad crown planes across a noncentral low ridge; no regular fan/spike.
 verts.extend([(center[0]-.12*rx,center[1]+.04*ry,h),(center[0]+.20*rx,center[1]-.09*ry,h*.965)])
 faces.extend([(24,25,26,32),(26,27,28,33,32),(28,29,30,33),(30,31,24,32,33)])
 ob=mesh(name,verts,faces,rocks)
 for p in ob.data.polygons:
  p.use_smooth=False
  p.material_index=(4+seed)%8 if p.normal.z>.75 else ((p.index+seed)%4)
 ob['massHeight']=h;ob['construction']='Solid irregular octagonal boulder with three broad crown planes and angular shoulder band'
 return ob

# The widest shoulders interlock; low and mid rocks leave the upper crown exposed.
boulder('perimeter-rockery__high_boulder',(.185,.185),.300,.305,.98,.17,11)
boulder('perimeter-rockery__middle_boulder',(-.205,-.035),.285,.330,.67,-.14,27)
boulder('perimeter-rockery__low_boulder',(.170,-.285),.310,.205,.43,.03,41)

def leaf(name,base,tip,width,bend,phase,seed):
 # A closed folded blade, with thick underside and raised central ridge.
 start=Vector(base);end=Vector(tip);axis=end-start
 side=Vector((math.cos(phase),math.sin(phase),0))
 along=Vector((-math.sin(phase),math.cos(phase),0))
 rings=[];verts=[]
 for t,w,fold in [(0,.10,.015),(.42,1,.10),(.77,.70,.065)]:
  center=start+axis*t+along*bend*math.sin(math.pi*t)
  for off,up in [(-w*width,0),(0,fold),(w*width,0),(0,-.025)]:
   v=center+side*off+Vector((0,0,up));verts.append(tuple(v))
 verts.append(tuple(end));faces=[(3,2,1,0)]
 for ring in range(2):
  for i in range(4):faces.append((ring*4+i,ring*4+(i+1)%4,(ring+1)*4+(i+1)%4,(ring+1)*4+i))
 for i in range(4):faces.append((8+i,8+(i+1)%4,12))
 ob=mesh(name,verts,faces,leafm)
 for p in ob.data.polygons:
  p.material_index=([0,1,2,3][(p.index-1)%4]+seed)%6
  p.use_smooth=False
 ob['rootEmbeddedInRock']=True;return ob

# Two different crevice crowns. Their bases are buried in the adjacent rock solids.
leaf('Crevice A broad upright',(-.10,.095,.49),(-.16,.11,1.06),.095,.018,.08,0)
leaf('Crevice A left fan',(-.12,.11,.49),(-.40,.14,.84),.082,.023,.50,0)
leaf('Crevice A rear fan',(-.11,.13,.49),(-.06,.38,.92),.084,.016,2.40,1)
leaf('Crevice A compact outer',(-.15,.12,.46),(-.33,.31,.73),.080,.014,1.50,0)
leaf('Crevice A small crease',(-.10,.11,.50),(-.03,-.02,.85),.069,.008,1.10,1)
leaf('Crevice B broad upright',(.205,-.145,.30),(.26,-.11,.81),.095,.016,.20,0)
leaf('Crevice B outer fan',(.21,-.14,.30),(.445,-.15,.65),.085,.016,1.36,1)
leaf('Crevice B left fold',(.19,-.15,.30),(.07,-.28,.72),.080,.018,2.42,0)
leaf('Crevice B short outer',(.23,-.13,.32),(.39,.015,.60),.077,.012,2.60,0)
leaf('Crevice B crown tip',(.20,-.16,.32),(.18,-.03,.73),.074,.018,.63,1)
leaf('Crevice B compact front',(.22,-.16,.32),(.31,-.33,.56),.075,.015,2.20,0)

bpy.context.view_layer.update()
meshes=[o for o in scene.objects if o.type=='MESH']
scene.name='perimeter-rockery native draft 01';scene['asset_id']='perimeter-rockery';scene['recipe']='source/build-draft-01.py'
scene['sourceProjectSHA256']=sha(SOURCE);scene['noGroundPlane']=True
scene.render.film_transparent=True;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.cycles.samples=48;scene.cycles.seed=401;scene.cycles.use_animated_seed=False;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.use_persistent_data=True
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()

def capture():
 c=scene.camera
 return {'matrixWorld':[list(r) for r in c.matrix_world],'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]}
assert capture()==originalCamera
def px(p):
 q=world_to_camera_view(scene,scene.camera,Vector(p));return [q.x*384,(1-q.y)*704]
origin=px((0,0,0))
calibration={'root':origin,'unitX':[a-b for a,b in zip(px((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),origin)]}
def geometry():
 records=[];pts=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in meshes:
  ev=o.evaluated_get(dep);me=ev.to_mesh();v=[ev.matrix_world@x.co for x in me.vertices];pts+=v
  bm=bmesh.new();bm.from_mesh(me)
  records.append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'min':[min(x[i] for x in v) for i in range(3)],'max':[max(x[i] for x in v) for i in range(3)],'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'materialSlots':[m.name if m else None for m in o.data.materials]})
  bm.free();ev.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)],'objects':records}
g=geometry();assert all(g['min'][i]>=(-.5,-.5,0)[i]-1e-6 for i in range(3)),g['min'];assert all(g['max'][i]<=(.5,.5,1.5)[i]+1e-6 for i in range(3)),g['max']
assert all(x['nonManifoldEdges']==x['zeroAreaFaces']==0 for x in g['objects'])
assert len(bpy.data.images)==0 and len(bpy.data.libraries)==0
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT),compress=True)
records=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(a);scene.frame_set(1);bpy.context.view_layer.update();g=geometry()
 assert all(g['min'][i]>=(-.5,-.5,0)[i]-1e-6 for i in range(3));assert all(g['max'][i]<=(.5,.5,1.5)[i]+1e-6 for i in range(3))
 path=OUT/f'static-{d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'direction':d,'angleDegrees':a,'path':str(path.relative_to(BASE)),'sha256':sha(path),'bounds':{'min':g['min'],'max':g['max']}})
root.rotation_euler.z=0;bpy.context.view_layer.update()
v={'asset':'perimeter-rockery','status':'native-checks-passed-awaiting-independent-review','blender':bpy.app.version_string,'sourceOriginal':{'path':str(SOURCE),'sha256':sha(SOURCE),'matchesBackup':sha(SOURCE)==sha(BASE/BRIEF['source']['backup'])},'candidateProject':{'path':str(PROJECT.relative_to(BASE)),'sha256':sha(PROJECT)},'recipe':{'path':str(Path(__file__).relative_to(BASE)),'sha256':sha(__file__)},'briefSHA256':sha(BASE/'brief.json'),'capture':capture(),'sourceCapture':originalCamera,'calibration':calibration,'logicalFrame':[192,352],'logicalRoot':[96,248],'sourceScale':2,'cellSize':128,'root':{'name':root.name,'matrixWorld':[list(r) for r in root.matrix_world]},'lighting':originalLights,'geometry':geometry(),'renders':records,'dependencyClosure':{'images':[],'libraries':[],'nativeProceduralMaterialsOnly':True,'sourceProjectProvidesAllRetainedCameraWorldLights':True},'render':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoising':True,'seed':401,'transparentFilm':True,'groundPlane':False,'colorManagement':[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma]},'checks':{'cameraExact':capture()==originalCamera,'sourceIntact':sha(SOURCE)==BRIEF['source']['projectSHA256'],'withinEnvelope':True,'closedNativeMeshes':True,'noGroundPlane':True,'noRasterCardsOrTargetsInScene':True,'noPerViewFitOrRecolor':True}}
(OUT/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
print('ROCKERY_NATIVE_READY',str(OUT),flush=True)
