"""Reopen fixed candidate; audit all192 source-equivalent samples, then native render."""
import bpy,sys,importlib.util,json,math,time,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;sp=importlib.util.spec_from_file_location('mateo_r03_common',HERE/'round03_common.py');C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)
B=json.loads((HERE/'round03-baseline.json').read_text());sc,asset,arm,food=C.owned();C.N.apply_clip(asset,C.rig,'idle',1,'S',sc)
actual=C.invariants(sc,asset,arm,food)
if C.digest(actual)!=C.digest(B['frozenInvariants']):
 C.write(C.OUT/'invariant-diagnostic.json',{'source':B['frozenInvariants'],'candidate':actual})
 raise AssertionError(['Reopened invariant mismatch',[(k,actual[k]==B['frozenInvariants'][k]) for k in actual]])
node=next(n for n in food.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');im=node.image
assert hashlib.sha256(bytes(im.packed_file.data)).hexdigest()==C.brief['foodDependency']['sha256']
assert list(im.size)==[731,505] and all(i.packed_file for i in bpy.data.images if i.type=='IMAGE')
for p in food.data.polygons:
 for li in p.loop_indices:assert list(food.data.uv_layers.active.data[li].uv)==[[0,0],[1,0],[1,1],[0,1]][food.data.loops[li].vertex_index]
quad=[Vector(v) for v in B['globalMappedRestQuad']];old=[Vector(v) for v in B['sourceFoodRestVertices']]
oldSupport=old[0]+(old[1]-old[0])*(627/1242)+(old[3]-old[0])*((1198-1051)/(1198-85))
newSupport=quad[0]+(quad[1]-quad[0])*.5+(quad[3]-quad[0])*(1/505)
oldBottom=(old[0]+old[1])*.5;right=Vector((1,0,0));up=Vector((0,math.sin(math.radians(35)),math.cos(math.radians(35))));toward=Vector((0,-math.cos(math.radians(35)),math.sin(math.radians(35))))
errors=[];rows=[];maxima={k:0. for k in ['mappedCornerWorld','mappedCornerNativePx','semanticSupportWorld','semanticSupportNativePx','semanticOccupiedWidthWorld','fullQuadAspect','visibleDepthBias','visibleOrthogonalBias','propToPalm','matrixDelta','footDelta','bodyBoundsDelta','knifeToPalm']};bodyHashes=True;bones=True;topologies=set();starts=time.time();device=C.module_device();audit='--audit-only' in sys.argv
keys=['foodPlaneMatrix','foodPropMatrix','knifeMatrix'];sameKeys=['bodyEvaluatedSHA256','bonesSHA256','foodHiddenFlags','topologySHA256']
def dmat(a,b):return max(abs(x-y) for ra,rb in zip(a,b) for x,y in zip(ra,rb))
def dp(a,b):return (Vector(a)-Vector(b)).length
for source in B['samples']:
 clip,d,i=source['clip'],source['direction'],source['index'];a=C.evaluate(sc,asset,arm,food,clip,d,i);M=Matrix(source['foodPlaneMatrix']);Mp=Matrix(source['foodPropMatrix']);corners=[Vector(x) for x in a['cornersWorld']];expected=[M@q for q in quad]
 ec=max((x-y).length for x,y in zip(corners,expected));ep=max(dp(C.pixel(sc,x),C.pixel(sc,y)) for x,y in zip(corners,expected));ss=M@oldSupport;cs=Matrix(a['foodPlaneMatrix'])@newSupport;sw=(cs-ss).length;spx=dp(C.pixel(sc,cs),C.pixel(sc,ss));width=(corners[1]-corners[0]).length*729/731;aspect=(corners[1]-corners[0]).length/(corners[3]-corners[0]).length
 matrix=max(dmat(source[k],a[k]) for k in keys);bd=max(abs(source['bodyBounds'][k][j]-a['bodyBounds'][k][j]) for k in ['min','max'] for j in range(3));fd=max(abs(source['feetMinZ'][k]-a['feetMinZ'][k]) for k in ['L','R']);pd=max(dp(source['palms'][k],a['palms'][k]) for k in ['L','R'])
 for k in sameKeys:
  if source[k]!=a[k]:errors.append([clip,d,i,k])
 bodyHashes&=source['bodyEvaluatedSHA256']==a['bodyEvaluatedSHA256'];bones&=source['bonesSHA256']==a['bonesSHA256'];topologies.add(a['topologySHA256'])
 if matrix>1e-6 or bd>1e-6 or fd>1e-6 or pd>1e-6:errors.append([clip,d,i,'actual source parity',matrix,bd,fd,pd])
 if ec>1e-5 or ep>.01 or sw>1e-5 or spx>.01:errors.append([clip,d,i,'fixed semantic mapping',ec,ep,sw,spx])
 visible=a['foodVisible'];depth=None;orth=None;anchor=None
 if visible:
  bias=M@oldBottom-Mp.translation;depth=bias.dot(toward);orth=(bias-depth*toward).length;anchor=(Mp.translation-(Vector(a['palms']['L'])+Vector(a['palms']['R']))*.5-Vector((0,0,.0225))).length
  vals={'semanticOccupiedWidthWorld':abs(width-C.mapping['occupiedWorldWidth']),'fullQuadAspect':abs(aspect-731/505),'visibleDepthBias':abs(depth-.6),'visibleOrthogonalBias':orth,'propToPalm':anchor}
  for k,v in vals.items():maxima[k]=max(maxima[k],v)
  if max(vals.values())>1e-5:errors.append([clip,d,i,'visible source law',vals])
 for k,v in {'mappedCornerWorld':ec,'mappedCornerNativePx':ep,'semanticSupportWorld':sw,'semanticSupportNativePx':spx,'matrixDelta':matrix,'footDelta':fd,'bodyBoundsDelta':bd}.items():maxima[k]=max(maxima[k],v)
 knifeDist=(Matrix(a['knifeMatrix']).translation-Vector(a['palms']['R'])).length if clip=='work' else None
 if knifeDist is not None:maxima['knifeToPalm']=max(maxima['knifeToPalm'],knifeDist)
 folder=C.OUT/'raw-frames'/(clip+'-'+d);folder.mkdir(parents=True,exist_ok=True);path=folder/(str(i).zfill(3)+'.png')
 if not audit:sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 rows.append({'clip':clip,'direction':d,'index':i,'path':str(path.relative_to(C.OBJ)),'rootRotationDegrees':math.degrees(a['rootRotationZ']),'visible':visible,'sourceHiddenFlags':a['foodHiddenFlags'],'mappedCornerMaxWorld':ec,'mappedCornerMaxNativePx':ep,'sourceSemanticSupportWorld':C.plain(ss),'candidateSemanticSupportWorld':C.plain(cs),'semanticSupportMaxNativePx':spx,'occupiedWidthWorld':width,'fullQuadAspect':aspect,'sourceMatrixMaxDelta':matrix,'visibleSourceDepthToward':depth,'visibleSourceOrthogonalBias':orth,'propPalmAnchorResidual':anchor,'knifeToPalmDistance':knifeDist,'bodyBounds':a['bodyBounds'],'bodySourceParity':source['bodyEvaluatedSHA256']==a['bodyEvaluatedSHA256'],'foodQuadProjected':a['cornersProjected']})
 if len(rows)%12==0:C.write(C.OUT/'capture-progress.json',{'done':len(rows),'total':192,'clip':clip,'direction':d,'auditOnly':audit,'elapsedSeconds':time.time()-starts});print('MATEO_ROUND03',len(rows),clip,d,flush=True)
assert len(rows)==192 and len(topologies)==1
if errors:C.write(C.OUT/'audit-errors.json',errors)
assert not errors,errors[:10]
report={'asset':'chef-mateo','round':'round03','pipeline':'native-3d with exact canonical2D food insert','brief':str(C.BRIEF.relative_to(C.OBJ)),'briefSHA256':C.sha(C.BRIEF),'approvedSourceSHA256':B['approvedProjectSHA256'],'candidateProjectSHA256':C.sha(Path(bpy.data.filepath)),'blenderVersion':bpy.app.version_string,'device':device,'scene':sc.name,'capture':C.brief['capture'],'nativeRecords':{k:str((C.OUT/v).relative_to(C.OBJ)) for k,v in [('camera','camera.json'),('assetRecord','assetRecord.json'),('rig','rig.json')]},'frozenNativeDefinitionsExact':True,'all192BodyEvaluationsExact':bodyHashes,'all192BoneEvaluationsExact':bones,'all192SourceMatricesVisibilityExact':maxima['matrixDelta']==0,'stableEvaluatedTopology':True,'foodMapping':{'sourceOldPackedSHA256':B['sourceFoodImage']['sha256'],'canonicalPackedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest(),'canonicalFullUV':True,'canonicalImageSize':list(im.size),'globalRestQuad':B['globalMappedRestQuad'],'fullQuadAspect':731/505,'semanticAlphaThreshold':128,'sourceSupportPoint':C.mapping['sourceSupportPoint'],'canonicalSupportPoint':C.mapping['canonicalSupportPoint'],'occupiedVisibleWorldWidth':C.mapping['occupiedWorldWidth'],'visibleSamples':sum(x['visible'] for x in rows),'hiddenSamples':sum(not x['visible'] for x in rows),'hiddenStatePolicy':'Unchanged actual source matrices/actions/visibility; the same fixed mapped rest quad, with source hidden scale, not the visible width law.','depthMeasurement':'Original source old-bottom reconstructed through unchanged plane matrix removes only authorized screen offset; actual visible0.6world bias/yaw preserved.','oldCustomStrings':'Unchanged historical provenance only; active packed image and native UV/quad are authoritative.'},'maximumResiduals':maxima,'contactsAndClearance':'All actual nonfood evaluated mesh positions/normals/world matrices, original rest/action/weights, feet/palms/knife and full bodybounds equal approved source in all192 samples.','RGBPolicy':'Native data/settings equality is not a claim of bodyRGB equality under changed emissive food. Calibrated identical-input control and actual canonical radiance deltas are reported separately.','nativeChecksPass':True,'errors':errors,'renders':rows,'elapsedSeconds':time.time()-starts,'auditOnly':audit}
C.write(C.OUT/('audit-validation.json' if audit else 'validation.json'),report);print('MATEO_ROUND03_COMPLETE',json.dumps(maxima),flush=True)
