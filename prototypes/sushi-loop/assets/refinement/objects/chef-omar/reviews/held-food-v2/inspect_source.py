"""Read-only approved source/food placement inspection. No model saves."""
import bpy,sys,pathlib,json,hashlib,importlib.util,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parents[2];R=B/'reviews/held-food-v2';H=B.parents[2]/'production/source/blender'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
native=load('omar_v2_judge_native',H/'native_actions.py')
def sigdrivers(o):
 return [{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'path':t.data_path} for t in v.targets]} for v in f.driver.variables]} for f in (o.animation_data.drivers if o.animation_data else [])]
result={}
for name,project,recipe_path,rig_path,clip in [('salmon',B/'../../../production/source/blender/refinement/chef-omar/source/round-01.blend',B/'source/recipe-round01.json',B/'source/rig-round01.json','hold'),('cucumber',B/'source/runtime-round-01.blend',B/'source/runtime-recipe-round01.json',B/'source/runtime-rig-round01.json','hold-cucumber')]:
 bpy.ops.wm.open_mainfile(filepath=str(project.resolve()));rec=json.loads(recipe_path.read_text());rig=json.loads(rig_path.read_text());sc=bpy.data.scenes[rec['scene']];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll=bpy.data.collections[rec['collection']];root=bpy.data.objects[rec['root']];asset={'root':root,'collection':coll};coll.hide_render=False;coll.hide_viewport=False;sc.view_layers[0].update();plane=next(o for o in coll.all_objects if '__image_plane' in o.name);im=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');source={
 'project':str(project.resolve()),'projectSHA256':sha(project),'scene':sc.name,'collection':coll.name,'root':root.name,'camera':sc.camera.name,'plane':plane.name,'parent':plane.parent.name,'parentType':plane.parent_type,'parentBone':plane.parent_bone,'vertices':[list(v.co) for v in plane.data.vertices],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'faces':[list(p.vertices) for p in plane.data.polygons],'planeLocation':list(plane.location),'planeRotationEuler':list(plane.rotation_euler),'planeScale':list(plane.scale),'parentLocation':list(plane.parent.location),'parentRotationEuler':list(plane.parent.rotation_euler),'rootScale':list(root.scale),'image':{'name':im.name,'size':list(im.size),'packed':bool(im.packed_file),'sha256':hashlib.sha256(im.packed_file.data).hexdigest()},'drivers':{plane.name:sigdrivers(plane),plane.parent.name:sigdrivers(plane.parent)},'clips':{k:{a:v.get(a) for a in ['frames','fps','loop','firstFrame','lastUniqueFrame','closingKeyFrame']} for k,v in rig['clips'].items()},'frames':[]}
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
  for device in prefs.devices:device.use=device.type=='METAL'
 except Exception:pass
 def px(v):
  p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
 for direction in ['N','E','S','W']:
  native.apply_clip(asset,rig,clip,6,direction,sc);dg=bpy.context.evaluated_depsgraph_get();e=plane.evaluated_get(dg);corners=[e.matrix_world@v.co for v in e.data.vertices];anchor=e.matrix_world@Vector((0,0,0));palms={}
  for side in ['L','R']:
   o=next(o for o in coll.all_objects if '__palm_'+side in o.name);ev=o.evaluated_get(dg);palms[side]=sum((ev.matrix_world@v.co for v in ev.data.vertices),Vector())/len(ev.data.vertices)
  midpoint=(palms['L']+palms['R'])*.5
  r={'clip':clip,'index':5,'direction':direction,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'worldWidth':(corners[1]-corners[0]).length,'worldHeight':(corners[2]-corners[1]).length,'planeBottomMidpointWorld':list(anchor),'planeBottomPixel':px(anchor),'palmMidpointWorld':list(midpoint),'palmMidpointPixel':px(midpoint),'bottomMinusPalmPixel':[a-b for a,b in zip(px(anchor),px(midpoint))],'dishParentOriginWorld':list(plane.parent.matrix_world.translation),'planeMatrix':[list(row) for row in e.matrix_world],'visible':not plane.hide_render,'render':str((R/(name+'-current-'+direction+'.png')).relative_to(B))}
  sc.render.filepath=str(B/r['render']);bpy.ops.render.render(write_still=True);r['renderSHA256']=sha(B/r['render']);source['frames'].append(r)
 result[name]=source;(R/'source-placement-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('SOURCE_PLACEMENT',name,json.dumps({k:v for k,v in source.items() if k not in ['frames','drivers']}),flush=True)
print('READ_ONLY_COMPLETE',flush=True)
