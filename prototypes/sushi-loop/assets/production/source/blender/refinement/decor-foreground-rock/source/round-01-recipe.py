"""Portable editable native rock authoring and exact saved-project capture.
Run blender -b --python this.py [-- --replay saved.blend outputdir].
No external mesh/material/image data are used. Source backup/contract JSON are provenance.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent.parent;SRC=BASE/'source';OUT=BASE/'candidates'/'round-01'
RESOURCE=SRC/'round-01-resources'
ROOT='S33 production concept cobalt-shelf root';COL='S33 production concept cobalt-shelf';SCENE='Foreground Rock Warm Native Round01'
DIRS={'N':180,'E':90,'S':0,'W':-90}
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(m):return [list(r) for r in m]
def lin(h):
 v=[int(h[i:i+2],16)/255 for i in (0,2,4)];return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)+(1,)
def mat(name,side,top):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled')
 bs.inputs['Roughness'].default_value=.82;bs.inputs['Specular IOR Level'].default_value=.14;bs.inputs['IOR'].default_value=1.45
 geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
 ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.15;ramp.inputs['From Max'].default_value=.92;ramp.inputs['To Min'].default_value=0;ramp.inputs['To Max'].default_value=1;l.new(sep.outputs['Z'],ramp.inputs['Value'])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';l.new(ramp.outputs['Result'],mix.inputs[0]);mix.inputs[1].default_value=lin(side);mix.inputs[2].default_value=lin(top)
 pos=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],pos.inputs[0]);height=n.new('ShaderNodeMapRange');l.new(pos.outputs['Z'],height.inputs[0]);height.inputs['From Min'].default_value=0;height.inputs['From Max'].default_value=1.075;height.inputs['To Min'].default_value=.72;height.inputs['To Max'].default_value=1.04
 mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(mix.outputs[0],mult.inputs[1]);l.new(height.outputs[0],mult.inputs[2]);l.new(mult.outputs[0],bs.inputs['Base Color']);l.new(mult.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.08
 l.new(bs.outputs[0],out.inputs['Surface']);m.diffuse_color=lin(side);return m

def stone(col,root,name,cx,cy,w,d,h,phase,seed,n=8):
 # Solid low-frequency polyhedral rock. Irregular convex natural form replaces
 # the old extruded eight-sided columns; flattened ends establish broad crown/contact.
 import bmesh
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
 ob=bpy.context.object;ob.name=name
 for c in list(ob.users_collection):c.objects.unlink(ob)
 col.objects.link(ob);ob.parent=root
 for v in ob.data.vertices:
  p=v.co.copy();a=math.atan2(p.y,p.x);rad=1+.12*math.sin(a*3+seed*1.7)+.055*math.cos(p.z*4+a*2+seed)
  xx=p.x*rad;yy=p.y*rad
  # Lean and asymmetry form purposeful wedge-like stone, never a perfect gem.
  xx+=.08*p.z*math.sin(seed);yy+=.07*p.z*math.cos(seed)
  v.co.x=cx+w*.52*(xx*math.cos(phase)-yy*math.sin(phase));v.co.y=cy+d*.52*(xx*math.sin(phase)+yy*math.cos(phase));v.co.z=max(-.75,min(.77,p.z+.06*math.sin(a*2+seed)))*h/1.52+h*.75/1.52
 ob.data.update();bpy.context.view_layer.objects.active=ob
 # Collapse low-frequency surfaces into broad sculpted facets, retain polygonal stone contours.
 dec=ob.modifiers.new('Broad sculpted stone facets','DECIMATE');dec.ratio=.48;bpy.ops.object.modifier_apply(modifier=dec.name)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.dissolve_limit(bm,angle_limit=.35,use_dissolve_boundaries=False,verts=list(bm.verts),edges=list(bm.edges));bm.to_mesh(ob.data);bm.free();ob.data.update()
 for m in MATS:ob.data.materials.append(m)
 for p in ob.data.polygons:p.material_index=1 if (p.index+seed)%13==0 else 2 if (p.index+seed)%17==0 else 0;p.use_smooth=False
 be=ob.modifiers.new('Real softly worn edges','BEVEL');be.width=.022 if h>.7 else .015;be.segments=4;be.limit_method='ANGLE';be.angle_limit=.12;be.harden_normals=True;bpy.ops.object.modifier_apply(modifier=be.name)
 for p in ob.data.polygons:p.use_smooth=p.area<.0018
 norm=ob.modifiers.new('Broad stable facet normals','WEIGHTED_NORMAL');norm.keep_sharp=True;norm.weight=55;norm.thresh=.01;bpy.ops.object.modifier_apply(modifier=norm.name)
 low=min(v.co.z for v in ob.data.vertices)
 for v in ob.data.vertices:v.co.z-=low
 ob.data.update()
 ob['nativeConstruction']='irregular solid convex polyhedral stone; broad decimated native facets; flattened crown and ground contact; real 4 segment worn bevel';ob.select_set(False);return ob

def allpoints(col):
 dg=bpy.context.evaluated_depsgraph_get();p=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);me=e.to_mesh();p.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
 return p
def bounds(p):return {'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]}
def config(sc):
 r=sc.render;r.engine='BLENDER_EEVEE';r.resolution_x=384;r.resolution_y=704;r.resolution_percentage=100;r.pixel_aspect_x=1.2206555604934692;r.pixel_aspect_y=1;r.film_transparent=True;r.image_settings.file_format='PNG';r.image_settings.color_mode='RGBA';r.image_settings.color_depth='8';r.dither_intensity=0;r.fps=12;r.use_compositing=False;r.use_persistent_data=True;sc.eevee.taa_render_samples=96
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 cam=sc.camera;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.clip_start=.1;cam.data.clip_end=1000
 rec=json.loads((RESOURCE/'source-camera.json').read_text());cam.matrix_world=Matrix(rec['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def py():return (1-world_to_camera_view(sc,cam,Vector((0,0,0))).y)*704
 b=py();cam.data.shift_y=1;bpy.context.view_layer.update();dy=py()-b;cam.data.shift_y=(512-b)/dy;bpy.context.view_layer.update();sc.frame_set(1)
def camera(sc):
 cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get()
 def pix(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*704]
 root=pix((0,0,0));axes={name:[x-y for x,y in zip(pix(p),root)] for name,p in {'unitX':(1,0,0),'unitDepth':(0,-1,0),'unitHeight':(0,0,1)}.items()}
 return {'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,256],'cellSize':128,'captureScale':2,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dg,x=384,y=704,scale_x=sc.render.pixel_aspect_x,scale_y=1)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797890615988,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':root,**axes},'nativeCaptureScale':2,'nativeResolution':[384,704],'publishedResolution':[384,704]}
def build():
 global MATS
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name=SCENE;col=bpy.data.collections.new(COL);sc.collection.children.link(col);root=bpy.data.objects.new(ROOT,None);col.objects.link(root)
 root['production_id']='decor-foreground-rock';root['sourceProjectSHA256']=sha(SRC/'original-library.blend');root['native_action_record']=json.dumps({'assetId':'decor-foreground-rock','clips':{'static':[]}})
 MATS=[mat('Cobalt stone / softly cyan turning planes','1E66D9','45ADE4'),mat('Cobalt secondary facet','2170DA','51B4E7'),mat('Cobalt deep fracture facet','205FCA','409FD8')]
 stone(col,root,'Broad asymmetrical crown',.035,.13,.81,.76,1.075,.08,1,8)
 stone(col,root,'Left stepping shoulder',-.30,.20,.45,.52,.75,.26,2,7)
 stone(col,root,'Front middle fractured buttress',-.04,-.16,.57,.47,.70,.12,3,7)
 stone(col,root,'Low front left stone',-.265,-.30,.54,.46,.415,.19,4,7)
 stone(col,root,'Right ledge stone',.315,-.265,.44,.53,.59,-.14,5,7)
 stone(col,root,'Rear broad lower buttress',-.05,.37,.70,.49,.67,.32,6,7)
 stone(col,root,'Right low weathered buttress',.31,.08,.42,.62,.56,.12,7,7)
 # Envelope normalization is one common authored geometry transform, never camera fitting.
 p=allpoints(col);b=bounds(p)
 for o in col.objects:
  if o.type!='MESH':continue
  for v in o.data.vertices:
   for i in range(2):v.co[i]=(v.co[i]-b['min'][i])/(b['max'][i]-b['min'][i])-0.5
   v.co.z=(v.co.z-b['min'][2])/(b['max'][2]-b['min'][2])*1.0750000476837158
  o.data.update()
 cam=bpy.data.objects.new('Registered 55 degree square grid camera',bpy.data.cameras.new('Registered square grid camera'));sc.collection.objects.link(cam);sc.camera=cam;config(sc)
 roles=[('Broad warm overhead',(0,0,4.5),185,3.5,(1,.95,.87))]
 for i in range(8):
  a=i*math.tau/8;roles.append(('Symmetric fill %d'%i,(3*math.cos(a),3*math.sin(a),1.9),28,4,(.9,.96,1)))
 for name,pos,power,size,color in roles:
  ld=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,ld);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.5))-ob.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
 sc.world=bpy.data.worlds.new('Symmetric soft blue studio');sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.86,.9,1,1);bg.inputs['Strength'].default_value=.10
 sc['sourceContract']='registered55degreeSquareGrid';sc['noGroundReceiver']=True;sc['staticClip']='1 frame;12fps;nonloop';root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
 write(SRC/'round-01-settings.json',{'asset':'decor-foreground-rock','briefSHA256':sha(RESOURCE/'frozen-brief.json'),'sourceBackupSHA256':sha(SRC/'original-library.blend'),'camera':camera(sc),'renderer':{'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'colorManagement':'Standard/None/exposure0/gamma1','nativeDirect2x':True},'modeling':'seven native irregular sculpted stones with broad fractured facets and real worn bevels; all mesh vertices editable','lighting':'central warm overhead plus eight equal evenly spaced blue-neutral fills; no ground receiver','resources':[]})
 bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'round-01.blend'),compress=True);return sc,col,root

def capture(sc,col,root,out):
 out.mkdir(parents=True,exist_ok=True);audits={};root.rotation_euler=(0,0,0);bpy.context.view_layer.update();canonical=bounds(allpoints(col))
 for d,deg in DIRS.items():
  root.rotation_euler=(0,0,math.radians(deg));bpy.context.view_layer.update();audits[d]={'degrees':deg,'rootMatrix':rows(root.matrix_world),'evaluatedWorldBounds':bounds(allpoints(col)),'camera':camera(sc)}
  sc.render.filepath=str(out/'raw'/f'static-{d}'/'000.png');Path(sc.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
 root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
 write(out/'native-audit.json',{'asset':'decor-foreground-rock','scene':sc.name,'openedProject':bpy.data.filepath,'openedProjectSHA256':sha(Path(bpy.data.filepath)),'collection':COL,'root':ROOT,'canonicalRootMatrix':rows(root.matrix_world),'evaluatedRootLocalBounds':canonical,'facings':audits,'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'evaluatedBounds':bounds([o.matrix_world@v.co for v in o.data.vertices]),'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]} for o in col.objects if o.type=='MESH'],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'position':list(o.location),'rotation':list(o.rotation_euler),'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'materials':[{'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{i.name:(list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if hasattr(i,'default_value') and i.type in ('VALUE','RGBA','VECTOR','INT','BOOLEAN')}} for n in m.node_tree.nodes],'links':[{'from':l.from_node.name+':'+l.from_socket.name,'to':l.to_node.name+':'+l.to_socket.name} for l in m.node_tree.links]} for m in bpy.data.materials],'camera':camera(sc),'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'compositing':sc.render.use_compositing,'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'frame':sc.frame_current,'fps':sc.render.fps,'actions':[a.name for a in bpy.data.actions],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'shapeKeys':[o.name for o in col.objects if o.type=='MESH' and o.data.shape_keys],'externalImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'externalLibraries':[l.filepath for l in bpy.data.libraries],'nonMeshRootChildren':[o.name for o in root.children if o.type!='MESH'],'ports':{},'sockets':{},'noGroundReceiver':not any(o.type=='MESH' and o.name not in col.objects for o in sc.objects)})
 write(out/'records'/'camera.json',camera(sc));asset=json.loads((RESOURCE/'source-assetRecord.json').read_text());asset.update(scale=2,artStyle={'revision':'warm-soft-cartoon-native-round01','lighting':'central overhead/eight symmetric fills','geometry':'asymmetric broad sculpted stone bank with real worn edges'},height=1.05);write(out/'records'/'asset.json',asset);write(out/'records'/'rig.json',json.loads((RESOURCE/'source-rig.json').read_text()))
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if args and args[0]=='--replay':
  bpy.ops.wm.open_mainfile(filepath=str(Path(args[1]).resolve()));sc=bpy.data.scenes[SCENE];bpy.context.window.scene=sc;capture(sc,bpy.data.collections[COL],bpy.data.objects[ROOT],Path(args[2]).resolve())
 else:
  sc,col,root=build();capture(sc,col,root,OUT)
