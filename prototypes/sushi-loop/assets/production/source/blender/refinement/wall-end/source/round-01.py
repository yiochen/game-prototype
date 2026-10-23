"""Wall-end round 01: approved family surfaces + native crafted terminal.
Run: blender -b --python source/round-01.py. Never modifies family/original inputs.
"""
import bpy, json, math, hashlib, shutil
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];R='round-01';O=B/'candidates'/R;O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
F=B/'source/round-01-approved-family.blend';FSET=B/'source/round-01-family-settings.json'
assert sha(F)=='13a7d057b1e0650582b60f4404ca1bb9b316774feb467c781730c7e43a25f723'
assert sha(FSET)=='690f0ee33c4ff18f02f4352fd91f326f0c42610e335c16a802222c4f216357ef'
family=json.loads(FSET.read_text());original=json.loads((B/'candidates/inspection/source.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(F))
collection=bpy.data.collections['S33_PROP_wall-middle.001'];collection.hide_render=False;collection.hide_viewport=False
# Explicitly isolate the named collection before evaluating matrices.
scene=bpy.data.scenes.new('Warm soft wall end — round 01');scene.collection.children.link(collection);bpy.context.window.scene=scene
oldscene=next(s for s in bpy.data.scenes if s!=scene)
scene.camera=oldscene.camera;scene.collection.objects.link(scene.camera)
scene.world=oldscene.world
for ob in list(oldscene.objects):
 if ob.type=='LIGHT':scene.collection.objects.link(ob)
# Inherit approved render/color values rather than guessing settings.
for attr in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','fps','filter_size']:
 setattr(scene.render,attr,getattr(oldscene.render,attr))
scene.render.engine='CYCLES'
for attr in ['samples','use_denoising','max_bounces','transparent_max_bounces','pixel_filter_type','seed','use_animated_seed','adaptive_threshold','use_adaptive_sampling']:
 setattr(scene.cycles,attr,getattr(oldscene.cycles,attr))
for attr in ['view_transform','look','exposure','gamma']:
 setattr(scene.view_settings,attr,getattr(oldscene.view_settings,attr))
for attr in ['file_format','color_mode','color_depth','compression']:
 setattr(scene.render.image_settings,attr,getattr(oldscene.render.image_settings,attr))
root=next(o for o in collection.all_objects if o.type=='EMPTY');root.name='wall-end__root';root.rotation_euler=(0,0,0)
for k,v in original['objects'][0]['custom'].items():root[k]=v
collection.name='S33_PROP_wall-end.refined'
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
bpy.context.view_layer.update()
# Clip each polygon at a buried interior termination. Preserve the family W
# positions AND split normals exactly; no longitudinal scaling or UV phase fit.
def clip_mesh(obj,xmax,cut_only=False):
 m=obj.data;verts=[];faces=[];normals=[];lookup={}
 for p in m.polygons:
  poly=[(m.vertices[m.loops[i].vertex_index].co.copy(),m.corner_normals[i].vector.copy())for i in p.loop_indices]
  if cut_only:
   if not all(abs(co.x+.5)<1e-6 for co,no in poly):continue
  else:
   out=[]
   for A,Bb in zip(poly,poly[1:]+poly[:1]):
    a,na=A;b,nb=Bb;ina=a.x<=xmax;inb=b.x<=xmax
    if ina:out.append(A)
    if ina!=inb:
     t=(xmax-a.x)/(b.x-a.x);out.append((a.lerp(b,t),na.lerp(nb,t).normalized()))
   poly=out
  if len(poly)<3:continue
  face=[]
  for co,no in poly:
   key=tuple(round(v,8)for v in co)
   if key not in lookup:lookup[key]=len(verts);verts.append(tuple(co))
   face.append(lookup[key]);normals.append(tuple(no))
  if len(set(face))>=3:faces.append(face)
  else:del normals[-len(face):]
 new=bpy.data.meshes.new(obj.name+' exact-family clip');new.from_pydata(verts,[],faces);new.update()
 for mat in m.materials:new.materials.append(mat)
 for p in new.polygons:p.use_smooth=True
 if len(normals)==len(new.loops):new.normals_split_custom_set(normals)
 obj.data=new
for o in list(collection.all_objects):
 if o.type!='MESH':continue
 o.name=o.name.replace('wall-middle__','wall-end__')
 clip_mesh(o,.235 if o.name.endswith('blue_coping')else .29,'__camera_cut_planes'in o.name)
 o['familyDerivation']='Exact approved round06 source W profile, native material and split normals; buried positive X termination.'
wood=bpy.data.materials['Warm wall · honey timber'];strip=bpy.data.materials['Warm wall · slender timber bead'];undercut=bpy.data.materials['Warm wall · cap undercut']
# Real bevelled wood joinery; unchanged four approved family material graphs.
def box(name,bounds,material,bevel,vertical_grain=False):
 (x0,x1),(y0,y1),(z0,z1)=bounds
 bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2));o=bpy.context.object;o.name='wall-end__'+name
 for c in list(o.users_collection):c.objects.unlink(o)
 collection.objects.link(o);o.parent=root
 o.dimensions=(x1-x0,y1-y0,z1-z0);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Reorient local object texture coordinates to run family grain along shaft.
 if vertical_grain:
  rot=Matrix.Rotation(math.pi/2,4,'Y');o.data.transform(rot.inverted());o.rotation_euler=rot.to_euler()
 o.data.materials.append(material)
 b=o.modifiers.new('Soft crafted solid edges','BEVEL');b.width=bevel;b.segments=4
 b.affect='EDGES';b.harden_normals=True
 for p in o.data.polygons:p.use_smooth=True
 w=o.modifiers.new('Broad planar normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=50
 o['constructionRole']=name;o['materialContract']='Unmodified approved family material';return o
box('terminal_shaft',[(.215,.395),(-.139,.139),(.085,.928)],wood,.018,True)
box('terminal_ground_shoe',[(.194,.41),(-.164,.164),(0,.13)],wood,.021,True)
box('terminal_foot_transition',[(.205,.402),(-.149,.149),(.115,.155)],strip,.008,True)
box('terminal_cap_seat',[(.199,.405),(-.162,.162),(.868,.931)],strip,.011)
box('terminal_crowned_cap',[(.19,.41),(-.18,.18),(.915,1.02)],wood,.026)
# One shallow, structural raised panel on either broad post face. Its long
# contour explains a framed shaft at game scale without tiny ornaments.
for sign in[-1,1]:
 box('shaft_field_'+str(sign),[(.235,.375),(sign*.141-.004,sign*.141+.004),(.19,.838)],wood,.006,True)
# All source-only debris removed; selected scene owns only asset/camera/lights.
owned=set(collection.all_objects)|{o for o in scene.objects if o.type in ['CAMERA','LIGHT']}
for o in list(bpy.data.objects):
 if o not in owned:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=collection and c.users==0:bpy.data.collections.remove(c)
for im in list(bpy.data.images):bpy.data.images.remove(im)
bpy.data.orphans_purge(do_recursive=True)
cam=scene.camera;cam.matrix_world=Matrix(family['capture']['camera']['worldMatrix'])
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=family['capture']['camera']['shift'][1]
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.pixel_aspect_x=family['capture']['pixelAspect'][0];scene.render.pixel_aspect_y=1
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU'
scene['asset_id']='wall-end';scene['family']=family['family'];scene['round']=R;scene['native_only']=True
rows=lambda m:[list(r)for r in m]
def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return[p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y]
def register(w,h,rootpix):
 scene.render.resolution_x=w;scene.render.resolution_y=h;cam.data.ortho_scale=w/256;cam.data.shift_y=0;bpy.context.view_layer.update();base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0))[1]-base[1];cam.data.shift_y=(rootpix[1]-base[1])/dy;bpy.context.view_layer.update()
def bounds(objects=None):
 dg=bpy.context.evaluated_depsgraph_get();pts=[o.matrix_world@v.co for o in(objects or collection.all_objects)if o.type=='MESH'for v in o.evaluated_get(dg).data.vertices];return[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
def sections():return{o.name:sorted(set((round(v.co.y,7),round(v.co.z,7))for v in o.data.vertices if abs(v.co.x+.5)<1e-6))for o in collection.all_objects if o.type=='MESH'and 'terminal_'not in o.name and 'shaft_field_'not in o.name}
root.rotation_euler.z=0;bpy.context.view_layer.update();initial_bounds=bounds();wprofile=sections()
cal={k:pixel(v)for k,v in{'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()};cal={k:(p if k=='root'else[p[i]-cal['root'][i]for i in range(2)])for k,p in cal.items()}
project=B/'source'/f'{R}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(project),check_existing=False)
# Read-only append approved neighbor AFTER candidate save, for native evidence.
with bpy.data.libraries.load(str(F),link=False)as(src,dst):dst.collections=['S33_PROP_wall-middle.001']
neighbor=dst.collections[0];scene.collection.children.link(neighbor);neighbor.hide_render=True;neighbor.hide_viewport=False
nroot=next(o for o in neighbor.all_objects if o.type=='EMPTY');nroot.rotation_euler=(0,0,0)
records=[]
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();neighbor.hide_render=True
 path=O/'raw'/f'static-{direction}-0000.png';path.parent.mkdir(exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'kind':'single','direction':direction,'clip':'static','index':0,'path':str(path.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'cameraWorldMatrix':rows(cam.matrix_world),'resolution':[384,704],'rootPixel':pixel((0,0,0)),'bounds':bounds()})
 nroot.rotation_euler.z=math.radians(angle);nroot.location=Matrix.Rotation(math.radians(angle),4,'Z')@Vector((-1,0,0));neighbor.hide_render=False;bpy.context.view_layer.update();register(896,1216,(448,768))
 path=O/'native-joins'/f'static-{direction}-W-neighbor.png';path.parent.mkdir(exist_ok=True);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 p1=root.matrix_world@Vector((-.5,0,0));p2=nroot.matrix_world@Vector((.5,0,0))
 records.append({'kind':'native-join','direction':direction,'path':str(path.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'neighborRootMatrix':rows(nroot.matrix_world),'placementsWorld':[list(root.location),list(nroot.location)],'mainWPortWorld':list(p1),'neighborEPortWorld':list(p2),'portDistance':(p1-p2).length,'resolution':[896,1216],'rootPixel':pixel((0,0,0)),'cameraWorldMatrix':rows(cam.matrix_world),'pixelPitch':256})
 neighbor.hide_render=True;register(384,704,(192,512))
root.rotation_euler.z=0;bpy.context.view_layer.update()
validation={'asset':'wall-end','round':R,'blender':bpy.app.version_string,'project':{'path':str(project.relative_to(B)),'sha256':sha(project)},'source':original,'family':{'project':{'path':str(F.relative_to(B)),'sha256':sha(F)},'settings':{'path':str(FSET.relative_to(B)),'sha256':sha(FSET)},'materialUsage':'Exact native material datablocks from approved family; shaft texture coordinates oriented with physical vertical grain. No material edits.','nativeNeighborSource':str(F.relative_to(B))},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'cellSize':128,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'worldMatrix':rows(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1))},'calibration':cal,'root':root.name,'boundsLocal':initial_bounds,'footprint':[1,1],'functionalHeight':1.02,'ports':json.loads(root['ports']),'rotationsDegrees':{'N':180,'E':90,'S':0,'W':-90}},'geometry':{'selectedObjectOnly':True,'meshCount':len([o for o in collection.all_objects if o.type=='MESH']),'vertices':sum(len(o.data.vertices)for o in collection.all_objects if o.type=='MESH'),'WProfile':wprofile,'connectorPlane':-.5,'bodyTermination':.29,'copingTermination':.235,'terminalBounds':{'x':[.19,.41],'y':[-.18,.18],'z':[0,1.02]},'description':'Family native wall surfaces preserve exact W profile and normals, clipped only where buried inside terminal. Real softened shaft, shoe, collar and crowned wood cap. Raised fields on both post faces; no raster detail.','noGeometryBeyondW':True},'render':family['render'],'lighting':family['lighting'],'renders':records,'dependencies':{'externalImages':[],'linkedLibraries':[],'selfContained':True},'status':'candidate-awaiting-independent-judge'}
(O/'validation.json').write_text(json.dumps(validation,indent=2));camrec=json.loads((B/'inputs/source-camera.json').read_text());camrec.update(captureScale=2,calibration=cal);camrec['camera'].update(validation['capture']['camera']);(O/'native-camera.json').write_text(json.dumps(camrec,indent=2));asset=json.loads((B/'inputs/source-assetRecord.json').read_text());asset['scale']=2;(O/'native-assetRecord.json').write_text(json.dumps(asset,indent=2));shutil.copy2(B/'inputs/source-rig.json',O/'native-rig.json')
print('WALL END COMPLETE',initial_bounds)
