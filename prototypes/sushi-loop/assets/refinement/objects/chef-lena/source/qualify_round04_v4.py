"""Portable dual-result qualification. Reads immutable raw pixels; edits none.
Run Python with Pillow/NumPy after native guard measurement, from any cwd.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,collections
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-04';V=C/'v4';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();jh=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();brief=O/'brief-v4-held-food-native-repeatability.json';criteria=O/'reviews/proposedcriteria-held-food-v4-alpha-repeatability.json';assert sha(brief)=='2060f5caad378986e4a1c01f1ba71803dbfda9c98ac73b0a8daa1d56723cd0d7';assert sha(criteria)=='55c37e8d27918dd35589ba8c37c30be7a0b7e90f1509ce8fd619ed2aaac03e10';crit=json.loads(criteria.read_text());rule=crit['technicalAcceptance']['controlledFullFrameComparison']['nativeRepeatabilityRule'];named=(rule['clip'],rule['facing'],rule['index']);xy=rule['nativeXY'];accepted=rule['acceptedNativeControlAndReplayRGBAValues'];state=rule['nativeStateSHA256'];sourceSHA=sha(P/'round-03.blend');basisSHA=sha(P/'round-02.blend');assert sourceSHA==crit['unchangedArtBasis']['sha256'] and basisSHA==crit['approvedBodySourceSHA256'];assert sha(C/'controlled-comparison.json')=='08a73bbf37e190021cef2c2fed0b6a486f777436125befdcf0b8f5cfbed9c067';assert sha(C/'controls/hold-W/007.png')=='bb4965894d96358fafab661df46aa2b61d8b5b709c4dbd5e04f380a459893ca3';assert sha(C/'alpha-causal-evidence.json')=='5457734a6057730b08a6fd33c44b015cfc9679440efb1335cea13d09b3805dd6'
original=json.loads((C/'controlled-comparison.json').read_text());controls=json.loads((C/'control-native-frames.json').read_text());bykey={(x['clip'],x['direction'],x['index']):x for x in controls['rows']};construction=json.loads((C/'control-construction.json').read_text());assert construction['candidateSceneLoaded'] is False and construction['sourceSaved'] is False

def resolve(path,base=O):
 p=Path(path)
 if p.is_absolute():return p
 if (O/p).is_file():return O/p
 return base/p

def validate_snapshot(s):
 data={k:v for k,v in s.items() if k!='snapshotSHA256'};assert jh(data)==state==s['snapshotSHA256']
 for k,r in s['arrays'].items():
  ar=np.array(r['values'],dtype=np.float32);assert hashlib.sha256(ar.tobytes()).hexdigest()==r['float32SHA256'];assert [float(x).hex() for x in ar.flatten()]==r['losslessHexScalars']
 return s
# Read actual new native measurements, not a renamed ledger boolean.
guards=[]
for p in sorted((V/'native-guards').glob('*.json')):
 r=json.loads(p.read_text());snap=validate_snapshot(r['snapshot']);assert sha(resolve(r['path']))==r['sha256'];assert r['sourceSaved'] is False;assert r['sourceSHA256'] in [basisSHA,sourceSHA];guards.append((p,r,snap))
assert len(guards)==2 and {r['independentApproved02Patch'] for p,r,s in guards}=={True,False}
referenceSnapshot=guards[0][2]
for p,r,s in guards:assert s==referenceSnapshot
cn=bykey[named];assert cn['food']['matrix']==referenceSnapshot['arrays']['foodWorldMatrix']['values'];assert cn['food']['worldCorners']==referenceSnapshot['arrays']['foodEvaluatedWorldVertices']['values'];assert cn['food']['uv']==referenceSnapshot['arrays']['foodEvaluatedUV']['values'];assert cn['rootMatrix']==referenceSnapshot['foodRootParentMatrix'];assert cn['cameraMatrix']==referenceSnapshot['camera']['matrix'];assert construction['after']['vertices']==referenceSnapshot['arrays']['foodEvaluatedLocalVertices']['values'];assert construction['after']['drivers']==referenceSnapshot['foodDrivers'];assert construction['after']['rayFlags']==referenceSnapshot['foodRayFlags'];assert cn['blenderFrame']==rule['blenderFrame'];assert cn['actualRender']['seed']==referenceSnapshot['cycles']['seed'];assert cn['actualRender']['samples']==referenceSnapshot['cycles']['samples'];assert cn['actualRender']['device']==referenceSnapshot['cycles']['device'];assert cn['actualRender']['view']==referenceSnapshot['view']['view_transform'];assert cn['actualRender']['look']==referenceSnapshot['view']['look'];assert cn['actualRender']['exposure']==referenceSnapshot['view']['exposure'];assert cn['actualRender']['gamma']==referenceSnapshot['view']['gamma'];assert (cn['dimensions']==rule['nativeFrameSize'])
originalState={'currentNativeStateSHA256':state,'freshMeasurements':[{'path':str(p.relative_to(O)),'sha256':sha(p),'sourceSHA256':r['sourceSHA256'],'independentApproved02Patch':r['independentApproved02Patch']} for p,r,s in guards],'originalFrameStateMatchedFreshGuard':True,'matchedFields':['evaluated food matrix/worldvertices/fullUV','top-only localvertices','root/camera matrices','drivers/ray flags','native frame/seed/device/samples/view/look/exposure/gamma'],'boundSourceAndConstructionReconstructRemainingNativeSettingsExactly':True}

def comparison(nativePath,shippingPath,key,nativeSHA=None,shippingSHA=None):
 npth=resolve(nativePath);spth=resolve(shippingPath)
 if nativeSHA:assert sha(npth)==nativeSHA
 if shippingSHA:assert sha(spth)==shippingSHA
 ni=Image.open(npth);si=Image.open(spth);assert ni.mode==si.mode=='RGBA' and ni.size==si.size==(384,640);a=np.array(ni);b=np.array(si);d=np.abs(a.astype(np.int16)-b.astype(np.int16));alpha=[];violations=[]
 for y,x in np.argwhere(d[:,:,3]>0):
  q={'nativeXY':[int(x),int(y)],'controlOrReplayRGBA':a[y,x].tolist(),'immutableShippingRGBA':b[y,x].tolist(),'differenceRGBA':d[y,x].tolist()};namedSample=key==named and [int(x),int(y)]==xy;q['namedRuleEvaluated']=namedSample;q['finiteWholeRGBAMembership']=a[y,x].tolist() in accepted if namedSample else False;q['nativeStateGuardSHA256']=state if namedSample else None;q['qualified']=namedSample and q['finiteWholeRGBAMembership'] and b[y,x].tolist()==rule['immutableShippingRGBA'] and sha(spth)==rule['immutableShippingPNG_SHA256'];alpha.append(q)
  if not q['qualified']:violations.append({'kind':'unqualifiedAlphaDifference',**q})
 rgbBad=np.argwhere((d[:,:,:3]>1).any(2))
 for y,x in rgbBad:violations.append({'kind':'RGBAboveOne','nativeXY':[int(x),int(y)],'nativeRGBA':a[y,x].tolist(),'shippingRGBA':b[y,x].tolist(),'differenceRGBA':d[y,x].tolist()})
 namedCheck=None
 if key==named:
  namedCheck={'nativeXY':xy,'nativeRGBA':a[xy[1],xy[0]].tolist(),'shippingRGBA':b[xy[1],xy[0]].tolist(),'acceptedWholeRGBAValues':accepted,'finiteSetMember':a[xy[1],xy[0]].tolist() in accepted,'nativeStateSHA256':state,'shippingFileSHA256':sha(spth),'shippingFileMatchesFrozenHash':sha(spth)==rule['immutableShippingPNG_SHA256']}
  if not(namedCheck['finiteSetMember'] and namedCheck['shippingFileMatchesFrozenHash'] and namedCheck['shippingRGBA']==rule['immutableShippingRGBA']):violations.append({'kind':'namedSampleGuardFailure',**namedCheck})
 zero=(a[:,:,3]==0)&(b[:,:,3]==0)
 return {'clip':key[0],'direction':key[1],'index':key[2],'nativePath':str(npth.relative_to(O)),'nativeSHA256':sha(npth),'shippingPath':str(spth.relative_to(O)),'shippingSHA256':sha(spth),'dimensions':[384,640],'maximumRGBA':d.max((0,1)).tolist(),'unequalCountsRGBA':(d>0).sum((0,1)).tolist(),'aboveOneCountsRGBA':(d>1).sum((0,1)).tolist(),'rawAlphaDifferences':alpha,'strictV3AlphaExact':not alpha,'strictV3FailurePixels':int(((d[:,:,3]>0)|(d[:,:,:3]>1).any(2)).sum()),'strictV3Pass':not alpha and not len(rgbBad),'namedFiniteRuleCheck':namedCheck,'zeroAlphaRGBMaximum':d[:,:,:3][zero].max(0).tolist() if zero.any() else [0]*3,'v4Violations':violations,'v4Pass':not violations,'noPixelsMaskedOrChanged':True}
rows=[]
for r in original['rows']:
 key=(r['clip'],r['direction'],r['index']);x=comparison(r['controlPath'],r['shippingPath'],key,r['controlSHA256'],r['shippingSHA256']);assert x['maximumRGBA']==r['channelMaximumAbsoluteDifference'];assert x['unequalCountsRGBA']==r['channelUnequalCounts'];assert x['strictV3Pass']==r['pass'];assert x['strictV3FailurePixels']==r['overTolerancePixels'];rows.append(x)
assert len(rows)==192 and sum(r['strictV3FailurePixels'] for r in rows)==1 and not all(r['strictV3Pass'] for r in rows)
repeats=[];snapshotCount=0
paths=[*sorted((C/'alpha-diagnostic').glob('*-repeats.json')),O/'reviews/alpha-repeatability-independent-evidence/judge-control-repeats.json',O/'reviews/alpha-repeatability-independent-evidence/judge-shipping-repeats.json']
for p in paths:
 data=json.loads(p.read_text());assert data['sourceSaved'] is False;group=[]
 for r in data['rows']:
  s=validate_snapshot(r['snapshot']);assert s==referenceSnapshot;snapshotCount+=1;path=resolve(r['path'],p.parent);x=comparison(path,O/'candidates/round-03/frames/hold-W/007.png',named,r['sha256'],rule['immutableShippingPNG_SHA256']);group.append(x)
 repeats.append({'label':data['label'],'metadataPath':str(p.relative_to(O)),'metadataSHA256':sha(p),'renders':len(group),'allNativeSnapshotsRecomputedToFrozenHash':True,'rows':group})
assert snapshotCount==60
freshGuardRows=[comparison(resolve(r['path']),O/'candidates/round-03/frames/hold-W/007.png',named,r['sha256'],rule['immutableShippingPNG_SHA256']) for p,r,s in guards]
replays=[]
for r in json.loads((C/'replay-manifest.json').read_text())['rows']:replays.append(comparison(r['path'],r['reference'],(r['clip'],r['direction'],r['index']),r['sha256']))
violations=[{'dataset':'full192','key':[r['clip'],r['direction'],r['index']],'violation':z} for r in rows for z in r['v4Violations']]+[{'dataset':'repeat','label':g['label'],'violation':z} for g in repeats for r in g['rows'] for z in r['v4Violations']]+[{'dataset':'freshGuardOrReplay','violation':z} for r in [*freshGuardRows,*replays] for z in r['v4Violations']]
report={'schemaVersion':1,'asset':'chef-lena','criteriaVersion':crit['criteriaVersion'],'brief':{'path':brief.name,'sha256':sha(brief)},'criteria':{'path':str(criteria.relative_to(O)),'sha256':sha(criteria)},'script':{'path':str(Path(__file__).relative_to(O)),'sha256':sha(Path(__file__))},'strictV3Result':{'originalLedger':'candidates/round-04/controlled-comparison.json','originalLedgerSHA256':sha(C/'controlled-comparison.json'),'originalLedgerBytesUnchanged':True,'originalAll192Pass':original['all192Pass'],'recomputedAll192Pass':all(r['strictV3Pass'] for r in rows),'recomputedFailurePixels':sum(r['strictV3FailurePixels'] for r in rows),'allRawAlphaDifferences':[{'key':[r['clip'],r['direction'],r['index']],**a} for r in rows for a in r['rawAlphaDifferences']],'meaning':'The original strictv3 exact-alpha test still fails1. Its false boolean and failed native control remain immutable.'},'frozenV4Result':{'nativeRepeatabilityRule':rule,'nativeStateGuard':originalState,'comparedFullFrames':192,'comparedPixels':192*384*640,'comparedRGBAChannelValues':192*384*640*4,'maximumRawRGBA':np.max([r['maximumRGBA'] for r in rows],0).tolist(),'allFullFrameRGBWithinOne':all(max(r['maximumRGBA'][:3])<=1 for r in rows),'allOtherAlphaExact':all(a['namedRuleEvaluated'] and a['qualified'] for r in rows for a in r['rawAlphaDifferences']),'violations':violations,'violationCount':len(violations),'all192Qualified':all(r['v4Pass'] for r in rows),'zeroViolationsAcrossControlsRepeatsGuardsReplays':not violations,'everyRawDifferenceRetained':True,'noMasksOrGeneralAlphaTolerance':True,'shippingBytesReplacedOrRepaired':False},'fullFrameRows':rows,'retainedNativeRepeats':{'editorRenders':36,'independentJudgeRenders':24,'all60NativeSnapshotsRecomputed':True,'groups':repeats},'newFreshNativeGuardMeasurements':freshGuardRows,'unchangedSourceFreshRepresentativeReplays':replays,'causalLimit':'Finite observed wholeRGBA set for this bound phase/state/runtime only. Internal Cycles/Metal rounding stage is not established. Any additional location/phase/value/state fails; this rule never extends automatically.','visualApproval':'Independent judge must still inspect retained visible food/body/contact/temporal/background bar and old-input radiance comparisons. This qualification does not self-approve appearance.'};assert not report['strictV3Result']['recomputedAll192Pass'];assert report['frozenV4Result']['all192Qualified'] and not violations;(V/'qualification.json').write_text(json.dumps(report,indent=2));print(json.dumps({'strictV3FailurePixels':report['strictV3Result']['recomputedFailurePixels'],'strictV3Pass':report['strictV3Result']['recomputedAll192Pass'],'v4QualifiedFrames':sum(r['v4Pass'] for r in rows),'v4Violations':len(violations),'nativeSnapshotGuard':state,'retainedNativeRepeats':snapshotCount,'qualificationSHA256':sha(V/'qualification.json')},indent=2))
