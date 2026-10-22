import bpy,json,pathlib,importlib.util,sys
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'round-01.blend'))
s=bpy.context.scene
print('RENDER',[(x.identifier,str(getattr(s.render,x.identifier))) for x in s.render.bl_rna.properties if any(t in x.identifier for t in ['dither','seed','filter'])])
print('EEVEE',[(x.identifier,str(getattr(s.eevee,x.identifier))) for x in s.eevee.bl_rna.properties if any(t in x.identifier for t in ['jitter','shadow','sample','ray'])])
sp=importlib.util.spec_from_file_location('replay',H/'round-01.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A)
c=bpy.data.collections['REFINED__sub-collector-inlet'];s.render.dither_intensity=0
for i in [1,13,1,13]:
 A.apply_clip(s,c,'active','N',i);p=H.parent/'candidates/round-01/draft'/f'probe-{i}-{s.frame_current_final}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
