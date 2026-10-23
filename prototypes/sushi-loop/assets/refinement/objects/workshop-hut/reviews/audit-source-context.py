import bpy, json, pathlib, math, hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
OUT=pathlib.Path(__file__).parent;sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
def active(lc):
 lc.exclude=False;lc.hide_viewport=False
 for c in lc.children:active(c)
for vl in sc.view_layers:active(vl.layer_collection)
ids=['dock-floor','dock-entry','workshop-hut','submarine-yellow','dock-cover']
roots={a:next(o for o in bpy.data.objects if o.get('production_id')==a and o.type=='EMPTY' and not o.parent) for a in ids}
cols={a:roots[a].users_collection[0] for a in ids}
positions={'dock-floor':(0,0,0),'dock-entry':(0,-1.5,0),'workshop-hut':(.78,.35,.23),'submarine-yellow':(-.70,-.42,.23),'dock-cover':(0,0,.23)}
for c in sc.collection.children:c.hide_render=c not in cols.values()
for a in ids:
 cols[a].hide_viewport=False;cols[a].hide_render=False
 for o in cols[a].all_objects:o.hide_viewport=False;o.hide_set(False)
 roots[a].location=positions[a];roots[a].rotation_euler=(0,0,0)
sc.frame_set(1);bpy.context.view_layer.update()
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def geo(a):
 vertices=[];faces=[];parts=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in cols[a].all_objects:
  if o.type!='MESH' or o.hide_render:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];n=len(vertices);vertices+=ps;faces += [tuple(n+i for i in p.vertices) for p in me.polygons]
  parts.append({'name':o.name,'hidden':o.hide_render,'boundsWorld':bounds(ps),'materials':[m.name for m in o.data.materials if m]});ev.to_mesh_clear()
 return {'root':{'name':roots[a].name,'position':list(roots[a].location),'rotation':list(roots[a].rotation_euler),'scale':list(roots[a].scale)},'collection':cols[a].name,'boundsWorld':bounds(vertices),'parts':parts,'geometrySHA256':hashlib.sha256(json.dumps({'v':[list(v) for v in vertices],'f':faces},sort_keys=True).encode()).hexdigest()},BVHTree.FromPolygons(vertices,faces)
records={};bvhs={}
for a in ids:records[a],bvhs[a]=geo(a)
overlaps=bvhs['workshop-hut'].overlap(bvhs['dock-cover'])
clearanceRays=[]
for x,y in [(1.03,.54),(1.03,.44),(1.03,.64),(.78,.35)]:
 h=bvhs['dock-cover'].ray_cast(Vector((x,y,3)),Vector((0,0,-1)),4)[0]
 clearanceRays.append({'xy':[x,y],'coverSurfaceFromAbove':list(h) if h else None})
samples=[]
for x in (.38,1.18):
 for y in (-.07,.35,.77):
  hit=bvhs['dock-floor'].ray_cast(Vector((x,y,.24)),Vector((0,0,-1)),1)[0]
  samples.append({'xy':[x,y],'floorHit':list(hit) if hit else None,'hutSupportZ':.2549999761581421,'verticalGap':.2549999761581421-hit.z if hit else None})
door=roots['workshop-hut'].matrix_world@Vector((-.12,-.56,0));socket=json.loads(roots['workshop-hut']['sockets'])['door']
path=[]
for y in (-.21,-.35,-.55,-.75):
 floor=bvhs['dock-floor'].ray_cast(Vector((.66,y,.24)),Vector((0,0,-1)),1)[0]
 path.append({'xy':[.66,y],'deckTop':list(floor) if floor else None,'doorApproachCenter':True})
record={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'mode':'Native source context audit only; no source saved, no candidate grading.','originalCompositionRoots':{a:list(p) for a,p in positions.items()},'nativeAssets':records,'door':{'sourceSocketLocal':socket,'world':list(door),'physicalDoor':'Closed surface panel; no animation/opening. Door-frame panel geometry is not an actual pass-through aperture.','physicalBounds':[p for p in records['workshop-hut']['parts'] if any(s in p['name'] for s in ['door.','door_frame','corner_','body.'])]},'sourceSupportRaySamples':samples,'doorApproachDeckRaySamples':path,'floorContactLimits':'Ray samples are supporting evidence; future candidate contact must use actual paired continuous surface profiles/areas, not these sparse source samples.','resources':{'libraries':[l.filepath for l in bpy.data.libraries],'hutImageTextureNodes':[{'material':m.name,'node':n.name,'image':n.image.name if n.image else None,'filepath':n.image.filepath if n.image else None,'packed':bool(n.image.packed_file) if n.image else None} for m in {m for o in cols['workshop-hut'].all_objects if o.type=='MESH' for m in o.data.materials if m} if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']}}
cam=bpy.data.objects.new('Judge Context Camera',bpy.data.cameras.new('Judge Context Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(json.loads((OUT.parent/'inputs/source-camera.json').read_text())['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=4
sc.render.resolution_x=1024;sc.render.resolution_y=1792;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1.49);sc.render.pixel_aspect_y=1;cam.data.shift_x=0;cam.data.shift_y=0
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*1024,(1-q.y)*1792))
bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(1152-base.y)/dy;bpy.context.view_layer.update();o=px((0,0,0))
record['contextCamera']={'nativeFrame':[1024,1792],'logicalFrame':[512,896],'rootPx':list(o),'unitXPx':list(px((1,0,0))-o),'unitDepthPx':list(px((0,-1,0))-o),'unitHeightPx':list(px((0,0,1))-o),'matrix':[list(x) for x in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'purpose':'Fixed wider diagnostic canvas with unchanged cell/projection; no per-view fitting.'}
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
folder=OUT/'source-context-native';folder.mkdir(exist_ok=True);cols['dock-cover'].hide_render=True
record['coverLimit']='Cover native source bounds included as clearance evidence; uncovered dock/hut/submarine contexts rendered to expose support. Cover static frame is not certified as seamless.'
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 rot=Matrix.Rotation(angle,4,'Z')
 for a in ids:roots[a].location=rot@Vector(positions[a]);roots[a].rotation_euler.z=angle
 bpy.context.view_layer.update();sc.render.filepath=str(folder/(d+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
record['coverHutIntersectionAudit']={'evaluatedVisibleMeshIntersectionPairs':len(overlaps),'firstPairs':overlaps[:20],'coverSurfaceRays':clearanceRays,'scope':'Source geometry only. A later paired candidate cover test is still required; no family approval.'}
(OUT/'native-source-context-v2.json').write_text(json.dumps(record,indent=2))
print('CONTEXT_AUDIT',json.dumps({'door':list(door),'bounds':{a:r['boundsWorld'] for a,r in records.items()},'support':samples,'resources':record['resources']}))
