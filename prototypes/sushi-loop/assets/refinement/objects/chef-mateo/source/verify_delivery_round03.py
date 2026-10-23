"""Read-only delivery verification plus exact previous packet-byte preservation."""
import sys,json,hashlib,subprocess
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent;P=O/'candidates/round03';d=json.loads((O/'delivery-round03.json').read_text());v=json.loads((P/'validation.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(O/d['referenceBrief'])=='e699452c13c421593cf1d1de45a8449222376b7cb6d71ad310b7337d4427c7ac'
assert sha(O/d['project'])==v['candidateProjectSHA256']=='b0e7450c0e204426a93bd798b6ba83a9d2a3d6c368987fe887370a3e7f7613f9'
assert sha(H/'round02.blend')=='3822fb7b734408a0e176d5546cfda3213754a620382c58a691717dee56c8df3e'
assert sha(H/'round03-resources/canonical-salmon.png')=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
prior=[]
for r in ['round01','round02']:
 packet=O/'candidates'/r/'packet.json';j=json.loads(packet.read_text());m=[]
 for name,x in j['files'].items():
  f=(packet.parent/x['path']).resolve()
  if not f.is_file() or sha(f)!=x['sha256']:m.append(name)
 assert not m,(r,m);prior.append({'round':r,'packetSHA256':sha(packet),'boundFileRecords':len(j['files']),'allExact':True})
assert len(d['rawFrames'])==192 and len(d['atlases'])==16
raw={(r['clip'],r['direction'],r['index']):r for r in d['rawFrames']};cellcount=0
for a in d['atlases']:
 f=O/a['path'];im=Image.open(f).convert('RGBA');assert im.size==tuple(a['size'])==(2304,1280) and a['columns']==6 and a['rows']==2 and sha(f)==a['sha256']
 for i,rect in enumerate(a['rects']):
  r=raw[(a['clip'],a['direction'],i)];rf=O/r['path'];ri=Image.open(rf).convert('RGBA');x,y,w,h=rect;assert ri.size==(384,640) and sha(rf)==r['sha256'];assert im.crop((x,y,x+w,y+h)).tobytes()==ri.tobytes();cellcount+=1
assert cellcount==192
qa=json.loads((P/'pixel-playback-validation.json').read_text());assert qa['cleanOuter2px'] and qa['exactAtlasCells']==192
for key,b in qa['playbacks'].items():
 f=O/b['path'];s=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(f)]))['streams'][0];assert s['r_frame_rate']=='12/1' and s['nb_frames']=='12' and float(s['duration'])==1 and s['width']==384 and s['height']==640;assert b['loop']==(b['clip']!='load')
for p in [d['project'],d['recipe'],d['recipeManifest'],d['captureRecipe'],d['packagingRecipe'],d['validation'],*d['heroes'].values(),*d['previews'].values(),*d['nativeRecords'].values(),*d['recipeResources'].values(),*d['resources']]:assert (O/p).is_file(),p
camera=json.loads((O/d['nativeRecords']['camera']).read_text());asset=json.loads((O/d['nativeRecords']['assetRecord']).read_text());rig=json.loads((O/d['nativeRecords']['rig']).read_text());assert camera['captureScale']==2 and asset['scale']==2 and asset['frame']==[192,320] and asset['anchor']==[96,248];assert set(rig['clips'])=={'idle','work','hold','load'}
a=json.loads((P/'frozen-extra-approved.json').read_text());b=json.loads((P/'frozen-extra-candidate.json').read_text());assert a['hashWithoutImageBinding']==b['hashWithoutImageBinding'];assert b['extra']['linkedLibraries']==[] and len(b['extra']['images'])==1 and b['extra']['images'][0]['packed']
assert v['all192BodyEvaluationsExact'] and v['all192BoneEvaluationsExact'] and v['all192SourceMatricesVisibilityExact'] and v['frozenNativeDefinitionsExact'] and v['stableEvaluatedTopology'] and v['nativeChecksPass']
r=json.loads((P/'calibrated-radiance-validation.json').read_text());assert len(r['rows'])==18 and r['sameInputAlphaMaximumDelta8bit']==0
context=json.loads((P/'serving-context-validation.json').read_text());assert len(context['renders'])==3 and context['noProjectSaved']
report={'asset':'chef-mateo','round':'round03','delivery':'delivery-round03.json','candidateProjectSHA256':sha(O/d['project']),'priorBoundFiles':prior,'rawFrames':192,'atlasCount':16,'atlasSize':[2304,1280],'exactAtlasCells':cellcount,'nativeFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'captureScale':2,'actualClips':16,'fps':12,'framesPerClip':12,'loopPolicy':'idle/work/hold true; load false','cleanOuter2px':True,'allNativeFreezeAnd192SampleChecksPass':True,'extraCameraDOFAndWorldLightNodeRayFlagsExact':True,'portablePackedDependencyClosure':True,'resourcesCanonicalSHA256':sha(H/'round03-resources/canonical-salmon.png'),'servingContextStills':3,'sameInputCalibration':r['sameInputCalibration'],'canonicalActualRGBDelta':r['canonicalActualRGBDelta'],'maximumMappingResiduals':v['maximumResiduals'],'editorApproval':False,'reviewStatus':'Coordinator must seal exact bytes and same independent judge decides.'}
(P/'delivery-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
