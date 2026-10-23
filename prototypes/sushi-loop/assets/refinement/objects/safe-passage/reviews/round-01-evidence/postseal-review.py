from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'supplemental-manifest.json';manifest=json.loads(mp.read_text());review=O/'reviews/round-01.json';r=json.loads(review.read_text());gates=json.loads((H/'gates.json').read_text())
assert r['verdict']=='approve' and r['blockers']==[]
assert r['candidatePacketSHA256']==sha(C/'packet.json')==manifest['candidatePacketSHA256']==gates['candidatePacketSHA256']
assert r['supplementalEvidence']=={'path':str(mp.relative_to(O)),'sha256':sha(mp)}
for f in manifest['files']:assert sha(O/f['path'])==f['sha256'],f['path']
assert gates['reviewSHA256']==sha(review) and gates['allExitZero']
for g in gates['gates']:
 assert g['exitCode']==0
 assert sha(Path(g['helper']))==g['helperSHA256']
 for k in ['stdout','stderr']:assert sha(O/g[k]['path'])==g[k]['sha256']
packet=json.loads((C/'packet.json').read_text());records=[*packet['files'].values(),*packet['candidateRenders'].values(),*packet['previews'].values()]
for f in records:assert sha((C/f['path']).resolve())==f['sha256'],f['path']
prep=O/'reviews/preparation-v1/hash-manifest.json';pd=json.loads(prep.read_text())
assert sha(prep)=='657f028dfa88507e164e6096ce87a3928b3b0dcbd850b7134ed9aa6e2d507d70'
for f in pd['files']:assert sha(O/f['path'])==f['sha256'],f['path']
assert not list(H.rglob('__pycache__'))
files=[p for p in H.rglob('*') if p.is_file()];assert all(p.stat().st_size<100000000 for p in files)
def descriptor(p):return {'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size}
outputs=[]
for g in gates['gates']:
 for k in ['stdout','stderr']:outputs.append(descriptor(O/g[k]['path']))
seal={'asset':'safe-passage','round':'round-01','status':'sealed-exact-packet-independent-approval','verdict':'approve','sealedAtUTC':datetime.now(timezone.utc).isoformat(),'pathBase':'object root: prototypes/sushi-loop/assets/refinement/objects/safe-passage','candidatePacket':descriptor(C/'packet.json'),'candidateSource':descriptor(O/'source/round-01.blend'),'review':descriptor(review),'supplementalEvidence':descriptor(mp),'gates':descriptor(H/'gates.json'),'gateOutputDescriptors':outputs,'allGatesExitZero':True,'unchangedGateHelpers':[{'path':g['helper'],'sha256':g['helperSHA256'],'exitCode':g['exitCode']} for g in gates['gates']],'verifiedSupplementalMembers':len(manifest['files']),'verifiedPacketRecords':len(records),'verifiedOriginalPreparationMembers':len(pd['files']),'originalPreparationManifestSHA256':sha(prep),'sourceAndFrozenInputsUnchangedAfterReview':True,'maxOwnFileBytes':max(p.stat().st_size for p in files),'allOwnFilesBelow100MB':True,'noOwnPycache':True,'postsealScript':descriptor(Path(__file__)),'scope':'Approval binds only the exact safe-passage round-01 packet, source and submitted art. No candidate changes, extra agents, Git/index, production, publication, live Blender or device actions. No broader family/Godot/full-game acceptance.'}
p=H/'postseal.json';assert not p.exists();p.write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'verdict':'approve','reviewSHA256':sha(review),'supplementalManifestSHA256':sha(mp),'gatesSHA256':sha(H/'gates.json'),'postsealSHA256':sha(p),'verifiedSupplementalMembers':len(manifest['files']),'verifiedPacketRecords':len(records),'verifiedOriginalPreparationMembers':len(pd['files'])},indent=2))
