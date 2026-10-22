"""Fresh raw repeated SAME-pose controls for native renderer repeatability."""
import bpy,json,pathlib,importlib.util,sys
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-01'
sp=importlib.util.spec_from_file_location('saved_replay',H/'replay-01.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);A=M.A
bpy.ops.wm.open_mainfile(filepath=str(H/'round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];records=[]
for di in 'NESW':
 for fr,label in [(1,'1a'),(1,'1b'),(13,'13a'),(13,'13b')]:
  r=M.measure(s,c,'active',di,fr);r['fullNativeResourceStateSHA256']=M.fingerprint(c)['sha256'];p=O/'repeatability'/f'{di}-{label}.png';p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);r.update(label=label,path=str(p.relative_to(E)),sha256=A.sha(p));records.append(r)
A.savej(O/'repeatability/native-controls.json',{'project':'source/round-01.blend','projectSHA256':A.sha(H/'round-01.blend'),'recipeSHA256':A.sha(H/'round-01.py'),'settings':A.settings(s,root),'records':records,'qualification':'Fresh same-pose controls, unchanged48sample EEVEE/filter.5/dither1. No raster repair or reduced-detail export. Frame13 remains actual source13.'})
