from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;O=H.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=H/'supplemental-evidence.json';R=O/'reviews/round-01.json';G=H/'gates.json';P=O/'candidates/round-01/packet.json';m=json.loads(M.read_text());r=json.loads(R.read_text());g=json.loads(G.read_text());assert sha(P)==m['candidatePacketSHA256']==r['candidatePacketSHA256']==g['candidatePacketSHA256'];assert sha(M)==r['supplementalEvidence']['sha256']==g['supplementalManifestSHA256'];assert sha(R)==g['reviewSHA256'];assert g['allExitZero']
for f in m['files']:assert sha(O/f['path'])==f['sha256'],f['path']
for c in g['commands']:
 assert c['exitCode']==0
 assert sha(Path(c['helper']['path']))==c['helper']['sha256']
 for name in ['stdout','stderr']:assert sha(O/c[name]['path'])==c[name]['sha256']
for group in ['files','candidateRenders','previews']:
 for f in json.loads(P.read_text())[group].values():assert sha(P.parent/f['path'])==f['sha256']
result={'asset':'portal-entry','round':'round-01','verdict':r['verdict'],'status':'EXACT_BOUND_REVIEW_AND_GATES_SEALED','acyclicOrder':['supplemental-evidence.json','reviews/round-01.json','gates.json and gate outputs','postseal.json'],'candidatePacket':{'path':'candidates/round-01/packet.json','sha256':sha(P)},'source':{'path':'source/round-01.blend','sha256':sha(O/'source/round-01.blend')},'supplementalEvidence':{'path':str(M.relative_to(O)),'sha256':sha(M),'files':len(m['files'])},'review':{'path':str(R.relative_to(O)),'sha256':sha(R)},'gates':{'path':str(G.relative_to(O)),'sha256':sha(G),'allExitZero':g['allExitZero'],'outputs':[{'name':c['name'],'exitCode':c['exitCode'],'stdout':c['stdout'],'stderr':c['stderr']} for c in g['commands']]},'allManifestFilesVerified':True,'candidateAndFrozenInputsUnchanged':True,'approvalScope':'Only this exact portal-entry candidate source/renders/packet. No family, production, Godot, deployment or device approval.'}
assert not (H/'postseal.json').exists();(H/'postseal.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'reviewSHA256':sha(R),'supplementSHA256':sha(M),'gatesSHA256':sha(G),'postsealSHA256':sha(H/'postseal.json'),'manifestFiles':len(m['files']),'verdict':r['verdict'],'allGateExitZero':g['allExitZero']},indent=2))
