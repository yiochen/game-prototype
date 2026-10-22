import bpy,json,math,sys,importlib.util
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'evidence'/'historical-adapter-replay';OUT.mkdir(exist_ok=True);sys.dont_write_bytecode=True
for n in ['native_actions','catalog_style','catalog_faceted','concept_decoration_geometry']:
 spec=importlib.util.spec_from_file_location(n,BASE/(n+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);globals()[n]=m
sc=next(s for s in bpy.data.scenes if any(o.get('production_id')=='decor-kelp' for o in s.objects));bpy.context.window.scene=sc
root=next(o for o in sc.objects if o.get('production_id')=='decor-kelp');col=next(c for c in root.users_collection if root in c.objects.values());objs=list(col.all_objects)
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for lc in bpy.context.view_layer.layer_collection.children:
 lc.exclude=False;lc.hide_viewport=False
col.hide_render=False;col.hide_viewport=False
for o in objs:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
rig=json.loads((BASE/'object/inputs/source-rig.json').read_text());meta=json.loads((BASE/'object/inputs/source-camera.json').read_text())
asset={'root':root,'collection':col,'parts':{o.name:o for o in objs}}
# Replay the own historical registered 35-degree orthographic camera, not saved active .240.
cam=sc.camera;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=meta['frame'][0]/128;cam.matrix_world=Matrix(meta['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=.75
sc.render.engine='BLENDER_EEVEE';sc.eevee.taa_render_samples=32
sc.render.resolution_x=768;sc.render.resolution_y=1920;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
catalog_style.ensure_compositor(sc);lighting=catalog_faceted.ensure_lights(sc)
for o in sc.objects:
 if o.type=='LIGHT' and not o.get('s33FacetedRole'):o.data.energy=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def pix(p):
 p=world_to_camera_view(sc,cam,Vector(p));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
def mesh(o):
 e=o.evaluated_get(dg);me=e.to_mesh();verts=[e.matrix_world@v.co for v in me.vertices];polys=[list(p.vertices)for p in me.polygons];e.to_mesh_clear();return verts,polys
camera={'frame':[192,480],'anchor':[96,384],'captureScale':4,'fps':12,'nativeFrame':[768,1920],'camera':{'type':'orthographic','worldMatrix':[list(r)for r in cam.matrix_world],'projectionMatrix':[list(r)for r in cam.calc_matrix_camera(dg,x=768,y=1920,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[1,1]},'calibration':{'root':pix((0,0,0)),'unitX': [v-b for v,b in zip(pix((1,0,0)),pix((0,0,0)))],'unitDepth':[v-b for v,b in zip(pix((0,-1,0)),pix((0,0,0)))],'unitHeight':[v-b for v,b in zip(pix((0,0,1)),pix((0,0,0)))]},'lighting':lighting,'savedCameraBeforeReplay':'S33 Capture Camera.240'}
(OUT/'registered-camera-replay.json').write_text(json.dumps(camera,indent=2)+'\n')
channels=[]
for t in rig['clips']['idle']['actions']:
 a=bpy.data.actions[t['action']];curves=[]
 for layer in a.layers:
  for strip in layer.strips:
   for slot in a.slots:
    bag=strip.channelbag(slot)
    if bag:
     for f in bag.fcurves:curves.append({'path':f.data_path,'index':f.array_index,'keys':[[*k.co,k.interpolation]for k in f.keyframe_points]})
 channels.append(dict(t,curves=curves))
frames=[]
for direction in ['S','E','N','W']:
 for frame in range(1,14):
  native_actions.apply_clip(asset,rig,'idle',frame,direction,sc);dg=bpy.context.evaluated_depsgraph_get()
  points=[];record={'direction':direction,'nativeFrame':frame,'publishedIndex':frame-1 if frame<=12 else None,'closureOnly':frame==13,'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r)for r in root.matrix_world],'geometry':[]}
  for o in objs:
   if o.type!='MESH':continue
   
   with concept_decoration_geometry.capture_projection(col,'ordinary35'):vs,ps=mesh(o)
   points+=vs;record['geometry'].append({'name':o.name,'rotationY':o.rotation_euler.y,'bounds':[[min(v[i]for v in vs),max(v[i]for v in vs)]for i in range(3)],'verticesWorld':[list(v)for v in vs],'polygons':ps})
  record['envelope']=[[min(v[i]for v in points),max(v[i]for v in points)]for i in range(3)]
  frames.append(record)
  if frame in [1,4,7,10,13]:
   p=OUT/'native'/direction/(f'{frame:02d}.png');p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);
   with concept_decoration_geometry.capture_projection(col,'ordinary35'):bpy.ops.render.render(write_still=True,scene=sc.name)
(OUT/'native-sampling.json').write_text(json.dumps({'asset':'decor-kelp','blender':bpy.app.version_string,'actions':channels,'samples':frames,'notes':'All 12 unique frames and closure sampled per facing after own native action binding; five representative phases rendered per facing with exact historical height-dependent ordinary35 projection adapter. Geometry sampled from enabled evaluated view layer.'},indent=2)+'\n')
materials=[]
for m in {m for o in objs if o.type=='MESH' for m in o.data.materials if m}:
 materials.append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None}for n in m.node_tree.nodes],'animated':bool(m.node_tree.animation_data),'drivers':len(m.node_tree.animation_data.drivers)if m.node_tree.animation_data else 0})
(OUT/'resource-ownership.json').write_text(json.dumps({'materials':materials,'libraries':[x.filepath for x in bpy.data.libraries],'armatures':[o.name for o in objs if o.type=='ARMATURE'],'UVs':{o.name:[u.name for u in o.data.uv_layers]for o in objs if o.type=='MESH'},'shapeKeys':{o.name:list(o.data.shape_keys.key_blocks.keys())for o in objs if o.type=='MESH' and o.data.shape_keys},'constraints':{o.name:[c.type for c in o.constraints]for o in objs if o.constraints}},indent=2)+'\n')
print('PREPARATION COMPLETE')
