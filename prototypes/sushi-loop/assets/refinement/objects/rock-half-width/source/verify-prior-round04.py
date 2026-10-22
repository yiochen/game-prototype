"""Read-only binding check for prior signed rounds and current external runtime."""
import json,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-04';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
expected=[('round-01','85e6cf09b3ebc5c60ab43d1a2623b2f60f6a01ea32a94da4d0e514c895b3790b','e6590160f38f7f2f3bfaaad461e8ef795da7bbb25eee5625dc4f8f1089ee69ed'),('round-02','537a23c0e259325b9ea932eed9b409f8da4952a6462ce6536a933b30717a2fa1','27bef6ee60807798a68730ed27f5af69472231b89cca950e729f984f1f29dbbe'),('round-03','e6e8d20d76627da2a5a7085409e33f98255348cfcbb5875f48cbdecd84076fb4','7178adbfc84dfc666b6e6cb1c83f56fc4bb25d10c78a4b55e5c0c3fc3d9f4b0d')]
for r,ph,rh in expected:
 packet=P/f'candidates/{r}/packet.json';review=P/f'reviews/{r}.json';assert sha(packet)==ph;assert sha(review)==rh
 x=json.loads(packet.read_text())
 records=list(x['files'].items())+[(f'candidateRenders:{i}',q) for i,q in x['candidateRenders'].items()]+[(f'previews:{i}',q) for i,q in x['previews'].items()]
 for name,item in records:
  f=(packet.parent/item['path']).resolve();assert sha(f)==item['sha256'],(r,name,str(f))
 rows.append({'round':r,'packetSHA256':ph,'reviewSHA256':rh,'verifiedPacketRecords':len(records),'allMatch':True})
for n,h in [('brief.json','73f2cef927fc54ed4d97853b326b321928b33383c9ebb6802bee9ae513f96244'),('source/initial-observations.json','03777f1245ea912dfb06a248ad5e1e6d1776dc84b98061aa125c56a532c7c96d')]:assert sha(P/n)==h,n
(O/'prior-round-integrity.json').write_text(json.dumps({'priorRounds':rows,'allPriorBytesMatch':True,'newRound':'round-04','note':'Read-only verification; prior source, candidate, delivery, packet, reviews, dependencies and frozen inputs were never rewritten.'},indent=2)+'\n')
binary=pathlib.Path('/Applications/Blender.app/Contents/MacOS/Blender');wrapper=pathlib.Path('/opt/homebrew/Caskroom/blender/5.2.2/.homebrew-command-wrappers/blender')
commands=['PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b --factory-startup --python source/reproduce-round04.py','PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b --factory-startup --python source/replay-round04.py','PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b --factory-startup --python source/audit-field-round04.py']
commands += ['PYTHONDONTWRITEBYTECODE=1 /Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 source/'+n+'-round04.py' for n in ['publish','verify-prior','analyze','compare','inspect-strips','finalize']]
commands += ['DEBUG=pw:browser node source/capture-consumer-round04.mjs']
(O/'commands-and-blender-runtime.json').write_text(json.dumps({'Blender':{'path':str(binary),'bytes':binary.stat().st_size,'sha256':sha(binary),'version':'5.2.2 LTS','wrapper':{'path':str(wrapper),'sha256':sha(wrapper)},'policy':'external binary hashed, not copied'},'commands':commands,'workingDirectory':'object root; scripts resolve their paths from their own location','scope':'Same executable and exact arguments as worktree-qualified invocations; background Blender only. Actual version/binary path also recorded by read-only native field audit.','unsubmittedExploration':'Native course tests and superseded pre-material-integration set retained outside final used closure in /tmp/rock-half-width-editor-unsubmitted. No unsubmitted image is used to repair or stand in for final native output.'},indent=2)+'\n')
print(json.dumps({'priorRecordsVerified':sum(q['verifiedPacketRecords'] for q in rows),'allPriorBytesMatch':True,'runtimeSHA256':sha(binary)}))
