import bpy,json,math,hashlib,sys,bmesh
from mathutils import Vector
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
out=Path(sys.argv[sys.argv.index('--')+1]);out.mkdir(parents=True,exist_ok=True)
root=bpy.data.objects['S33 production concept cobalt-crags root'];col=bpy.data.collections['S33 production concept cobalt-crags'];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.view_layer.update()
rows=lambda m:[[float(x) for x in r] for r in m]
meshes=[o for o in col.all_objects if o.type=='MESH']
def bounds():
 ps=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];return {'min':[min(v[i] for v in ps) for i in range(3)],'max':[max(v[i] for v in ps) for i in range(3)]}
def evaluated_bounds():
 ps=[]
 for o in meshes:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();ps += [e.matrix_world@v.co for v in m.vertices];e.to_mesh_clear()
 return {'min':[min(v[i] for v in ps) for i in range(3)],'max':[max(v[i] for v in ps) for i in range(3)]}
def projection():
 cam=sc.camera;r=sc.render;p=world_to_camera_view(sc,cam,Vector((0,0,0)))
 return {'name':cam.name,'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=r.resolution_x,y=r.resolution_y,scale_x=r.pixel_aspect_x,scale_y=r.pixel_aspect_y)),'pixelAspect':[r.pixel_aspect_x,r.pixel_aspect_y],'resolution':[r.resolution_x,r.resolution_y,r.resolution_percentage],'rootPixels':[p.x*r.resolution_x,(1-p.y)*r.resolution_y]}
res={'method':'Fresh Blender process reading exact sealed .blend. Independent scene/root/mesh/camera/resource inspection and all-four replay using source square-footing formula; no save or recipe import.','projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'collection':col.name,'root':root.name,'canonicalRootMatrix':rows(root.matrix_world),'physicalBounds':bounds(),'evaluatedBounds':evaluated_bounds(),'camera':projection(),'meshes':[],'materials':[],'lights':[],'scenes':len(bpy.data.scenes),'linkedLibraries':[l.filepath for l in bpy.data.libraries],'fileImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'actions':[a.name for a in bpy.data.actions],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'objectCounts':{t:sum(o.type==t for o in sc.objects) for t in ['MESH','EMPTY','LIGHT','CAMERA']},'useCompositing':sc.render.use_compositing,'directions':{}}
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data)
 res['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'looseVertices':sum(not v.link_edges for v in bm.verts),'degenerateFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'modifiers':[m.type for m in o.modifiers],'materialSlots':[m.name for m in o.data.materials]});bm.free()
for m in bpy.data.materials:
 res['materials'].append({'name':m.name,'nodes':[n.type for n in m.node_tree.nodes] if m.use_nodes else [],'linkedLibraries':bool(m.library)})
for o in sc.objects:
 if o.type=='LIGHT':res['lights'].append({'name':o.name,'type':o.data.type,'location':list(o.location),'matrixWorld':rows(o.matrix_world),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)})
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler=(0,0,a);sc.frame_set(1);bpy.context.view_layer.update();drec={'rootMatrix':rows(root.matrix_world),'bounds':bounds(),'evaluatedBounds':evaluated_bounds(),'camera':projection()};saved=[]
 for o in meshes:
  saved.append((o,[v.co.copy() for v in o.data.vertices]));inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   p=o.matrix_world@v.co;p.y*=1+(1/math.sin(math.radians(35))-1)*max(0,1-max(0,p.z)/.42)**2;v.co=inv@p
  o.data.update()
 bpy.context.view_layer.update();drec['captureBounds']=evaluated_bounds();p=out/f'{d}.png';sc.render.filepath=str(p.resolve());bpy.ops.render.render(write_still=True,scene=sc.name)
 drec['renderSHA256']=hashlib.sha256(p.read_bytes()).hexdigest()
 for o,ps in saved:
  for v,p in zip(o.data.vertices,ps):v.co=p
  o.data.update()
 bpy.context.view_layer.update();res['directions'][d]=drec
root.rotation_euler=(0,0,0);bpy.context.view_layer.update();res['postReplayBounds']=bounds();(out/'native-check.json').write_text(json.dumps(res,indent=2)+'\n');print('INDEPENDENT_NATIVE_CHECK_COMPLETE',json.dumps({'projectSHA256':res['projectSHA256'],'bounds':res['physicalBounds'],'directions':list(res['directions'])}))
