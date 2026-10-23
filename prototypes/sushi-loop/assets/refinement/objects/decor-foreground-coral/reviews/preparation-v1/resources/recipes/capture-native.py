import bpy,sys,json,hashlib,math,time
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;R=P/'resources';sys.path.insert(0,str(R/'native'))
import native_actions as na
import capture_runtime as cr
D=json.loads((R/'inputs/source-assetRecord.json').read_text());rig=json.loads((R/'inputs/source-rig.json').read_text())
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));asset={**D,'root':root,'collection':col}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
sc.view_layers[0].update();cr.scene=lambda:sc
camera=cr.configure_camera(D['projection'],D['frame'],D['anchor'],D['scale'],D.get('camera_elevation_degrees'))
# Retain loaded source32 EEVEE samples/filter1.5; only lossless PNG compression adjusted.
sc.render.image_settings.compression=15;sc.render.use_file_extension=True;sc.render.use_persistent_data=True
records=[];cases=[('static',d,1) for d in ['N','E','S','W']]+[('idle','S',f) for f in range(1,14)]+[('idle',d,f) for d in ['N','E','W'] for f in [1,7]]
for clip,d,f in cases:
 na.apply_clip(asset,rig,clip,f,d,sc);dest=P/'evidence/native'/clip/d/f'{f:03d}.png';dest.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(dest);start=time.monotonic();bpy.ops.render.render(write_still=True)
 records.append({'clip':clip,'direction':d,'frame':f,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':[list(x) for x in root.matrix_world],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'nativeRoot':camera['calibration']['root'],'captureScale':D['scale'],'filterSize':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'path':str(dest.relative_to(P.parent.parent)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'renderSeconds':time.monotonic()-start})
ledger={'status':'untouched-source registered replay, no source save or art edits','source':'reviews/preparation-v1/resources/native/original.blend','sourceSHA256':hashlib.sha256((R/'native/original.blend').read_bytes()).hexdigest(),'binary':'/opt/homebrew/bin/blender','version':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'camera':camera,'nativeFilterSize':sc.render.filter_size,'samples':sc.eevee.taa_render_samples,'records':records,'limits':'bounded preparation views/representative native temporal captures; final candidate requires all52 published unique frames plus loop closure/hold proofs'}
(P/'evidence/native-capture-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('REGISTERED REPLAY COMPLETE',len(records))
