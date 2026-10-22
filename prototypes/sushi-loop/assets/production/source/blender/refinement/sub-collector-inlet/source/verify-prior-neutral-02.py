import bpy,json,pathlib,sys,importlib.util
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02'
sp=importlib.util.spec_from_file_location('round02_saved_replay',H/'replay-02.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);A=M.A
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;c=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root'];A.apply_clip(s,c,'idle','S',1)
 channels={o.name:{'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'basis':[list(r) for r in o.matrix_basis],'parent':o.parent.name if o.parent else None} for o in c.all_objects}
 return M.fingerprint(c),channels,A.settings(s,root),{'eeveeSamples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'ditherIntensity':s.render.dither_intensity,'engine':s.render.engine,'transparent':s.render.film_transparent}
old,oc,os,orender=read(H/'round-01.blend');new,nc,ns,nrender=read(H/'round-02.blend')
report={'priorSource':'source/round-01.blend','priorSHA256':A.sha(H/'round-01.blend'),'newSource':'source/round-02.blend','newSHA256':A.sha(H/'round-02.blend'),'idleNeutralResourceFingerprintsExact':old==new,'idleStoredTransformChannelsExact':oc==nc,'cameraLightingFilterSamplesAndSettingsUnchanged':os==ns,'nativeRenderRecipeRound01':orender,'nativeRenderRecipeRound02':nrender,'nativeRenderRecipeExact':orender==nrender,'priorFingerprint':old['sha256'],'newFingerprint':new['sha256'],'changeScope':'Only active guard rotationX keys changed. Idle native geometry, normals, UVs, material nodes, root, mounts, channels, camera and light/capture settings are exactly retained.','approval':False}
assert orender==nrender and nrender['eeveeSamples']==48 and nrender['filterSize']==.5 and nrender['ditherIntensity']==1
assert report['idleNeutralResourceFingerprintsExact'] and report['idleStoredTransformChannelsExact'] and report['cameraLightingFilterSamplesAndSettingsUnchanged']
A.savej(O/'neutral-prior-round-identity.json',report);print(json.dumps(report,indent=2))
