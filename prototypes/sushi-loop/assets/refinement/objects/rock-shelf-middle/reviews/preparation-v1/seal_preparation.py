import pathlib,hashlib,json,sys
B=pathlib.Path(__file__).parent;MF=B/'manifest.json';SF=B/'seal.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records():
 paths=sorted([p for p in B.rglob('*') if p.is_file() and p not in [MF,SF]],key=lambda p:p.as_posix())
 paths += [B.parent/n for n in ['initial.json','proposedcriteria.json','source-contract-proposal.json']]
 return [{'path':str(p.relative_to(B)) if B in p.parents else '../'+p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
if '--verify' in sys.argv:
 m=json.loads(MF.read_text());s=json.loads(SF.read_text());r=records()
 assert m['files']==r,'Payload changed/missing/new files';assert sha(MF)==s['manifestSHA256'],'Manifest changed';assert all(x['bytes']<100000000 for x in r),'File limit';print(json.dumps({'status':'verified','files':len(r),'bytes':sum(x['bytes'] for x in r),'manifestSHA256':sha(MF)},indent=2));sys.exit()
assert not MF.exists() and not SF.exists(),'Never overwrite a sealed preparation'
r=records();assert all(x['bytes']<100000000 for x in r)
m={'schema':'independent-judge-source-preparation-v1','asset':'rock-shelf-middle','scope':'PREPARATION ONLY; no candidate construction/approval or family/production approval','files':r,'resourceClosure':'Frozen original source blend, own inputs/brief/prompts/instructions/skill, original family authoring source, actual capture/publisher/packing dependencies, actual consumer functions, executable minimal Playwright/Pillow helper/native closure, own reproduction/measurement scripts and exact source+sampling-study evidence. External application/Python/browser runtime binaries pinned by identity; no massive application trees duplicated.','pending':'Root freeze criteria+source contract, then fresh editor candidate construction and original judge exact-packet review.'}
MF.write_text(json.dumps(m,indent=2)+'\n');payload=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();s={'asset':'rock-shelf-middle','stage':'preparation-only','manifest':'manifest.json','manifestSHA256':sha(MF),'payloadRecordsSHA256':payload,'files':len(r),'bytes':sum(x['bytes'] for x in r),'candidateVerdict':None,'immutable':'Do not mutate listed files; corrections require new versioned preparation/addendum.'};SF.write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
