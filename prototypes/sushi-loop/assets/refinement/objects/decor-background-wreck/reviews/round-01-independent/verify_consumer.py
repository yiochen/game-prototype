from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parent;O=P.parent.parent;S=O/'source/round-01-resources/consumer';PRE=O/'reviews/preparation-v1/resources/consumer';R=P/'resources';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();records=[]
for f in S.rglob('*'):
 if not f.is_file():continue
 rel=f.relative_to(S);d=R/'consumer'/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
 if rel.parts[0]!='sprites' or 'decor-background-wreck' not in rel.parts:
  records.append({'path':str(f.relative_to(O)),'sha256':sha(f),'preparationEqual':(PRE/rel).exists() and sha(f)==sha(PRE/rel)})
for rel in ['round-01-consumer.mjs']:
 shutil.copy2(O/'source'/rel,R/rel)
ledger=json.loads((O/'candidates/round-01/consumer-ledger.json').read_text());fixture=json.loads((S/'fixture.json').read_text());prefixture=json.loads((PRE/'fixture.json').read_text());changes=[]
for a,b in zip(fixture['objects'],prefixture['objects']):
 changes.append({'object':a['id'],'changedFields':[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]})
configs=json.loads((O/'brief.json').read_text())['qualityCriteria']['requiredEvidence']['preparedConsumerCasesPerMode'];runs=[]
for run in ledger['runs']:
 cases=run['cases'];configMatches=[]
 for actual,want in zip(cases,configs):configMatches.append(all(actual.get(k)==v for k,v in want.items()))
 runs.append({'mode':run['mode'],'browserVersion':run['browserVersion'],'launch':run['launch'],'hostViewport':run['viewport'],'dpr':run['dpr'],'errors':run['errors'],'preparedConfigsMatch':configMatches,'allNativeSmoothingFalse':all(not c['smoothingAfterResize'] for c in cases+run['viewportContexts']),'allLoadedOwnRectsFramesCorrect':all(all(s['rect']==[0,0,384,704] and s['width']==192 and s['height']==352 for s in c['plan']['sprites'] if s['object']=='decor-background-wreck') for c in cases),'finalViewports':[v['viewport'] for v in run['viewportContexts']],'allActualScreenshotSHA256Match':all(sha(O/c['screenshot'])==c['screenshotSHA256'] for c in cases+run['viewportContexts'])})
# Static frame index stays0 for all source seconds, while companions may move independently.
staticOwn=[{'mode':run['mode'],'seconds':c['seconds'],'ownFrames':[v['index'] for v in c['frames'] if v['object']=='decor-background-wreck']} for run in ledger['runs'] for c in run['cases'] if c['kind']=='context']
# Recompute two-browser native/canvas and screenshot residuals independently.
from PIL import Image,ImageChops,ImageStat
comparisons=[]
a=ledger['runs'][0]['cases']+ledger['runs'][0]['viewportContexts'];b=ledger['runs'][1]['cases']+ledger['runs'][1]['viewportContexts']
for aa,bb in zip(a,b):
 x=Image.open(O/aa['screenshot']).convert('RGBA');y=Image.open(O/bb['screenshot']).convert('RGBA');df=ImageChops.difference(x,y);comparisons.append({'source':aa['screenshot'],'other':bb['screenshot'],'sameNativeCanvasRGBA':aa['nativeCanvasRGBA256']==bb['nativeCanvasRGBA256'],'sameCSSPixels':x.tobytes()==y.tobytes(),'maxRGBAChannelDifference':max(v[1] for v in df.getextrema()),'meanRGBAChannelDifference':ImageStat.Stat(df).mean})
env=json.loads((O/'candidates/round-01/environment.json').read_text());executables=[]
for e in env['actualBrowserExecutables']:
 f=Path(e['actualExecutable']);executables.append({'mode':e['mode'],'path':str(f),'sha256':sha(f),'matchesRecorded':sha(f)==e['sha256'],'runtimeNotCopied':True})
report={'asset':'decor-background-wreck','candidatePacketSHA256':sha(O/'candidates/round-01/packet.json'),'pathBase':'object-root','currentHelperMatchesOriginalPreparation':records,'fixtureMetadataChangesFromPreparation':changes,'candidateMetadataFieldsChecked':['frameSize','root','sourceScale','footprint','rootCell','directionFootprints','directionRootCells','layer','blocking','clips','interactions'],'browserRuns':runs,'ownStaticFrameIndices':staticOwn,'actualExecutableChecks':executables,'nativeVsCSSResiduals':comparisons,'limits':'Exact saved consumer technical code and all declared media independently examined; no redundant browser Cartesian replay. Bounded helper fixture is not fullReact UI/Godot/device evidence.'}
(P/'independent-consumer-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'metadataChanges':changes,'runs':runs,'sameNativeCanvases':sum(c['sameNativeCanvasRGBA'] for c in comparisons),'caseCount':len(comparisons),'actualExecutableHashesMatch':all(e['matchesRecorded'] for e in executables)},indent=2))
