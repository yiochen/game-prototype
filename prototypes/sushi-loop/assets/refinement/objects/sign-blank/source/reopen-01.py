import bpy,json,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
project=P/'source/round-01.blend';before=sha(project)
bpy.ops.wm.open_mainfile(filepath=str(project));s=bpy.context.scene;cam=s.camera
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
meshes=[o for o in s.objects if o.type=='MESH'];points=[];objects=[]
for o in meshes:
 ev=o.evaluated_get(dg);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];points+=vs
 bm=bmesh.new();bm.from_mesh(me);objects.append({'name':o.name,'matrix':[list(r) for r in o.matrix_world],'bounds':[[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]],'vertices':len(me.vertices),'faces':len(me.polygons),'nonManifoldEdges':sum(len(e.link_faces)!=2 for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces)});bm.free();ev.to_mesh_clear()
def px(v):
 q=world_to_camera_view(s,cam,Vector(v));return Vector((q.x*384,(1-q.y)*704))
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.render.filepath=str(O/'reopened-S.png');bpy.ops.render.render(write_still=True)
origin=px((0,0,0));v={'projectSHA256Before':before,'projectSHA256After':sha(project),'projectUnchanged':before==sha(project),'reopenedNativeFrame':'candidates/round-01/reopened-S.png','reopenedNativeFrameSha256':sha(O/'reopened-S.png'),'originalNativeFrameSha256':sha(O/'static-S.png'),'renderBytesIdentical':sha(O/'static-S.png')==sha(O/'reopened-S.png'),'meshCount':len(meshes),'objects':objects,'bounds':[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]],'root':list(bpy.data.objects['sign-blank__root'].location),'projectedRoot':list(origin),'projectedUnitX':list(px((1,0,0))-origin),'projectedUnitDepth':list(px((0,-1,0))-origin),'projectedUnitHeight':list(px((0,0,1))-origin),'linkedLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file],'allDatablocksLocal':not any(d.library for bank in [bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.collections,bpy.data.node_groups,bpy.data.images] for d in bank)}
(O/'reopened-validation.json').write_text(json.dumps(v,indent=2));print('REOPENED',v['renderBytesIdentical'],v['allDatablocksLocal'])
