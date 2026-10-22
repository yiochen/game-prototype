import bpy,pathlib,importlib.util,sys
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(H/'round-01.blend'));s=bpy.context.scene
print('LIGHT',[(x.identifier,str(getattr(next(o.data for o in s.objects if o.type=='LIGHT'),x.identifier))) for x in bpy.data.lights[0].bl_rna.properties if any(t in x.identifier for t in ['jitter','shadow'])])
sp=importlib.util.spec_from_file_location('r',H/'round-01.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A);c=bpy.data.collections['REFINED__sub-collector-inlet']
s.render.dither_intensity=0
for label,samples,shadows in [('one',1,True),('64',64,True),('noshadows',48,False)]:
 s.eevee.taa_render_samples=samples;s.eevee.use_shadows=shadows
 for i in [1,13]:
  A.apply_clip(s,c,'active','N',i);s.render.filepath=str(H.parent/'candidates/round-01/draft'/f'{label}-{i}.png');bpy.ops.render.render(write_still=True)
