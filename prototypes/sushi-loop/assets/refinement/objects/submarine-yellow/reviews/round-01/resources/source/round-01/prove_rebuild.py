import sys,runpy
sys.dont_write_bytecode=True
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).parent/'native_common.py')))
F=runpy.run_path(str(H/'component_identity.py'));rebuilt=Path(sys.argv[sys.argv.index('--')+1]);proof={};identities={}
def actions():
 ret=[]
 for a in sorted(bpy.data.actions,key=lambda a:a.name):
  ret.append({'name':a.name,'slots':[x.identifier for x in a.slots],'channels':[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[[val(k.co),k.interpolation,val(k.handle_left),val(k.handle_right)] for k in f.keyframe_points]} for l in a.layers for st in l.strips for bag in st.channelbags for f in bag.fcurves]})
 return ret
for label,p in [('selected',H/'project.blend'),('portable-rebuild',rebuilt)]:
 bpy.ops.wm.open_mainfile(filepath=str(p));apply('upgraded-dock-ready');c=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];s=bpy.context.scene
 identities[label]={'allPersistentResourcesSHA256':F['hd'](F['persistent'](c)),'allActionDatablocksSHA256':hd(actions()),'canonicalVisibilityMapSHA256':hd(json.loads(c['canonicalVisibilityActions'])),'frozenMainActionMapSHA256':hd(json.loads(bpy.data.objects['submarine-yellow__root']['nativeActions'])),'sceneCamera':val(s.camera.matrix_world),'cameraData':[s.camera.data.ortho_scale,s.camera.data.shift_x,s.camera.data.shift_y,s.render.pixel_aspect_x,s.render.pixel_aspect_y,s.render.resolution_x,s.render.resolution_y,s.render.filter_size],'imageAndLinkedResources':[[(i.name,i.filepath,bool(i.packed_file)) for i in bpy.data.images],[l.filepath for l in bpy.data.libraries]]}
proof={'selectedSourceSHA256':sha(H/'project.blend'),'rebuiltSourceSHA256':sha(rebuilt),'resourceSnapshots':identities,'allNativeResourceActionCameraIdentityExact':identities['selected']==identities['portable-rebuild'],'byteIdentityRequired':False,'note':'Exact native persistent mesh arrays/normals/UV/material graphs/transforms/modifiers and all action datablocks/camera/maps verified. Independently saved .blend container bytes may differ. Renderer noise calibrated separately, selected native captures remain authoritative.'};assert proof['allNativeResourceActionCameraIdentityExact'];save(O/'portable-rebuild-identity.json',proof)
for d in DIRS:
 apply('upgraded-dock-ready',1,d);p=O/'rebuild-replay'/('upgraded-dock-ready-'+d+'.png');p.parent.mkdir(exist_ok=True);s.render.filepath=str(p);bpy.ops.render.render(write_still=True)
print('PORTABLE_IDENTITY',proof)
