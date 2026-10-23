import sys,runpy
sys.dont_write_bytecode=True
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).parent/'native_common.py')))
s,root,col=open_source();records=[]
for d in DIRS:
 for clip in ['idle','upgraded-dock-ready','upgraded-dock-charging']:
  apply(clip,1,d);p=O/'replay'/(clip+'-'+d+'.png');p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append(capture_record(clip,d,1,p,'clean-source-replay'))
 for repeat in range(2):
  apply('upgraded-dock-ready',1,d);p=O/'replay'/('samepose-'+d+'-'+str(repeat)+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append(capture_record('upgraded-dock-ready',d,1,p,'same-run-samepose-control'))
companions={}
for key,file,cn,loc in [('floor','dock-floor-round-04.blend','WarmSoft_dock-floor',(0,0,0)),('entry','dock-entry-round-06.blend','S33_PROP_dock-entry',(0,-1.5,0)),('hut','workshop-hut-round-01.blend','WarmSoft_workshop-hut',(.78,.35,.23))]:
 with bpy.data.libraries.load(str(R/file),link=False) as(src,dst):dst.collections=[cn]
 c=dst.collections[0];s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;rr=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);rr.location=loc;rr.rotation_euler=(0,0,0);companions[key]=(c,rr,loc)
s.render.resolution_x=1280;s.render.resolution_y=1536;s.camera.data.ortho_scale=6;s.camera.data.shift_y=.10
for d in DIRS:
 for clip in ['dock-ready','upgraded-dock-ready','dock-charging','upgraded-dock-charging']:
  apply(clip,4,d,(-.70,-.42,.23));p=O/'native-context'/(clip+'-'+d+'.png');p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True);rec=capture_record(clip,d,4,p,'fixed-root-actual-native-dock');rec.update(companionRoots={k:val(rr.matrix_world) for k,(c,rr,loc) in companions.items()},disclosure='Actual accepted mesh resources at fixed positions, main65degree physical camera. Larger canvas retains256nativepixels/Xworld. Standalone companion55degree sprites use distinct projection; no crossprojection pixelidentity, no cover approval.');records.append(rec)
save(O/'context-replay-captures.json',{'sourceSHA256':sha(H/'project.blend'),'acceptedDockManifestSHA256':sha(R/'accepted-dock-manifest.json'),'captures':records})
