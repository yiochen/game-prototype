import bpy,sys,math,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;OUT=RES.parent/'evidence/independent-native-L';OUT.mkdir(parents=True,exist_ok=True)
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};records=[]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def layers(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layers(c)
def enable(col):
 col.hide_viewport=False;col.hide_render=False
 for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
 layers(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update()
def configure(sc,scale,frame=(192,352),anchor=(96,248),filt=.01):
 cam=sc.camera;sc.render.resolution_x=round(frame[0]*scale);sc.render.resolution_y=round(frame[1]*scale);sc.render.resolution_percentage=100
 sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.filter_size=filt
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 r=px((0,0,0));return {'frame':list(frame),'root':list(anchor),'scale':scale,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'ortho':cam.data.ortho_scale,'cameraWorld':[list(row) for row in cam.matrix_world],'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}}
def render(sc,name,meta):
 p=OUT/(name+'.png');p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'path':str(p.relative_to(OUT)),**meta,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def append(filepath,colname):
 with bpy.data.libraries.load(str(filepath),link=False) as (src,dst):dst.collections=[colname]
 c=dst.collections[0];bpy.context.scene.collection.children.link(c);enable(c);return c
# Exact approved rig, unchanged original derivative, actual proper-handed L native references.
bpy.ops.wm.open_mainfile(filepath=str(RES/'canonical-middle02.blend'));sc=bpy.context.scene
middle=bpy.data.objects['wreck-middle__root'];middlecol=bpy.data.collections['Wreck middle authored candidate'];enable(middlecol)
col=append(RES/'candidate.blend','S33_PROP_wreck-corner.001');root=next(o for o in col.objects if o.get('asset_id')=='wreck-corner');root.location=(0,0,0)
edgepath=RES/'canonical-edge02.blend'
with bpy.data.libraries.load(str(edgepath),link=False) as (src,dst):
 edgecols=[c for c in src.collections if 'Wreck edge' in c];assert len(edgecols)==1,edgecols;dst.collections=edgecols
edgecol=dst.collections[0];sc.collection.children.link(edgecol);enable(edgecol);edge=next(o for o in edgecol.objects if o.get('asset_id')=='wreck-edge')
clones={}
for o in list(middlecol.objects):cp=o.copy();middlecol.objects.link(cp);clones[o]=cp
for o,cp in clones.items():cp.parent=clones.get(o.parent);cp.matrix_parent_inverse=o.matrix_parent_inverse.copy()
midN=clones[middle]
for d,a in ANGLES.items():
 root.rotation_euler.z=a;middlecol.hide_render=True;edgecol.hide_render=True;sc.frame_set(1);bpy.context.view_layer.update();camera=configure(sc,2)
 render(sc,'candidate-single/'+d,{'kind':'saved candidate corner in exact approved rig diagnostic; not candidate','direction':d,'camera':camera,'rootMatrix':[list(r) for r in root.matrix_world]})
 middlecol.hide_render=False
 west=Vector((-math.cos(a),-math.sin(a),0));north=Vector((-math.sin(a),math.cos(a),0))
 middle.location=west;middle.rotation_euler.z=a;midN.location=north;midN.rotation_euler.z=a+math.pi/2
 pxroots=[(0,0),(west.x*128,-west.y*128),(north.x*128,-north.y*128)]
 anchor=(round(96-min(v[0] for v in pxroots)),round(248-min(v[1] for v in pxroots)));frame=(320,480)
 for kind in ['middle-L','mixed-edge-L']:
  for o in [middle]+list(middle.children_recursive):o.hide_render=kind=='mixed-edge-L'
  edgecol.hide_render=kind!='mixed-edge-L';edge.location=west;edge.rotation_euler.z=a
  bpy.context.view_layer.update();camera=configure(sc,2,frame,anchor)
  render(sc,kind+'/'+d,{'kind':'saved candidate corner at0 + approved '+('middle02 W and middle02 N' if kind=='middle-L' else 'edge02 W and middle02 N')+'; proper-handed L baseline only','direction':d,'camera':camera,'moduleRootMatrices':{'corner':[list(r) for r in root.matrix_world],'Wneighbor':[list(r) for r in (middle if kind=='middle-L' else edge).matrix_world],'Nneighbor':[list(r) for r in midN.matrix_world]},'assembly':{'roots':[[0,0,0],list(west),list(north)],'rotationsDegrees':[math.degrees(a),math.degrees(a),math.degrees(a)+90],'Wcontact':'corner W to neighbor E','Ncontact':'corner N to +90deg neighbor W','capsRetained':True,'pitch':1}})
 for o in [middle]+list(middle.children_recursive):o.hide_render=False
(OUT/'capture-records.json').write_text(json.dumps({'blender':bpy.app.version_string,'scope':'Original judge independent saved-source native control recapture; no verdict inferred','records':records},indent=2)+'\n')
print('OWN_NATIVE_L_COMPLETE',len(records))
