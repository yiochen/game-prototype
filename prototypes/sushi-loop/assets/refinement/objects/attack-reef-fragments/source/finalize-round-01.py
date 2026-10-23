"""Serialize authored metadata and the exact actual-used resource closure for ROOT.

This is an editor handoff inventory, never a packet, gate, seal, or approval.
Run only in a fresh reproduction directory or before the first immutable handoff.
"""
from pathlib import Path
import json,hashlib
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
metadata=json.loads((S/'round-01-finalization-inputs.json').read_text())
report=C/'consumer-v2/browser-report.json';browser=json.loads(report.read_text())
for helper in browser['helpers']:helper['path']=helper['path'].replace('source/round-01-inputs/consumer-v2/','source/round-01-inputs/consumer/')
browser['metadataCorrection']='Helper path labels corrected from consumer-v2 to actual source/round-01-inputs/consumer after capture; launch and imported helper bytes were unchanged and retained exact099/570 hashes.'
dump(report,browser)
preview=C/'previews/preview-map.json';mapping=json.loads(preview.read_text())
mapping['motion']['path']='candidates/round-01/consumer-v2/full-chromium/actual-playback-allphase-windup.png'
mapping['motion']['requiredSiblingSheets']=['candidates/round-01/consumer-v2/'+mode+'/actual-playback-allphase-'+clip+'.png' for mode in ['full-chromium','headless-shell'] for clip in ['windup','active','recovery']]
mapping['motion']['videos']=['candidates/round-01/consumer-v2/'+mode+'/actual-consumer-session.webm' for mode in ['full-chromium','headless-shell']]
dump(preview,mapping)
ledger=json.loads((C/'native-validation.json').read_text());motion=json.loads((C/'motion-validation.json').read_text());inspection=json.loads((C/'consumer-v2/inspection-report.json').read_text());published=json.loads((C/'published-frame-validation.json').read_text())
assert ledger['complete'] and len(ledger['captureRecords'])==144
assert all(p['all144PhasesDecoded'] for p in inspection['playback'])
validation=metadata['authoredValidation'];validation['projectSHA256']=sha(S/'round-01.blend')
validation['actualCanonicalSAllphaseUnion']={'min':[min(r['canonicalSBounds']['min'][j] for r in ledger['captureRecords']) for j in range(3)],'max':[max(r['canonicalSBounds']['max'][j] for r in ledger['captureRecords']) for j in range(3)]}
validation['actualMeasuredAllphaseClearanceAndProjectedContainment']=all(r['clearancePass'] and r['canvasContainmentPass'] for r in ledger['captureRecords'])
validation['allAtlasCellsEqualPublishedRGBA']=published['allAtlasCellsEqualPublishedRGBA']
validation['actualNativeTerminalHoldAndClipBoundaries']['maxEvaluatedVertexDifference']=max(x['maximumEvaluatedVertexError'] for x in motion['actualSavedActionTerminalHold']+motion['actualSavedActionClipBoundaries'])
validation['actualBrowserModes']=[{'mode':m['mode'],'version':m['browserVersion'],'launchOptions':m['options'],'DPR':m['deviceScaleFactor'],'viewport':m['viewport'],'pageErrors':m['errors'],'all144PhasesDecoded':next(p['all144PhasesDecoded'] for p in inspection['playback'] if p['mode']==m['mode'])} for m in browser['modes']]
dump(C/'validation.json',validation)
delivery=metadata['deliveryBase']
paths=[]
for p in (S/'round-01-inputs').rglob('*'):
 if p.is_file():paths.append(p)
source_names=['construction-acknowledgment-v1.json','construction-acknowledgment-v1.json.sha256','build-round-01.py','capture-round-01.py','publish-round-01.py','capture-consumer-round-01-v2.mjs','inspect-consumer-round-01-v2.py','inventory-round-01.py','finalize-round-01.py','round-01-finalization-inputs.json','round-01-recipe.json','round-01-executed-commands.json','round-01-build.log','round-01-capture.log','round-01-publish.log','round-01-consumer-v2.log','round-01-inspection-v2.log','round-01-inventory.log']
paths += [S/name for name in source_names]
paths += list((S/'round-01-records').glob('*.json'))
for p in C.rglob('*'):
 if p.is_file() and 'consumer' not in p.relative_to(C).parts and p.name not in ['delivery-draft.json','delivery.json','handoff.json','resource-manifest.json'] and '__pycache__' not in p.parts:paths.append(p)
paths=sorted(set(paths));assert all(p.stat().st_size<100_000_000 for p in paths)
delivery['resources']={str(p.relative_to(B)):str(p.relative_to(B)) for p in paths if p!=S/'round-01.blend'}
dump(C/'delivery.json',delivery)
manifest=[{'path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(paths+[S/'round-01.blend',C/'delivery.json']))]
diagnostics=[p for p in (C/'consumer').rglob('*') if p.is_file()]+[S/n for n in ['capture-consumer-round-01.mjs','inspect-consumer-round-01.py','round-01-consumer.log','round-01-inspection.log']]
dump(C/'resource-manifest.json',{'asset':'attack-reef-fragments','round':'round-01','pathBase':'object-root','purpose':'editor immutable handoff resource inventory, not candidate packet or approval','resources':manifest,'diagnosticAttempt01':{'reason':'Videoaudit correctly rejected two missing phase0 samples; retainedhistory, notfinal evidence.','resources':[{'path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size} for p in diagnostics]}})
handoff=metadata['handoffBase']
for key,path in [('project',S/'round-01.blend'),('delivery',C/'delivery.json'),('validation',C/'validation.json'),('resourceManifest',C/'resource-manifest.json'),('constructionAcknowledgment',S/'construction-acknowledgment-v1.json')]:
 handoff[key]={'path':str(path.relative_to(B)),'sha256':sha(path)}
dump(C/'handoff.json',handoff)
print(json.dumps({key:handoff[key] for key in ['project','delivery','validation','resourceManifest']}|{'handoffSHA256':sha(C/'handoff.json'),'resources':len(manifest)},indent=2))
