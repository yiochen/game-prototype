import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';P=B/'source/round-06.blend';F=B/'source/resources/paired-native-v3/dock-floor-round-04.blend';R=O/'native-replay';R.mkdir(exist_ok=True);H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):H(p) for p in [P,F]};bpy.ops.wm.open_mainfile(filepath=str(P));sc=bpy.context.scene;cam=sc.camera;ec=bpy.data.collections['S33_PROP_dock-entry'];er=bpy.data.objects['dock-entry__root']
def conv(v):
 try:return list(v)
 except:return str(v)
def geometry(c):
 dg=bpy.context.evaluated_depsgraph_get();vv=[];ff=[];objects=[]
 for ob in c.all_objects:
  if ob.type!='MESH':continue
  ev=ob.evaluated_get(dg);me=ev.to_mesh();v=[ev.matrix_world@x.co for x in me.vertices];faces=[list(p.vertices) for p in me.polygons];off=len(vv);vv+=v;ff += [[x+off for x in f] for f in faces];objects.append({'name':ob.name,'hideRender':ob.hide_render,'parent':ob.parent.name if ob.parent else None,'matrixWorld':[list(x) for x in ev.matrix_world],'verticesWorld':[list(x) for x in v],'polygons':faces,'normalsWorld':[list((ev.matrix_world.to_3x3()@p.normal).normalized()) for p in me.polygons],'zeroAreaFaces':sum(p.area==0 for p in me.polygons),'verySmallPositiveFaces':sum(0<p.area<1e-12 for p in me.polygons),'materialNames':[m.name for m in ob.data.materials if m]});ev.to_mesh_clear()
 return objects,BVHTree.FromPolygons(vv,ff,all_triangles=False)
def ray(t,x,y):
 p,n,i,d=t.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),3);return None if p is None else {'point':list(p),'normal':list(n)}
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*sc.render.resolution_x/2,(1-q.y)*sc.render.resolution_y/2]
def cal():
 p=px((0,0,0));return {'root':p,'unitX':[a-b for a,b in zip(px((1,0,0)),p)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),p)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),p)],'cameraWorld':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
record={'candidatePacketSHA256':'5e4a1c313176fc0e0474474a0fbc800b3ddd321d9c4076e71da39620a617ba70','sourceSHA256':H(P),'floorSHA256':H(F),'blender':bpy.app.version_string,'savedScene':sc.name,'savedRootMatrix':[list(x) for x in er.matrix_world],'rootProperties':{k:er[k] if isinstance(er[k],(int,float,str,bool)) else conv(er[k]) for k in er.keys()},'savedSettings':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'renderSamples':sc.eevee.taa_render_samples,'size':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'frameCurrent':sc.frame_current,'actions':len(bpy.data.actions),'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'transparent':sc.render.film_transparent,'compositor':sc.use_nodes},'savedCalibration':cal(),'objects':[{'name':x.name,'type':x.type,'hideRender':x.hide_render,'parent':x.parent.name if x.parent else None,'scale':list(x.scale),'loc':list(x.location),'rotation':list(x.rotation_euler),'constraints':[c.type for c in x.constraints],'animated':bool(x.animation_data)} for x in ec.all_objects],'libraries':[{'name':x.name,'path':x.filepath} for x in bpy.data.libraries],'images':[{'name':x.name,'path':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images],'materials':[],'lights':[],'standaloneRenders':[],'pairedRenders':[]}
for m in bpy.data.materials:
 record['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links] if m.use_nodes else []})
for l in sc.objects:
 if l.type=='LIGHT':record['lights'].append({'name':l.name,'type':l.data.type,'location':list(l.location),'rotation':list(l.rotation_euler),'energy':l.data.energy,'color':list(l.data.color),'size':getattr(l.data,'size',None)})
er.rotation_euler.z=0;er.location=(0,0,0);bpy.context.view_layer.update();eg,et=geometry(ec);record['entryGeometry']=eg;record['flightProfiles']=[{'x':x,'samples':[{'y':-.5+i*.0005,'hit':ray(et,x,-.5+i*.0005)} for i in range(1001)]} for x in [-.38,-.25,0,.25,.38]];record['clearanceRays']=[{'x':x,'y':y,'hitAboveFlight':(lambda r: None if r is None else r)(ray(et,x,y))} for x in [-.38,0,.38] for y in [-.49,-.4,-.25,-.1,-1e-6]]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 er.rotation_euler.z=a;bpy.context.view_layer.update();f=R/f'static-{d}.png';assert not f.exists();sc.render.filepath=str(f);bpy.ops.render.render(write_still=True);record['standaloneRenders'].append({'direction':d,'path':str(f.relative_to(O)),'sha256':H(f),'calibration':cal(),'rootMatrix':[list(r) for r in er.matrix_world]})
with bpy.data.libraries.load(str(F),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);fr=bpy.data.objects['dock-floor__root'];fr.location=(0,0,0);fr.rotation_euler.z=0;er.rotation_euler.z=0;er.location=(0,-1.5,0);bpy.context.view_layer.update();fg,ft=geometry(fc);eg,et=geometry(ec);record['pairedEntryGeometry']=eg;record['floorGeometry']=fg;record['boundaryRays']=[{'x':-.39+i*.005,'entry':ray(et,-.39+i*.005,-1.500001),'floor':ray(ft,-.39+i*.005,-1.499999)} for i in range(157)]
sc.render.resolution_x=1280;sc.render.resolution_y=1280;cam.data.ortho_scale=5;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(320-base[1])/dy;bpy.context.view_layer.update()
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 fr.rotation_euler.z=a;er.rotation_euler.z=a;er.location=Matrix.Rotation(a,4,'Z')@Vector((0,-1.5,0));bpy.context.view_layer.update();f=R/f'pair-{d}.png';assert not f.exists();sc.render.filepath=str(f);bpy.ops.render.render(write_still=True);record['pairedRenders'].append({'direction':d,'path':str(f.relative_to(O)),'sha256':H(f),'calibration':cal(),'entryRootMatrix':[list(r) for r in er.matrix_world],'floorRootMatrix':[list(r) for r in fr.matrix_world]})
record['sourceHashesAfter']={str(p):H(p) for p in [P,F]};record['nativeSourcesUnchanged']=record['sourceHashesAfter']==before;(O/'own-native-audit.json').write_text(json.dumps(record,indent=2)+'\n');print('OWN_NATIVE_AUDIT_DONE',record['nativeSourcesUnchanged'])
