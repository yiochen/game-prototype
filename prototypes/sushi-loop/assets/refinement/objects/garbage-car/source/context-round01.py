import bpy,json,sys,math,pathlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent;OUT=P/'candidates/round-01';sys.path.insert(0,str(P/'source/resources'));import native_actions as A
rig=json.loads((P/'source/resources/source-rig.json').read_text());root=bpy.data.objects['garbage-car__root'];sc=bpy.context.scene;coll=root.users_collection[0]
A.apply_clip({'root':root,'collection':coll},rig,'idle',1,'S',sc)
for o in coll.all_objects:
 if o.animation_data:o.animation_data_clear()
clones=[]
for i in (1,2):
 c=bpy.data.collections.new('Independent car assembly '+str(i));sc.collection.children.link(c);mapping={}
 for o in coll.all_objects:
  n=o.copy()
  if o.type=='MESH':n.data=o.data.copy()
  n.animation_data_clear();c.objects.link(n);mapping[o]=n
 for o,n in mapping.items():
  if o.parent:n.parent=mapping[o.parent]
 clones.append(mapping[root])
placements=[(root,(1.5,-1,0)),(clones[0],(5.5,-1,0)),(clones[1],(1.5,-4,0))]
for r,loc in placements:r.location=loc
cam=sc.camera;sc.render.resolution_x=2304;sc.render.resolution_y=2048;cam.data.ortho_scale=9;cam.data.shift_x=(2304/2-256)/2304;cam.data.shift_y=0
bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*2304,(1-p.y)*2048]
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(256-base[1])/dy;bpy.context.view_layer.update()
zero=px((0,0,0));audit={'project':'source/context-round01.blend','source':'source/round-01.blend','frame':[2304,2048],'nativeCellPitch':256,'originPixels':zero,'calibration':{'X':[a-b for a,b in zip(px((1,0,0)),zero)],'depth':[a-b for a,b in zip(px((0,-1,0)),zero)],'height':[a-b for a,b in zip(px((0,0,1)),zero)]},'placements':[{'root':r.name,'gridTopLeft':xy,'facing':'S','actualMatrix':[list(v) for v in r.matrix_world],'projectedRoot':px(r.location)} for (r,loc),xy in zip(placements,[[0,0],[4,0],[0,3]])],'independentMeshes':True,'cameraMatrix':[list(row) for row in cam.matrix_world],'lightingUnchanged':True,'floorIncluded':False}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/context-round01.blend'),compress=True)
sc.render.filepath=str(OUT/'previews/native-repeated.png');(OUT/'previews').mkdir(exist_ok=True);bpy.ops.render.render(write_still=True)
(OUT/'native-context-audit.json').write_text(json.dumps(audit,indent=2))
