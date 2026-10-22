"""Render-only replay from immutable saved source; no geometry/material edits or authoring builders."""
import bpy,math,json,pathlib,sys,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parent;R=P/'resources';sys.path.insert(0,str(R/'blender-code'))
import capture_runtime as cap
sc=cap.scene();c=bpy.data.collections['S33_PROP_harpoon_mount.001'];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
root=bpy.data.objects['harpoon_mount__root.001'];rig=json.loads((R/'inputs/source-rig.json').read_text())
camera=cap.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
sc.render.engine='BLENDER_EEVEE';sc.render.filter_size=1.5
# Native capture quality is common across views and poses.
if hasattr(sc,'eevee') and hasattr(sc.eevee,'taa_render_samples'):sc.eevee.taa_render_samples=64
capfile=P/'native-source';capfile.mkdir(exist_ok=True)
records=[]
def assign(clip,f,d):
 for o in c.all_objects:
  if o.animation_data:o.animation_data.action=None
 for t in rig['clips'][clip]['actions']:
  o=bpy.data.objects[t['ownerName']];o.animation_data_create();a=bpy.data.actions[t['action']];o.animation_data.action=a;o.animation_data.action_slot=next(s for s in a.slots if s.identifier==t['slotIdentifier'])
 root.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]
 sc.frame_set(f);bpy.context.view_layer.update()
def pts_mesh(o):
 dg=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(dg);m=eo.to_mesh();vs=[eo.matrix_world@v.co for v in m.vertices];eo.to_mesh_clear();return vs
def bounds(vs):return [[min(v[i] for v in vs) for i in range(len(vs[0]))],[max(v[i] for v in vs) for i in range(len(vs[0]))]]
for clip in ['idle','active']:
 for d in 'NESW':
  for f in range(1,rig['clips'][clip]['lastUniqueFrame']+1):
   assign(clip,f,d);vs=[v for o in c.all_objects if o.type=='MESH' for v in pts_mesh(o)];xy=[]
   for v in vs:
    q=world_to_camera_view(sc,sc.camera,v);xy.append([q.x*192,(1-q.y)*352])
   dst=capfile/f'{clip}-{d}-{f:02}.png';sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True,scene=sc.name)
   records.append({'clip':clip,'direction':d,'sourceFrame':f,'path':str(dst.relative_to(P)),'bounds':bounds(vs),'projectedLogicalVertexBounds':bounds(xy),'movingLocations':{o.name:list(o.location) for o in c.all_objects if 'barrel' in o.name or 'muzzle' in o.name}})
assign('idle',1,'S')
geo=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 dg=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(dg);m=eo.to_mesh();vs=[eo.matrix_world@v.co for v in m.vertices]
 geo.append({'name':o.name,'localLocation':list(o.location),'localEuler':list(o.rotation_euler),'localScale':list(o.scale),'evaluatedVertices':[list(v) for v in vs],'evaluatedFaces':[list(f.vertices) for f in m.polygons],'bounds':bounds(vs),'materialSlots':[mat.name if mat else None for mat in o.data.materials],'modifiers':[{'name':a.name,'type':a.type} for a in o.modifiers],'uvLayers':[l.name for l in o.data.uv_layers]});eo.to_mesh_clear()
images=[{'name':im.name,'path':im.filepath,'source':im.source,'packed':bool(im.packed_file)} for im in bpy.data.images if im.users and im.name!='Render Result']
(P/'native-source-audit.json').write_text(json.dumps({'source':'resources/own-original-library.blend','sourceSHA256':hashlib.sha256((R/'own-original-library.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'method':'Existing native mesh/material/action replay; no authoring pose function, no rebuilding. Actual actions assigned by cohort and evaluated at integer source frames.','camera':camera,'rootNeutral':[list(r) for r in root.matrix_world],'neutralGeometry':geo,'nativeImages':images,'frames':records},indent=2)+'\n')
(P/'replay-camera.json').write_text(json.dumps(camera,indent=2)+'\n')
print('SOURCE_REPLAY_COMPLETE',len(records))
