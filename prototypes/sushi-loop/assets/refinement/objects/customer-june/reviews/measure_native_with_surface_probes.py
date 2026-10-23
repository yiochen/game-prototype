import bpy, math,json,sys,hashlib,importlib.util,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).parent;OBJ=OUT.parent;REPO=OBJ.parents[5]
RUNTIME='starter-meals' in bpy.data.filepath
MODE='runtime' if RUNTIME else 'main'
NATIVE=OBJ/'inputs/runtime-variants/external/assets/production/source/blender/native_actions.py' if RUNTIME else REPO/'prototypes/sushi-loop/assets/production/source/blender/native_actions.py'
spec=importlib.util.spec_from_file_location('native_june_independent',NATIVE);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
record=json.loads((OBJ/('inputs/runtime-variants/export/source/customer-june/rig.json' if RUNTIME else 'inputs/source-rig.json')).read_text())
sc=next(s for s in bpy.data.scenes if ('Starter' in s.name if RUNTIME else s.name=='S33 Native Asset Library Export'))
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects[record['groundRootObject']];collection=next(c for c in sc.collection.children if root in list(c.all_objects));objects=list(collection.all_objects);arm=next(o for o in objects if o.type=='ARMATURE');plane=next(o for o in objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');foodroot=plane.parent
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=collection
collection.hide_render=False;collection.hide_viewport=False
for o in objects:o.hide_set(False)
sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
cam=sc.camera or next(o for o in sc.objects if o.type=='CAMERA');sc.camera=cam
saved_camera={'name':cam.name,'world':[list(r) for r in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
receipt=json.loads((OBJ/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(receipt['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*384,(1-q.y)*640]
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(496-base[1])/dy;bpy.context.view_layer.update()
def props(o):
 def conv(v):
  if isinstance(v,(str,int,float,bool)):return v
  try:return [conv(x) for x in v]
  except:return str(v)
 return {k:conv(o[k]) for k in o.keys()}
def bound(vs):
 a=np.array(vs);return {'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist()}
def evaluated(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();vs=[e.matrix_world@v.co for v in m.vertices];polys=[list(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return vs,polys
image=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');packed=bytes(image.packed_file.data) if image.packed_file else None
if packed:(OUT/(MODE+'-packed-food.png')).write_bytes(packed)
uvs={}
for p in plane.data.polygons:
 for li in p.loop_indices:uvs[plane.data.loops[li].vertex_index]=list(plane.data.uv_layers.active.data[li].uv)
static={'mode':MODE,'project':bpy.data.filepath,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'collection':collection.name,'savedCamera':saved_camera,'registeredCamera':{'worldMatrix':[list(r) for r in cam.matrix_world],'ortho_scale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'scale':2,'pixelAspect':[1,1],'rootPx':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1))},'root':{'name':root.name,'props':props(root)},'armature':{'name':arm.name,'bones':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,'useDeform':b.use_deform,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in arm.data.bones]},'food':{'plane':plane.name,'root':foodroot.name,'props':props(plane),'vertices':[list(v.co) for v in plane.data.vertices],'uvs':uvs,'image':image.name,'imageDimensions':list(image.size),'filepath':image.filepath,'packedSHA256':hashlib.sha256(packed).hexdigest() if packed else None,'drivers':[{ 'path':c.data_path,'index':c.array_index,'expression':c.driver.expression,'variables':[{'name':v.name,'dataPath':v.targets[0].data_path,'owner':v.targets[0].id.name} for v in c.driver.variables]} for c in plane.animation_data.drivers]},'actions':{c:[{'name':x['action'],'owner':x['ownerName'],'slot':x.get('slotIdentifier')} for x in r['actions']] for c,r in record['clips'].items()}}
(OUT/(MODE+'-source-static.json')).write_text(json.dumps(static,indent=2)+'\n')
asset={'root':root,'collection':collection}
contact_names=['minimal_foot_L','minimal_foot_R','palm_L','palm_R','thumb_L','thumb_R','pelvis','head','smile']
# Meshes may change later. Here record actual evaluated surfaces, not only rig invariance.
def short(o):return o.name.split('customer_june__')[1].replace('.001','')
parts={short(o):o for o in objects if o.type=='MESH'}
contacts={n:next(o for o in objects if o.type=='MESH' and short(o)==n) for n in contact_names}
samples=[];summaries={}
for clip in record['clips']:
 for facing in ['S','E','N','W']:
  for frame in range(1,13):
   native.apply_clip(asset,record,clip,frame,facing,sc);dg=bpy.context.evaluated_depsgraph_get();bones={b.name:arm.matrix_world@b.matrix for b in arm.pose.bones};ri=root.matrix_world.inverted()
   meshes={};body=[];trees={}
   for o in objects:
    if o.type!='MESH':continue
    vs,polys=evaluated(o,dg);n=short(o);meshes[n]={'bounds':bound(vs),'visible':not o.hide_render,'matrix':[list(r) for r in o.evaluated_get(dg).matrix_world]}
    if o!=plane and not o.hide_render:body.extend(vs)
    if o in contacts.values():trees[n]=(vs,polys,BVHTree.FromPolygons(vs,polys,all_triangles=True))
   def nearest(name,p):
    v,n,i,d=trees[name][2].find_nearest(p);return {'query':list(p),'point':list(v),'normal':list(n),'distance':d,'triangle':i}
   palmpts={}
   for side in ['L','R']:
    # Source modeled palm centers (.267,-.025,.165), source definition evaluated_sockets.
    rest=arm.data.bones['hand_'+side].matrix_local;pt=bones['hand_'+side]@rest.inverted()@Vector((-.267 if side=='L' else .267,-.025,.165));palmpts[side]=pt
   pelvisbone=bones['pelvis'];seat=pelvisbone@arm.data.bones['pelvis'].matrix_local.inverted()@Vector((0,0,.070));mouth=bones['head']@arm.data.bones['head'].matrix_local.inverted()@Vector((0,-.255,.543))
   contact={}
   for side in ['L','R']:
    contact['palm_'+side]=nearest('palm_'+side,palmpts[side]);contact['thumb_'+side]=nearest('thumb_'+side,palmpts[side]);vs=trees['minimal_foot_'+side][0];z=min(v.z for v in vs);sole=[v for v in vs if v.z<=z+1e-5];contact['foot_'+side]={'supportZ':z,'soleCenter':list(sum(sole,Vector())/len(sole)),'supportVertices':[list(v) for v in sole],'footBoneHead':list(bones['foot_'+side].translation),'footBoneTail':list(arm.matrix_world@arm.pose.bones['foot_'+side].tail)}
   for side in ['L','R']:
    for typ,point in [('palm',palmpts[side]),('thumb',sum(trees['thumb_'+side][0],Vector())/len(trees['thumb_'+side][0]))]:
     v,n,idx,dist=trees[typ+'_'+side][2].ray_cast(point+Vector((0,0,2)),Vector((0,0,-1)),4)
     contact[typ+'_upwardSurface_'+side]={'point':list(v) if v else None,'normal':list(n) if n else None,'triangle':idx,'rayFrom':list(point+Vector((0,0,2)))}
   contact['seat']=nearest('pelvis',seat);contact['mouthHead']=nearest('head',mouth);contact['mouthSmile']=nearest('smile',mouth)
   qvs=[plane.evaluated_get(dg).matrix_world@v.co for v in plane.data.vertices];row={'clip':clip,'facing':facing,'frame':frame,'bodyBounds':bound(body),'rootMatrix':[list(r) for r in root.matrix_world],'bones':{n:[list(r) for r in m] for n,m in bones.items()},'meshBounds':meshes,'contacts':contact,'points':{'palms':{s:list(p) for s,p in palmpts.items()},'seat':list(seat),'mouth':list(mouth)},'food':{'visible':not plane.hide_render,'foodRootMatrix':[list(r) for r in foodroot.matrix_world],'planeMatrix':[list(r) for r in plane.evaluated_get(dg).matrix_world],'corners':[list(v) for v in qvs],'cornerPx':[px(v) for v in qvs],'width':(qvs[1]-qvs[0]).length,'bottomCenter':list((qvs[0]+qvs[1])/2),'bottomCenterPx':px((qvs[0]+qvs[1])/2),'foodRootPx':px(foodroot.matrix_world.translation),'palmMidpoint':list((palmpts['L']+palmpts['R'])/2),'palmMidpointPx':px((palmpts['L']+palmpts['R'])/2),'planeRotation':list(plane.rotation_euler),'planeLocation':list(plane.location)}}
   samples.append(row)
 for this in [s for s in samples if s['clip']==clip]:
  pass
 subset=[s for s in samples if s['clip']==clip];summaries[clip]={'count':len(subset),'min':[min(s['bodyBounds']['min'][i] for s in subset) for i in range(3)],'max':[max(s['bodyBounds']['max'][i] for s in subset) for i in range(3)],'visibleFoodCount':sum(s['food']['visible'] for s in subset),'foodWidthRange':[min(s['food']['width'] for s in subset),max(s['food']['width'] for s in subset)]}
 print('MEASURED',MODE,clip,summaries[clip],flush=True)
(OUT/(MODE+'-samples.json')).write_text(json.dumps(samples,separators=(',',':'))+'\n');(OUT/(MODE+'-summary.json')).write_text(json.dumps(summaries,indent=2)+'\n')
print('COMPLETE',len(samples))
