from pathlib import Path
import hashlib,json,subprocess
O=Path(__file__).resolve().parents[1];repo=O.parents[5];H=O/'reviews/round-01-evidence';F=O/'final'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
expected={'candidates/round-01/packet.json':'f4d3f66a3094db075819e4927ead8baa0196ae7cca6726d831b8568692707bf3','source/round-01.blend':'1efc24a21f1ade2accdcca93446f2c4d9743df4437ad2e927c1c239849003aa4','reviews/round-01.json':'5d0f07176decbfd41c933388545d0520e5a0a6d648d41c5a3bfc415827f01ede','reviews/round-01-evidence/supplemental-manifest.json':'8db64fede6b9bd429d91be57df5b8c9b54816ab870ca0f9d628d393f542c9713','reviews/round-01-evidence/gates.json':'da2e7b0c8ab580f2ca751c18e0dc20d433c25a0ba19f8227e1677b88ddbd15db','reviews/round-01-evidence/postseal.json':'ee7fec607babc1cf6360d4febd914bcd9dd76829906cd9f16c0239ce9bf53883'}
for p,s in expected.items():assert sha(O/p)==s,p
s=read(H/'supplemental-manifest.json');g=read(H/'gates.json');seal=read(H/'postseal.json');r=read(O/'reviews/round-01.json')
assert r['verdict']=='approve' and r['blockers']==[]
pkt=expected['candidates/round-01/packet.json'];src=expected['source/round-01.blend'];rv=expected['reviews/round-01.json']
assert s['candidatePacketSHA256']==g['candidatePacketSHA256']==r['candidatePacketSHA256']==pkt
assert s['sourceSHA256']==r['candidateProjectSHA256']==src
assert g['reviewSHA256']==rv and g['allExitZero'] and seal['allGatesExitZero']
assert len(s['files'])==s['fileCount']==seal['verifiedSupplementalMembers']==498
count=0
def verify(value):
 global count
 if isinstance(value,dict):
  if 'path' in value and 'sha256' in value:
   p=Path(value['path']);p=p if p.is_absolute() else O/p
   assert sha(p)==value['sha256'],str(p)
   if 'bytes' in value:assert p.stat().st_size==value['bytes'],str(p)
   count+=1
  for v in value.values():verify(v)
 elif isinstance(value,list):
  for v in value:verify(v)
verify(s);verify(seal)
prep=O/'reviews/preparation-v1/hash-manifest.json';assert sha(prep)==seal['originalPreparationManifestSHA256']=='657f028dfa88507e164e6096ce87a3928b3b0dcbd850b7134ed9aa6e2d507d70'
assert len(read(prep)['files'])==seal['verifiedOriginalPreparationMembers']==309
verify(read(prep))
checks=[]
for gate in g['gates']:
 assert gate['exitCode']==0 and sha(gate['helper'])==gate['helperSHA256']
 verify(gate['stdout']);verify(gate['stderr'])
 p=subprocess.run(gate['argv'],cwd=gate['workingDirectory'],text=True,capture_output=True)
 checks.append({'name':gate['name'],'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 p.check_returncode()
result={'asset':'safe-passage','round':'round-01','boundHashes':expected,'supplementalMembers':498,'rootVerifiedDescriptors':count,'postsealNestedAndGateOutputHashesVerified':True,'supplementalSourceAndPacketScalarBindingsVerified':True,'unchangedHelperHashesVerified':True,'originalPreparationMembersVerified':309,'rerunGates':checks,'approvalScope':'Exact safe-passage candidate only; ROOT separately handles integration/publication.'}
(F/'root-review-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'asset':'safe-passage','status':'passed','verifiedDescriptors':count,'gates':len(checks)}))
