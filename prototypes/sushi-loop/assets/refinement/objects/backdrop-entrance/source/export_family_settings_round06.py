import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-06';sc=bpy.context.scene;cam=sc.camera
recipe=json.loads((P/'source/round-06-recipe.json').read_text());val=json.loads((R/'validation.json').read_text())
for c in bpy.data.collections:c.hide_viewport=False
sc.view_layers[0].update()
def serial(x):
 if isinstance(x,(bool,str,int,float)):return x
 try:return [float(v) for v in x]
 except:return None
def nodes(tree):
 out=[]
 for n in tree.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':{str(i)+':'+s.name:serial(s.default_value) for i,s in enumerate(n.inputs) if hasattr(s,'default_value')}}
  for a in ['operation','blend_type','samples','distribution','vector_type','convert_from','convert_to']:
   if hasattr(n,a):d[a]=getattr(n,a)
  if hasattr(n,'color_ramp'):d['colorRamp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  out.append(d)
 return {'nodes':out,'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in tree.links]}
def matrix(o):return [list(r) for r in o.matrix_world]
def project(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
def config(w,h,ortho,shift):
 sc.render.resolution_x=w;sc.render.resolution_y=h;cam.data.ortho_scale=ortho;cam.data.shift_y=shift;sc.view_layers[0].update();o=project((0,-.5,0));x=project((1,-.5,0));z=project((0,-.5,1))
 return {'nativeFrame':[w,h],'logicalFrame':[w//3,h//3],'sourceScale':3,'cellSizeLogical':128,'cameraType':'ORTHO','worldMatrix':matrix(cam),'orthoScale':ortho,'shift':[0,cam.data.shift_y],'pixelAspect':[1,1],'sensorFit':cam.data.sensor_fit,'elevationDegrees':35,'registeredFrontContactPoint':[0,-.5,0],'registeredNativeContact':o,'registeredLogicalContact':[o[0]/3,o[1]/3],'nativeRootOriginProjection':project((0,0,0)),'unitX':[x[i]-o[i] for i in range(2)],'unitZ':[z[i]-o[i] for i in range(2)]}
gate=config(1728,1344,4.5,.2696022093296051);wall=config(576,1344,1.5,.2696022093296051*3)
profiles={};dg=bpy.context.evaluated_depsgraph_get()
for cn,planes in [('S33_PROP_uniform35-gate',[-2,2]),('S33_PROP_uniform35-wall-plain',[-.5,.5])]:
 d={}
 for plane in planes:
  pieces=[]
  for o in bpy.data.collections[cn].objects:
   if o.type!='MESH':continue
   pts=[o.matrix_world@v.co for v in o.data.vertices];pp=[p for p in pts if abs(p.x-plane)<1e-5]
   if not pp:continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();ep=[o.matrix_world@v.co for v in me.vertices];epp=[p for p in ep if abs(p.x-plane)<1e-5]
   pieces.append({'sourcePart':o.name,'materials':[m.name for m in o.data.materials],'rawJoinYZ':sorted(set(tuple(round(p[i],8) for i in [1,2]) for p in pp)),'evaluatedJoinYZ':sorted(set(tuple(round(p[i],8) for i in [1,2]) for p in epp)),'profileGeometryUnchangedFromOriginal':val['protectedJoinPlanes']['geometryAndMatricesUnchanged']});ev.to_mesh_clear()
  d[str(plane)]=pieces
 profiles[cn]=d
mats={m.name:{'diffuseColor':list(m.diffuse_color),'shader':nodes(m.node_tree)} for m in bpy.data.materials if m.name in recipe['materials']}
lights={o.name:{'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'angleRadians':o.data.angle,'useShadow':o.data.use_shadow,'matrix':matrix(o),'rotationEuler':list(o.rotation_euler)} for o in sc.objects if o.type=='LIGHT'}
settings={'schemaVersion':1,'assetFamily':'restaurant-facade','candidate':'backdrop-entrance round-06; approval selection belongs to coordinator/judge','nativeProject':'source/round-06-family-context.blend','nativeProjectSha256':hashlib.sha256((P/'source/round-06-family-context.blend').read_bytes()).hexdigest(),'equivalentSelectedProject':'source/round-06.blend','recipe':'source/round-06-recipe.json','worldName':sc.world.name,'world':nodes(sc.world.node_tree),'materials':mats,'materialRoleMap':{'canopyBlue':'S33_uniform35_blue','canopyBlueLight':'S33_uniform35_blue_light','canopyBlueDark':'S33_uniform35_blue_dark','ochreWall':'S33_uniform35_wall_wood','timber':'S33_uniform35_wood','goldTimber':'S33_uniform35_goldwood','timberHighlight':'S33_uniform35_wood_light','darkTimber':'S33_uniform35_wood_dark','clothRed':'S33_uniform35_red','cream':'S33_uniform35_chalk','threshold':'S33_uniform35_sill','doorway':'S33_uniform35_door','metal':'S33_uniform35_metal','brass':'S33_uniform35_brass'},'protectedProfileMaterialRule':'Use the corresponding __protected_profile variant on shared facade meshes reaching a join plane. Its actual native nodes suppress ray-bevel radius in the outer 4 percent of local Generated X, preventing exposed captured end-cap shading. This is shading only; original profile geometry is unchanged.','lights':lights,'rendering':{**recipe['renderer'],'filmTransparent':True,'imageFormat':'PNG RGBA8','resolutionPercentage':100,'pixelAspect':[1,1],'gamma':sc.view_settings.gamma,'transparentMaxBounces':sc.cycles.transparent_max_bounces,'nativePixelFilter':sc.cycles.pixel_filter_type,'nativeFilterWidth':sc.cycles.filter_width,'denoiser':sc.cycles.denoiser if sc.cycles.use_denoising else None,'useDenoising':sc.cycles.use_denoising,'samples':sc.cycles.samples},'capture':{'gate':gate,'wall':wall},'rootContract':{'nativeObjectOrigin':[0,0,0],'registeredFrontContactPoint':[0,-.5,0],'phase':'S rootRotationZ = 0 radians','rootMatrix':matrix(bpy.data.objects['uniform35-gate__root'])},'joinProfiles':profiles,'horizontalLightContract':{'worldDirectionDependency':'Z only, no X/Y position ramp','sunXDirection':0,'infiniteLightNoDistanceFalloff':True,'localWallLights':False,'paperEmission':'camera ray only, no diffuse/glossy illumination emission','groundObject':None,'groundCastShadow':False},'scopeForFollowOnWall':'Shared palette, native material behavior, lighting, rendering, camera/contact calibration and protected join cross sections are the cohesive family contract. Interior wall geometry and new decorative/architectural parts may change under the user\'s follow-on modeling freedom policy v2; this file imposes no old interior part count.','usage':'Append the named materials, world and infinite sun from the self-contained native project. The wall collection is context-only and source-hidden in the saved library; explicitly unhide collection and objects if rendering it. Use the wall camera numeric configuration above. Wall production remains subject to its own fresh editor/judge review.'}
(R/'family-settings.json').write_text(json.dumps(settings,indent=2));print('FAMILY_SETTINGS',R/'family-settings.json')
