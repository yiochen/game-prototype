import bpy,pathlib,math
P=pathlib.Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-02.blend'));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.sampling_pattern='TABULATED_SOBOL';s.cycles.scrambling_distance=0;OUT=P/'candidates/round-04';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-04.blend'))
exec((P/'source/test_join_round02.py').read_text().split("s.render.resolution_x=896")[0].split("P=pathlib.Path(__file__).resolve().parents[1];")[0] if False else 'pass')
c=bpy.data.collections['S33_FB_belt-straight-n.001'];root=next(o for o in c.objects if '__root.' in o.name)
root.rotation_euler.z=math.pi;s.render.filepath=str(OUT/'hero-N.png');bpy.ops.render.render(write_still=True)
original=list(c.objects);clones=[]
for i in [-1,1]:
 mapping={}
 for o in original:q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 clones.append((i,mapping[root]))
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
for i,q in clones:q.rotation_euler.z=math.pi;q.location=(0,i,0)
bpy.context.view_layer.update();s.render.filepath=str(OUT/'native-N-00.png');bpy.ops.render.render(write_still=True)
