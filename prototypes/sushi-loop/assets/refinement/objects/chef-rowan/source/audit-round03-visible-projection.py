"""Small supplement: original vs final actual visible evaluated quads, not hidden caches."""
import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def measure(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];col.hide_viewport=False;col.hide_render=False
 def vis(lc):
  lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
  for c in lc.children:vis(c)
 vis(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update();plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];asset=dict(root=root,collection=col);records=[]
 for clip in rig['clips']:
  for direction in ['N','E','S','W']:
   for frame in range(1,13):
    native.apply_clip(asset,rig,clip,frame,direction,scene);dg=bpy.context.evaluated_depsgraph_get();m=plane.evaluated_get(dg).matrix_world;visible=not plane.hide_render;points=[]
    if visible:
     for point in [v.co for v in plane.data.vertices]+[Vector((0,0,0))]:
      q=world_to_camera_view(scene,scene.camera,m@point);points.append([q.x*384,(1-q.y)*640])
    records.append(dict(clip=clip,direction=direction,index=frame-1,visible=visible,pixels=points))
 return records
base=OBJ/'inputs/baseline-round01.blend';candidate=HERE/'round-03.blend';a=measure(base);b=measure(candidate);groups=[]
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  pairs=[(x,y) for x,y in zip(a,b) if y['clip']==clip and y['direction']==direction];errs=[max(abs(v-w) for p,q in zip(x['pixels'],y['pixels']) for v,w in zip(p,q)) for x,y in pairs if y['visible']];assert all(x['visible']==y['visible'] for x,y in pairs)
  groups.append(dict(clip=clip,direction=direction,evaluations=len(pairs),actualVisibleComparisons=len(errs),maximumActualNativePixelError=max(errs,default=None),allUnderPoint001NativePixel=all(e<.001 for e in errs)))
report=dict(activeBrief='brief-v4-food-occlusion.json',baselineSHA256=sha(base),sourceSHA256=sha(candidate),source='source/round-03.blend',serializer='source/audit-round03-visible-projection.py',serializerSHA256=sha(Path(__file__)),nativePoseEvaluations=192,actualVisibleQuadComparisons=96,hiddenPolicy='Hidden evaluated descendants intentionally excluded here; all192 composed native points and exact law are in occlusion-native-audit.json.',groups=groups,maximumActualVisibleNativePixelError=max(g['maximumActualNativePixelError'] or 0 for g in groups),allChecksPassed=all(g['allUnderPoint001NativePixel'] for g in groups))
(OUT/'visible-projection-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['allChecksPassed']
