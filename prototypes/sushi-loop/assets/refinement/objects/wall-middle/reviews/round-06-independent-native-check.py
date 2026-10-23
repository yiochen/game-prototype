import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1]
project=B/'source/round-06.blend';original=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identify(name):return name.split('__')[1].replace('.001','')
bpy.ops.wm.open_mainfile(filepath=str(original));c=bpy.data.collections['S33_PROP_wall-middle.001']
originals={identify(o.name):{'vertices':[tuple(v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons]} for o in c.all_objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(project));s=bpy.context.scene;c=bpy.data.collections['S33_PROP_wall-middle.001'];root=bpy.data.objects['wall-middle__root.001'];bpy.context.view_layer.update()
points=[o.matrix_world@v.co for o in c.all_objects if o.type=='MESH' for v in o.data.vertices]
profiles=[]
for o in c.all_objects:
 if o.type!='MESH' or 'camera_cut_planes' in o.name:continue
 old=originals[identify(o.name)];vs=old['vertices']
 for side in (-.5,.5):
  segments=[]
  for f in old['faces']:
   for i,j in zip(f,f[1:]+f[:1]):
    if abs(vs[i][0]-side)<1e-6 and abs(vs[j][0]-side)<1e-6:segments.append((Vector(vs[i][1:]),Vector(vs[j][1:])))
  ps=[Vector((v.co.y,v.co.z)) for v in o.data.vertices if abs(v.co.x-side)<1e-6]
  def distance(p):
   ds=[]
   for a,b in segments:
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared)) if d.length_squared else 0;ds.append((p-(a+t*d)).length)
   return min(ds)
  corners=[Vector(v[1:]) for v in vs if abs(v[0]-side)<1e-6]
  profiles.append({'mesh':o.name,'plane':side,'maxDistance':max(distance(p) for p in ps),'containsSourceCorners':all(any((p-q).length<1e-6 for p in ps)for q in corners)})
cam=s.camera
p=world_to_camera_view(s,cam,Vector((0,0,0)))
matInfo=[]
for m in bpy.data.materials:
 if not m.users:continue
 matInfo.append({'name':m.name,'nodes':[n.bl_idname for n in m.node_tree.nodes] if m.node_tree else [],'hasImageNode':any(n.type=='TEX_IMAGE'for n in m.node_tree.nodes) if m.node_tree else False})
result={'candidateProjectSHA256':sha(project),'originalProjectSHA256':sha(original),'scene':s.name,'collection':c.name,'root':{'matrix':[list(x) for x in root.matrix_world],'groundRoot':json.loads(root['ground_root']),'ports':json.loads(root['ports'])},'bounds':[[min(v[i]for v in points),max(v[i]for v in points)]for i in range(3)],'geometryEndsAtPlanes':all(-.5000001<=v.x<=.5000001 for v in points),'meshCount':sum(o.type=='MESH'for o in s.objects),'profiles':profiles,'camera':{'matrix':[list(x)for x in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'rootInPixels':[p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]},'lights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size}for o in s.objects if o.type=='LIGHT'],'resources':{'images':[(i.name,i.filepath)for i in bpy.data.images],'libraries':[i.filepath for i in bpy.data.libraries]},'materials':matInfo,'savedProject':False}
(B/'reviews/round-06-independent-native-check.json').write_text(json.dumps(result,indent=2)+'\n')
print('INDEPENDENT_CHECK',json.dumps({k:v for k,v in result.items()if k not in ['profiles','materials','lights','root']}))
