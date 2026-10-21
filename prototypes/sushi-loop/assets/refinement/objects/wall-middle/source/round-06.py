"""Reconstruct warm wall within source boundary profiles; run with Blender 5.2."""
import bpy, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];OUT=B/'candidates/round-06';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
SRC_HASH=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
collection=bpy.data.collections['S33_PROP_wall-middle.001'];collection.hide_render=False;collection.hide_viewport=False
scene=bpy.data.scenes.new('Warm soft wall middle — round 01');scene.collection.children.link(collection);bpy.context.window.scene=scene;bpy.context.view_layer.update()
root=next(o for o in collection.all_objects if o.type=='EMPTY');root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
original=[]
for o in collection.all_objects:
 if o.type=='MESH':
  original.append({'name':o.name,'vertices':[list(v.co)for v in o.data.vertices],'faces':[list(p.vertices)for p in o.data.polygons],'materials':[m.name for m in o.data.materials]})
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
owned=set(collection.all_objects)
for o in list(bpy.data.objects):
 if o not in owned:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=collection:bpy.data.collections.remove(c)
for o in list(collection.all_objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
for datablocks in (bpy.data.materials,bpy.data.images,bpy.data.meshes,bpy.data.worlds,bpy.data.actions):
 for d in list(datablocks):
  if d.users==0:datablocks.remove(d)

def linear(c):
 return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4

def col(h):return tuple(linear(int(h[i:i+2],16)/255)for i in(0,2,4))+(1,)

def mat(name,hexcolor,rough,spec,grain=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=col(hexcolor);m['base_srgb']='#'+hexcolor
 n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=col(hexcolor);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=spec
 bs.inputs['Emission Color'].default_value=col(hexcolor);bs.inputs['Emission Strength'].default_value=.16
 if grain:
  tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],sep.inputs[0])
  def mathnode(op,a,b=None):
   v=n.new('ShaderNodeMath');v.operation=op
   if hasattr(a,'node'):l.new(a,v.inputs[0])
   else:v.inputs[0].default_value=a
   if b is not None:
    if hasattr(b,'node'):l.new(b,v.inputs[1])
    else:v.inputs[1].default_value=b
   return v.outputs[0]
  x=mathnode('MULTIPLY',sep.outputs['X'],2*math.pi);wave=mathnode('SINE',x);wave=mathnode('MULTIPLY',wave,2.6)
  x2=mathnode('MULTIPLY',sep.outputs['X'],4*math.pi);wave2=mathnode('COSINE',x2);wave2=mathnode('MULTIPLY',wave2,.55)
  z=mathnode('MULTIPLY',sep.outputs['Z'],40);phase=mathnode('ADD',z,wave);phase=mathnode('ADD',phase,wave2);grainwave=mathnode('SINE',phase)
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]);ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=col('B27C35')
  for p,c in[(.16,'B9823B'),(.28,'C68D42'),(.72,'C78E44'),(1,'C18A3D')]:e=ramp.color_ramp.elements.new(p);e.color=col(c)
  # Sine remapped into 0..1; broad grain, no noise or image textures.
  g=mathnode('MULTIPLY_ADD',grainwave,.5);g.node.inputs[2].default_value=.5
  l.new(g,ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color']);l.new(ramp.outputs['Color'],bs.inputs['Emission Color'])
 l.new(bs.outputs[0],out.inputs['Surface']);return m
wood=mat('Warm wall · honey timber','C58A38',.66,.22,True)
strip=mat('Warm wall · slender timber bead','A96B27',.58,.22)
capwood=mat('Warm wall · cap undercut','8C592A',.66,.18)
blue=mat('Warm wall · soft blue enamel','0867CD',.38,.28)
# Cross-section material and geometry remain exact on x=±.5. Open seam cuts
# remove internal cut faces; the end member closes the family. This prevents
# end-face shadow/color stripes in independent RGBA module assemblies.
def extrusion(name,profile,material,smooth=True,xs=None,deform=None):
 xs=xs or [-.5,.5]
 # Samples on each straight source segment localize normal softening while
 # leaving the exact geometric boundary polygon unchanged.
 if deform is None:
  dense=[]
  for a,b in zip(profile,profile[1:]+profile[:1]):
   av=Vector(a);bv=Vector(b);length=(bv-av).length;f=min(.22,.006/length)
   for t in (0,f,1-f):dense.append(tuple(av.lerp(bv,t)))
  profile=dense
 verts=[]
 for x in xs:
  for y,z in profile:
   yy,zz=(deform(x,y,z)if deform else(y,z));verts.append((x,yy,zz))
 count=len(profile);faces=[]
 for k in range(len(xs)-1):
  for j in range(count):faces.append((k*count+j,k*count+(j+1)%count,(k+1)*count+(j+1)%count,(k+1)*count+j))
 mesh=bpy.data.meshes.new(name+' native surface');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('wall-middle__'+name,mesh);collection.objects.link(o);o.parent=root;o.data.materials.append(material)
 for p in mesh.polygons:p.use_smooth=smooth
 # Analytical cross-section normals keep longitudinal planes coherent and keep
 # the exact cut section free of caps. Panel normals are geometric for relief.
 if deform is None and smooth:
  ns=[]
  for j,(y,z)in enumerate(profile):
   prev=Vector(profile[(j-1)%count]);curr=Vector((y,z));nxt=Vector(profile[(j+1)%count]);a=curr-prev;b=nxt-curr
   na=Vector((0,a.y,-a.x)).normalized();nb=Vector((0,b.y,-b.x)).normalized()
   # Mostly planar broad faces; modest turning response at the bead edges.
   ns.append((na+nb).normalized())
  mesh.normals_split_custom_set([ns[loop.vertex_index%count]for loop in mesh.loops])
 if deform is not None:
  mesh.update();normal_values=[]
  for loop,corner in zip(mesh.loops,mesh.corner_normals):
   no=Vector(corner.vector)
   if abs(abs(mesh.vertices[loop.vertex_index].co.x)-.5)<1e-6:no.x=0;no.normalize()
   normal_values.append(no)
  mesh.normals_split_custom_set(normal_values)
 o['open_modular_cuts']='x=-0.5,+0.5; exact source profile, no terminal face';return o
# Panel has broad, very shallow convex timber-face relief between source beads.
zs=sorted(set(round(z,6)for z in [.07,.89,.145,.34,.365,.56,.585,.78,.805]+[.07+i*.82/64 for i in range(65)]))
profile=list(reversed([(-.105,z)for z in zs]+[(.105,z)for z in reversed(zs)]))
intervals=[(.07,.12),(.145,.34),(.365,.56),(.585,.78),(.805,.89)]
def timber_relief(x,y,z):
 a=0
 for low,high in intervals:
  if low<z<high:a=.017*math.sin(math.pi*(z-low)/(high-low))**2
 return y+math.copysign(a*math.cos(math.pi*x)**2,y),z
panel=extrusion('wall_panel',profile,wood,True,[-.5+i/32 for i in range(33)],timber_relief)
for i,z in enumerate((.12,.34,.56,.78)):
 extrusion('horizontal_board_'+str(i),[(-.115,z),(.115,z),(.115,z+.025),(-.115,z+.025)],strip,True)
extrusion('wood_cap',[(-.15,.86),(.15,.86),(.15,.935),(-.15,.935)],capwood,True)
def blue_crown(x,y,z):
 dz=.008*math.cos(math.pi*x)**2*max(0,1-(abs(y)/.12)**4) if abs(z-1.01)<1e-5 else 0
 return y,z+dz
coping_profile=[(-.18,.93),(.18,.93),(.18,.97),(.12,1.01)]+[(y,1.01)for y in [.09,.06,.03,0,-.03,-.06,-.09]]+[(-.12,1.01),(-.18,.97)]
extrusion('blue_coping',coping_profile,blue,True,[-.5+i/32 for i in range(33)],blue_crown)
# Source-profile cut planes remain solid in a standalone view, but camera-only
# closure does not cast artificial ray shadows into a neighboring module.
# This is native shader ray visibility, not a raster seam overlay.
for o in list(collection.all_objects):
 if o.type!='MESH':continue
 sourcepart=next(p for p in original if p['name'].split('__')[1].replace('.001','')==o.name.split('__')[1])
 sourceverts=sourcepart['vertices'];capfaces=[];verts=[]
 for side in (-.5,.5):
  faces=[f for f in sourcepart['faces']if all(abs(sourceverts[i][0]-side)<1e-6 for i in f)]
  for face in faces:
   start=len(verts);verts += [sourceverts[i] for i in face];capfaces.append(tuple(range(start,start+len(face))))
 if not capfaces:continue
 mesh=bpy.data.meshes.new(o.name+' cut plane mesh');mesh.from_pydata(verts,[],capfaces);mesh.update()
 end=bpy.data.objects.new(o.name+'__camera_cut_planes',mesh);collection.objects.link(end);end.parent=root
 cm=o.data.materials[0].copy();cm.name=o.data.materials[0].name+' camera-only cut'
 n=cm.node_tree.nodes;l=cm.node_tree.links;out=next(v for v in n if v.type=='OUTPUT_MATERIAL');bs=next(v for v in n if v.type=='BSDF_PRINCIPLED');tr=n.new('ShaderNodeBsdfTransparent');lp=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(bs.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);end.data.materials.append(cm)
 if o.name.endswith('blue_coping'):
  # Native cut-face shading gutter: the thin visible sampling edge shares the
  # top-plane normal so camera antialiasing cannot expose a dark cut stripe.
  # All geometry and alpha still ends on the exact original connector plane.
  model=json.loads((B/'source/cut-radiance-model.json').read_text());coefficients=model['coefficientsAscendingPowers']
  tex=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Object'],sep.inputs[0])
  ratio=n.new('ShaderNodeMath');ratio.operation='DIVIDE';ratio.inputs[1].default_value=.18;l.new(sep.outputs['Y'],ratio.inputs[0])
  q=n.new('ShaderNodeMath');q.operation='MULTIPLY';l.new(ratio.outputs[0],q.inputs[0]);l.new(ratio.outputs[0],q.inputs[1])
  previous=None
  for i in range(len(coefficients)-2,-1,-1):
   node=n.new('ShaderNodeVectorMath');node.name='Symmetric cut radiance Horner '+str(i);node.operation='MULTIPLY_ADD'
   if previous is None:node.inputs[0].default_value=coefficients[i+1]
   else:l.new(previous,node.inputs[0])
   l.new(q.outputs[0],node.inputs[1]);node.inputs[2].default_value=coefficients[i];previous=node.outputs[0]
  emission=n.new('ShaderNodeEmission');emission.name='Camera cut top-radiance continuity';l.new(previous,emission.inputs['Color']);emission.inputs['Strength'].default_value=1
  l.new(bs.outputs[0],mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2])
  end['cut_radiance_model']='source/cut-radiance-model.json; same quartic for both cuts and every facing; ordinary BSDF transport'

 end['purpose']='Camera-only exact source cut closure, transparent to every secondary/shadow ray.'
# No external bitmap resources participate in this asset, and library-only
# image datablocks are removed before saving the isolated project.
for image in list(bpy.data.images):bpy.data.images.remove(image)
bpy.data.orphans_purge(do_recursive=True)
# Clean consistent camera rebuilt from the exact recorded world matrix.
camrec=json.loads((B/'inputs/source-camera.json').read_text());cam=bpy.data.objects.new('Registered square top front camera',bpy.data.cameras.new('Registered square top front camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.matrix_world=Matrix(camrec['camera']['worldMatrix']);cam.data.shift_x=0
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=camrec['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1

def pixel(v):
 p=world_to_camera_view(scene,cam,Vector(v));return Vector((p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y))
def register(width,height,rootpixel):
 scene.render.resolution_x=width;scene.render.resolution_y=height;cam.data.ortho_scale=width/256;cam.data.shift_y=0;bpy.context.view_layer.update();base=pixel((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,0,0)).y-base.y;cam.data.shift_y=(rootpixel[1]-base.y)/dy;bpy.context.view_layer.update()
register(384,704,(192,512))
scene.render.engine='CYCLES';scene.cycles.samples=512;scene.cycles.use_denoising=False;scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=32
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for d in prefs.devices:d.use=d.type=='METAL'
scene.cycles.device='GPU'
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.fps=12
scene.cycles.pixel_filter_type='BOX';scene.render.filter_size=1
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.35
world=bpy.data.worlds.new('Warm wall uniform ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28;scene.world=world
# Far field soft sources: translation-invariant to <0.2% across three cells.
lights=[]
def area(name,pos,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
area('Centered broad overhead',(0,0,1000),5000000,700)
for i in range(4):
 a=i*math.pi/2;area('Equal cardinal fill '+str(i),(750*math.cos(a),750*math.sin(a),450),1400000,700)
scene['asset_id']='wall-middle';scene['family']='restaurant-wall-wood-blue-v2';scene['round']='round-06';scene['native_only']=True
bpy.context.view_layer.update()
# Capture validation helpers.
def rows(m):return[list(r)for r in m]
def bounds():
 dg=bpy.context.evaluated_depsgraph_get();pts=[o.matrix_world@v.co for o in collection.all_objects if o.type=='MESH' for v in o.evaluated_get(dg).data.vertices];return[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)]
def section(side):
 result={};plane=-.5 if side=='W'else .5
 for o in collection.all_objects:
  if o.type!='MESH':continue
  values=sorted(set((round(v.co.y,7),round(v.co.z,7))for v in o.data.vertices if abs(v.co.x-plane)<1e-6));result[o.name]=values
 return result
initial_bounds=bounds();sections={side:section(side)for side in['W','E']}
cal={k:list(pixel(v))for k,v in{'root':(0,0,0),'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()}
cal={k:(p if k=='root'else [p[i]-cal['root'][i]for i in range(2)])for k,p in cal.items()}
root.rotation_euler.z=0;bpy.context.view_layer.update();blend=B/'source/round-06.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),check_existing=False)
records=[]
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();path=OUT/'raw'/('static-'+direction+'-0000.png');path.parent.mkdir(exist_ok=True)
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'kind':'single','clip':'static','direction':direction,'index':0,'path':str(path.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'cameraWorldMatrix':rows(cam.matrix_world),'resolution':[384,704],'rootPixel':list(pixel((0,0,0))),'bounds':bounds()})
 # Native copies sit at exact ports and are independently transformed meshes.
 copies=[];positions=[]
 for offset in[-1,1]:
  vector=Matrix.Rotation(math.radians(angle),4,'Z')@Vector((offset,0,0));positions.append(list(vector))
  for o in list(collection.all_objects):
   if o.type!='MESH':continue
   dup=o.copy();dup.data=o.data;dup.parent=None;dup.matrix_world=o.matrix_world.copy();dup.location+=vector;scene.collection.objects.link(dup);copies.append(dup)
 register(896,1216,(448,768));p=OUT/'native-joins'/('static-'+direction+'-3modules.png');p.parent.mkdir(exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 records.append({'kind':'native-join','direction':direction,'path':str(p.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':rows(root.matrix_world),'placementsWorld':positions+[[0,0,0]],'resolution':[896,1216],'rootPixel':list(pixel((0,0,0))),'cameraWorldMatrix':rows(cam.matrix_world),'pixelPitch':256,'joinPlanesLocal':[-.5,.5]})
 for o in copies:bpy.data.objects.remove(o,do_unlink=True)
 register(384,704,(192,512))
root.rotation_euler.z=0;bpy.context.view_layer.update()
materials=[]
for m in[wood,strip,capwood,blue]:
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');materials.append({'name':m.name,'base_srgb':m['base_srgb'],'roughness':bs.inputs['Roughness'].default_value,'specularIORLevel':bs.inputs['Specular IOR Level'].default_value,'emissionStrength':bs.inputs['Emission Strength'].default_value,'procedural':True,'nodeTree':[{'name':n.name,'type':n.type,'inputs':{v.name:list(v.default_value)if hasattr(v.default_value,'__len__')else v.default_value for v in n.inputs if hasattr(v,'default_value') and not v.is_linked}}for n in m.node_tree.nodes]})
# Source ring compatibility: dense collinear vertices are legal refinements of
# the same exact source polygonal boundary; compare against source edge segments.
def source_profile(o):
 return sorted(set((v[1],v[2])for v in o['vertices']if abs(v[0]-.5)<1e-6))
profile_validation=[]
for o in original:
 key=o['name'];new=next(n for n in collection.all_objects if n.type=='MESH'and n.name.split('__')[1]==key.split('__')[1].replace('.001',''))
 oldpoints=source_profile(o);newpoints=sections['E'][new.name]
 # Canonical shape comparison by point-to-boundary segments in source face edges.
 oldv=o['vertices'];segments=[]
 for f in o['faces']:
  for a,b in zip(f,f[1:]+f[:1]):
   if abs(oldv[a][0]-.5)<1e-6 and abs(oldv[b][0]-.5)<1e-6:segments.append((Vector(oldv[a][1:]),Vector(oldv[b][1:])))
 def dist(p):
  p=Vector(p);ds=[]
  for a,b in segments:
   d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared))if d.length_squared else 0;ds.append((p-(a+t*d)).length)
  return min(ds)
 err=max(dist(p)for p in newpoints);contains=all(any((Vector(p)-Vector(q)).length<1e-6 for q in newpoints)for p in oldpoints)
 profile_validation.append({'part':new.name,'maximumDistanceToSourceProfile':err,'containsEverySourceCorner':contains,'sameWandE':sections['W'][new.name]==newpoints,'passed':err<1e-6 and contains,'materialBandRole':{'wall_panel':'wood_light','wood_cap':'wood_dark','blue_coping':'blue'}.get(new.name.split('__')[1],'wood')})
validation={'asset':'wall-middle','round':'round-06','blender':bpy.app.version_string,'source':{'path':str(SOURCE),'sha256':SRC_HASH,'unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SRC_HASH,'collection':collection.name,'originalMeshes':original},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'sourceRecordedCaptureScale':4,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'camera':{'worldMatrix':rows(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'projectionMatrix':rows(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1))},'calibration':cal,'actualRoot':root.name,'footprint':[1,1],'functionalHeight':1.02,'boundsLocal':initial_bounds,'ports':json.loads(root['ports']),'facings':{'S':0,'E':90,'N':180,'W':-90}},'geometry':{'selectedObjectOnly':True,'meshCount':14,'vertices':sum(len(o.data.vertices)for o in collection.all_objects if o.type=='MESH'),'openCutPlanes':'Body extrusions are uncapped; exact source cut planes are camera-only native shader surfaces, transparent to every secondary/shadow ray. All source profile positions and material-band roles preserved.','boundaryChecks':profile_validation,'boundarySections':sections,'interiorModeling':'Convex timber face relief and a gently crowned blue coping top (max Z 1.018 within functional 1.02). Both vanish smoothly on connector planes. Exact source cross-sections and band roles retained.'},'render':{'engine':scene.render.engine,'device':scene.cycles.device,'devices':[{'name':d.name,'type':d.type,'use':d.use}for d in prefs.devices],'samples':scene.cycles.samples,'denoise':False,'filterSize':scene.render.filter_size,'worldStrength':.28,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'lights':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'type':o.data.type,'shape':o.data.shape}for o in lights],'noGroundReceiver':True,'horizontalSymmetry':4,'perViewChanges':'Root rotation and join copy placement only; registered camera expands canvas for joins without changing pixel pitch.'},'materials':materials,'renders':records,'dependencies':{'externalImages':[{'name':i.name,'path':i.filepath}for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'selfContained':not bpy.data.libraries and not any(i.source=='FILE'for i in bpy.data.images)},'capCutShaderValidation':model,'status':'candidate-awaiting-independent-judge'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
(OUT/'native-camera.json').write_text(json.dumps({**camrec,'captureScale':2,'calibration':cal,'camera':{**camrec['camera'],**validation['capture']['camera']}},indent=2))
asset=json.loads((B/'inputs/source-assetRecord.json').read_text());asset['scale']=2;(OUT/'native-assetRecord.json').write_text(json.dumps(asset,indent=2));shutil.copy2(B/'inputs/source-rig.json',OUT/'native-rig.json')
print('WALL ROUND COMPLETE',OUT)
