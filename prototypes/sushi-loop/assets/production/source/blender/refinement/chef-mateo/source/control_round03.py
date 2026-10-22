"""Fresh identical-input control, unsaved. Source-old A versus candidate-restored-old B."""
import bpy,sys,json,hashlib,importlib.util,time
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('mateo_r03_common',HERE/'round03_common.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
B=json.loads((HERE/'round03-baseline.json').read_text());sc,asset,arm,food=C.owned();candidate=Path(bpy.data.filepath).name=='round03.blend';label='candidate-restored-old' if candidate else 'approved-source-old';OUT=C.OUT/'controls'/label;OUT.mkdir(parents=True,exist_ok=True)
C.N.apply_clip(asset,C.rig,'idle',1,'S',sc)
assert C.digest(C.invariants(sc,asset,arm,food))==C.digest(B['frozenInvariants'])
node=next(n for n in food.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
if candidate:
 for v,co in zip(food.data.vertices,B['sourceFoodRestVertices']):v.co=co
 for uv,co in zip(food.data.uv_layers.active.data,B['sourceFoodUV']):uv.uv=co
 food.data.update();old=bpy.data.images.load(str(C.RES/'historical-salmon.png'),check_existing=False);old.alpha_mode=B['sourceFoodImage']['alphaMode'];old.colorspace_settings.name=B['sourceFoodImage']['colorSpace'];old.pack();node.image=old
assert hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()==B['sourceFoodImage']['sha256']
device=C.module_device();selected={('idle','S',0),('work','S',3)}|{(c,d,i) for c,inds in [('hold',[0,6]),('load',[0,11])] for d in ['N','E','S','W'] for i in inds};rows=[];started=time.time()
for row in B['samples']:
 key=(row['clip'],row['direction'],row['index']);a=C.evaluate(sc,asset,arm,food,*key)
 if key not in selected:continue
 assert a['bodyEvaluatedSHA256']==row['bodyEvaluatedSHA256'] and a['foodHiddenFlags']==row['foodHiddenFlags']
 path=OUT/(key[0]+'-'+key[1]+'-'+str(key[2]).zfill(3)+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 rows.append({'clip':key[0],'direction':key[1],'index':key[2],'path':str(path.relative_to(C.OBJ)),'foodQuadProjected':a['cornersProjected'],'sourceBodyParity':True,'sourceFoodVisibilityParity':True})
report={'label':label,'inputProjectSHA256':C.sha(Path(bpy.data.filepath)),'oldPackedSHA256':hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest(),'renderSettingsHash':B['frozenInvariants']['captureLightingRenderSettings'],'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'renderSamples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'device':device,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'nativeDataSettingsExactBeforeControlRestore':True,'candidateRestoredOldImageQuadUVOnly':candidate,'projectSaved':False,'samples':rows,'elapsedSeconds':time.time()-started}
C.write(OUT/'index.json',report);print('MATEO_IDENTICAL_INPUT_CONTROL',label,len(rows),flush=True)
