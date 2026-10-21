"""Revise only the detached smile with native face-conforming geometry. Round01 is read-only."""
import bpy,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-02';C.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round02 as native
sc=bpy.data.scenes['Lena warm soft round01'];bpy.context.window.scene=sc;sc.name='Lena warm soft round02';coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];head=bpy.data.objects['chef_lena__head.002'];smile=bpy.data.objects['chef_lena__R01_gentle_smile'];rig=json.loads((P/'rig-round02.json').read_text());asset={'collection':coll,'root':root,'armature':arm};native.apply_clip(asset,rig,'idle',1,'S',sc)
# Raw baked head and smile use common ground-root-local rest coordinates and same deform bone.
# Ray-project every mouth vertex against actual head mesh, giving an embedded elliptical ribbon.
bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons],all_triangles=False)
vs=[];faces=[];samples=96;segments=16;offsets=[]
for j in range(samples+1):
 x=-.043+.086*j/samples;z=.530+.019*(x/.043)**2;slope=2*.019*x/(.043**2);n=Vector((-slope,1)).normalized()
 for k in range(segments):
  a=math.tau*k/segments;xx=x+.004*math.cos(a)*n.x;zz=z+.004*math.cos(a)*n.y
  hit,normal,index,dist=bvh.ray_cast(Vector((xx,-.8,zz)),Vector((0,1,0)),2)
  if hit is None:raise RuntimeError('Smile vertex ray missed actual native head surface')
  depth=.0005+.0015*math.sin(a);vs.append((xx,hit.y+depth,zz));offsets.append(depth)
for j in range(samples):
 for k in range(segments):faces.append((j*segments+k,j*segments+(k+1)%segments,(j+1)*segments+(k+1)%segments,(j+1)*segments+k))
faces.extend([tuple(reversed(range(segments))),tuple(range(samples*segments,(samples+1)*segments))])
me=bpy.data.meshes.new('Lena02 face-conforming embedded smile');me.from_pydata(vs,[],[tuple(reversed(f)) for f in faces]);me.update();material=smile.data.materials[0];me.materials.append(material);smile.data=me
for poly in me.polygons:poly.use_smooth=True
vg=smile.vertex_groups.get('head') or smile.vertex_groups.new(name='head');vg.add(range(len(me.vertices)),1,'REPLACE')
smile['refinement_round']=2;smile['construction']='Native thin elliptical mouth ribbon projected to actual rounded head surface; front<=0.001 local outside skin, back embedded0.002; unchanged head-bone deformation.'
# Preserve all lights, materials, garments, rig/rest/actions, camera and capture settings.
recipe=json.loads((P/'recipe-round01.json').read_text());recipe['round']=2;recipe['scene']=sc.name;recipe['previousApprovedConstructionSource']={'path':'source/round-01.blend','sha256':hashlib.sha256((P/'round-01.blend').read_bytes()).hexdigest()};recipe['revisionScope']={'review':'reviews/round-01.json','blocker':'detached-profile-smile','onlyArtChange':'Replace floating tubular smile with actual head-surface-conforming native embedded ribbon','restLocalSurfaceDepthRange':[min(offsets),max(offsets)],'sameHeadBone':True,'originalSmileNameRetained':smile.name,'otherSceneConstructionUnchanged':True};recipe['commands']={'build':'blender -b source/round-01.blend --python source/build_round02.py','render':'blender -b source/round-02.blend --python source/render_round02.py','package':'Bundled Python with Pillow: source/package_round02.py'};recipe['dependencyClosure']={'native_actions_round02.py':'immutable round02 copy of original native action adapter','rig-round02.json':'immutable original action registry','source-contacts-round02.json':'untouched original192sample evaluated contact baseline','source-rest-round02.json':'untouched original25bone rest baseline','round-01.blend':'reviewed preceding construction, read only','dependencies/dish-salmon.png':'unchanged original packed2D dish, also embedded'}
(P/'recipe-round02.json').write_text(json.dumps(recipe,indent=2)+'\n')
# Save ordinary editable final project before any round02 capture; never overwrite prior round files.
path=P/'round-02.blend'
if path.exists():raise RuntimeError('Round02 project already exists; do not overwrite')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
(C/'smile-native-construction.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'object':smile.name,'nativeVertices':len(me.vertices),'nativePolygons':len(me.polygons),'headSurface':'actual baked chef_lena__head.002 rest mesh','maximumRestLocalFrontProjection':-min(offsets),'backEmbedding':max(offsets),'sharedDeformBone':'head','allOtherArtAndCapturePreserved':True},indent=2))
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
for direction in ['S','E','N','W']:
 native.apply_clip(asset,rig,'idle',1,direction,sc);sc.render.filepath=str(C/('scout-'+direction+'.png'));bpy.ops.render.render(write_still=True)
print('ROUND02 SAVED',path)
