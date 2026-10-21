import bpy,json,math,bmesh,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03';PROJECT=BASE/'source/round-03.blend'
bpy.ops.wm.open_mainfile(filepath=str(PROJECT));scene=bpy.context.scene;cam=scene.camera;root=bpy.data.objects['slate-rock__root.001'];collection=bpy.data.collections['S33_PROP_slate-rock.001']
def bounds():
 pts=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in collection.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dep);m=e.to_mesh();pts.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
def pixel(point):
 v=world_to_camera_view(scene,cam,Vector(point));return [v.x*384,(1-v.y)*704]
parts=[]
for o in collection.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(row) for row in o.matrix_world],'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}
 if o.type=='MESH':
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();bm=bmesh.new();bm.from_mesh(m)
  r.update({'vertices':len(m.vertices),'polygons':len(m.polygons),'nonManifoldEdges':sum(not ed.is_manifold for ed in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'materialSlots':[mat.name if mat else None for mat in o.data.materials],'usedMaterialIndices':sorted(set(p.material_index for p in m.polygons))});bm.free();e.to_mesh_clear()
 parts.append(r)
root.rotation_euler=(0,0,0);bpy.context.view_layer.update();origin=pixel((0,0,0))
cal={'root':origin,'unitX':[a-b for a,b in zip(pixel((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(pixel((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(pixel((0,0,1)),origin)]}
facings=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(a);bpy.context.view_layer.update();facings.append({'direction':d,'rootRotationDegrees':a,'rootMatrix':[list(r) for r in root.matrix_world],'bounds':bounds(),'reopenedRenderPath':f'candidates/round-03/reopened-{d}.png'})
 scene.render.filepath=str(OUT/f'reopened-{d}.png');bpy.ops.render.render(write_still=True)
root.rotation_euler.z=0;bpy.context.view_layer.update()
record={'project':'source/round-03.blend','projectSha256':hashlib.sha256(PROJECT.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scene':scene.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'frame':[scene.render.resolution_x,scene.render.resolution_y],'sourceScale':scene.get('source_scale'),'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'type':cam.data.type,'matrixWorld':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':cal,'parts':parts,'facings':facings,'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'sceneMeshes':[o.name for o in scene.objects if o.type=='MESH'],'lights':[{'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'location':list(o.location)} for o in scene.objects if o.type=='LIGHT'],'transparentFilm':scene.render.film_transparent,'proceduralMaterialsOnly':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'cyclesDevice':scene.cycles.device,'reopenedNativeRender':{'path':'candidates/round-03/reopened-N.png'}}
(OUT/'reopened-source.json').write_text(json.dumps(record,indent=2)+'\n');print('REOPENED',record['projectSha256'])
