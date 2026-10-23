"""Geometry-only stage. Preserve source W/N end profiles and concave clearance.
Final materials, lighting and family submissions remain pending.
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1]
SRC=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(SRC))
c=next(c for c in bpy.data.collections if 'wall-inner-corner' in c.name)
s=bpy.data.scenes.new('Wall inner corner geometry stage');s.collection.children.link(c);bpy.context.window.scene=s;bpy.context.view_layer.update()
root=next(o for o in c.all_objects if o.type=='EMPTY' and '__root' in o.name)
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
source={}
for o in c.all_objects:
 if o.type=='MESH':
  source[o.name]={'verts':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}
# Every ring uses source section half-width and height. The only plan modification
# is a tangent convex round entirely within source solid at the outside elbow.
# Concave vertex and both complete end cross-sections stay byte-coordinate equal.
def ring(h,z,r,n=12):
 r=min(r,h*.35)
 points=[(-.5,-h,z),(h-r,-h,z)]
 for k in range(1,n+1):
  a=-math.pi/2+k/n*math.pi/2
  points.append((h-r+r*math.cos(a),-h+r+r*math.sin(a),z))
 points.extend([(h,.5,z),(-h,.5,z),(-h,h,z),(-.5,h,z)])
 return points
reports=[]
for o in list(c.all_objects):
 if o.type!='MESH':continue
 old=source[o.name];zvals=sorted(set(v[2] for v in old['verts']))
 rings=[]
 for z in zvals:
  h=max(v[0] for v in old['verts'] if v[2]==z)
  r=.028 if 'blue_coping' in o.name else (.017 if 'wood_cap' in o.name else .010)
  rings.append(ring(h,z,r))
 n=len(rings[0]);verts=[p for ring_ in rings for p in ring_]
 faces=[tuple(reversed(range(n))),tuple((len(rings)-1)*n+i for i in range(n))]
 for j in range(len(rings)-1):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 me=bpy.data.meshes.new(o.name+' continuous rounded native');me.from_pydata(verts,[],faces);me.update()
 for mat in o.data.materials:me.materials.append(mat)
 o.data=me
 for p in me.polygons:
  # The outside 90-degree arc has tangent smooth normals. Broad planes remain flat.
  p.use_smooth=(p.index>=2 and 1<=(p.index-2)%n<=12)
 o['geometry_refinement']='continuous L bands; convex elbow tangent round; exact W/N source sections; concave vertex unchanged'
 # Compare all source join vertices with new end plane vertices.
 checks={}
 for tag,axis,plane in [('W',0,-.5),('N',1,.5)]:
  oldpoints=sorted(tuple(v) for v in old['verts'] if abs(v[axis]-plane)<1e-7)
  newpoints=sorted(tuple(v.co) for v in me.vertices if abs(v.co[axis]-plane)<1e-7)
  checks[tag]={'source':oldpoints,'current':newpoints,'exactOriginalVertices':oldpoints==newpoints}
  assert oldpoints==newpoints,(o.name,tag,oldpoints,newpoints)
 reports.append({'part':o.name,'rings':[(max(p[0] for p in rr),rr[0][2]) for rr in rings],'convexRadius':r,'vertices':len(verts),'polygons':len(faces),'portChecks':checks})
# Retain capture camera as a real mathutils.Matrix, including registered pixel aspect.
rec=json.loads((B/'inputs/source-camera.json').read_text());camdata=bpy.data.cameras.new('Registered corner camera');cam=bpy.data.objects.new('Registered corner camera',camdata);s.collection.objects.link(cam)
cam.matrix_world=Matrix(rec['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5;camdata.shift_y=0
s.camera=cam;s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=rec['camera']['pixelAspect'][0];s.render.pixel_aspect_y=rec['camera']['pixelAspect'][1];s.render.film_transparent=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.fps=12
def pixel(v):
 p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*384,(1-p.y)*704))
bpy.context.view_layer.update();base=pixel((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-base.y;camdata.shift_y=(512-base.y)/dy;bpy.context.view_layer.update()
cal={k:list(pixel(v))for k,v in {'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()}
cal={k:(p if k=='root'else[p[i]-cal['root'][i]for i in range(2)])for k,p in cal.items()}
# Strip unrelated scene and orphan dependency data from the editable copy only.
for sc in list(bpy.data.scenes):
 if sc!=s:bpy.data.scenes.remove(sc)
for col in list(bpy.data.collections):
 if col!=c and col.users==0:bpy.data.collections.remove(col)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();allpts=[]
for o in c.all_objects:
 if o.type=='MESH':
  ev=o.evaluated_get(dg);me=ev.to_mesh();allpts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
report={'stage':'geometry-only; not a candidate; family settings pending','source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'collection':c.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'bounds':[[min(p[i]for p in allpts),max(p[i]for p in allpts)]for i in range(3)],'sourcePortProfilesExact':True,'cameraCalibration':cal,'concaveClearance':'No new point outside original ring L. Original (-h,h) concave vertex retained at every source band height. Convex outside arc removes material inside the original envelope.','parts':reports,'pending':['approved family materials','approved family lighting/capture exact matching','four native rotations','native both-port assemblies','independent sprite assemblies','RGB alpha QA and final validation']}
(B/'candidates/geometry-stage.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/geometry-stage.blend'))
print(json.dumps({'bounds':report['bounds'],'sourcePortProfilesExact':True,'parts':len(reports)}))
