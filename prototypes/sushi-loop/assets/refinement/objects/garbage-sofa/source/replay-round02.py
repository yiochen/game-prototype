"""Reopen the delivered native model and repeat its saved assembled capture."""
import bpy,pathlib,json,hashlib
P=pathlib.Path(__file__).resolve().parent;OBJ=P.parent;OUT=OBJ/'candidates/round-02'
bpy.ops.wm.open_mainfile(filepath=str(P/'round-02.blend'))
sc=bpy.context.scene;assert sc.camera.name=='Registered sofa square top-front camera'
assert abs(bpy.data.objects['garbage-sofa__root'].rotation_euler.z)<1e-6
sc.render.filepath=str(OUT/'replay-idle-S.png');bpy.ops.render.render(write_still=True)
(OUT/'replay-native-record.json').write_text(json.dumps({'project':'source/round-02.blend','sourceSHA256':hashlib.sha256((P/'round-02.blend').read_bytes()).hexdigest(),'render':'candidates/round-02/replay-idle-S.png','direction':'S','rootRotationZ':float(bpy.data.objects['garbage-sofa__root'].rotation_euler.z),'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'samples':sc.cycles.samples,'scope':'Fresh process reopen and native render. No source changes or resave.'},indent=2)+'\n')
