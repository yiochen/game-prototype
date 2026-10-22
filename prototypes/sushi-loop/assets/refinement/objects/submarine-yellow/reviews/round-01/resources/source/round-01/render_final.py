import sys,runpy,json
sys.dont_write_bytecode=True
from pathlib import Path
F=runpy.run_path(str(Path(__file__).parent/'native_common.py'));globals().update(F)
s,root,col=open_source();dirs=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(DIRS);records=[]
assert (s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage)==(640,768,100)
assert s.render.pixel_aspect_x==s.render.pixel_aspect_y==1 and s.render.filter_size==.5
for d in dirs:
 for clip in json.loads(root['nativeActions']):
  folder=O/'frames'/(clip+'-'+d);folder.mkdir(parents=True,exist_ok=True)
  for f in range(1,13):
   apply(clip,f,d);p=folder/('%03d.png'%(f-1));s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append(capture_record(clip,d,f,p));print('CAPTURE',clip,d,f,flush=True)
  # Closure frame 13 and a meaningful half-frame stay outside the runtime atlas.
  for f,kind in [(13,'closure-or-terminal'),(3.5,'meaningful-half')]:
   apply(clip,f,d);p=O/'diagnostics'/(clip+'-'+d+'-'+kind+'.png');p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append(capture_record(clip,d,f,p,kind))
 save(O/('captures-'+d+'.json'),{'sourceSHA256':sha(H/'project.blend'),'captures':[r for r in records if r['direction']==d],'captureLaw':'Direct saved native 640x768 EEVEE64, persisted filter.5, squarepixel camera65; no resampling/postprocessing. Runtime1..12; closure13 and half3.5 diagnostic only.'})
