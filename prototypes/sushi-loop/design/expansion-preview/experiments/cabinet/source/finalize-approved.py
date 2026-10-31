"""Copy exact independently approved cabinet bytes. Never rerenders or rewrites art."""
import json,hashlib,shutil,subprocess,sys,datetime
from pathlib import Path
E=Path(__file__).resolve().parent.parent;P=E/'candidates/evidence-02/packet.json';R=E/'reviews/evidence-02.json';F=E/'final';F.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
subprocess.run([sys.executable,'/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py','verify','--packet',str(P),'--review',str(R)],check=True)
p=json.loads(P.read_text());r=json.loads(R.read_text());records={}
def exact(record,name):
 src=(P.parent/record['path']).resolve();assert sha(src)==record['sha256'];dst=F/name
 if dst.exists():assert sha(dst)==record['sha256'],f'Would replace different final bytes: {dst}'
 else:shutil.copyfile(src,dst)
 assert sha(dst)==record['sha256'];records[name]={'sha256':record['sha256'],'source':str(src),'bytes':dst.stat().st_size}
exact(p['files']['candidateProject'],'cabinet.blend')
for facing,record in p['candidateRenders'].items():exact(record,'static-'+facing+'.png')
for name,record in p['previews'].items():exact(record,name+'.png')
# Validation is retained as exact evidence beside the standalone editable model.
exact(p['files']['nativeValidation'],'validation.json')
m={'asset':'garbage-cabinet','finalizedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'approve','candidatePacket':str(P),'candidatePacketSHA256':sha(P),'independentReview':str(R),'independentReviewSHA256':sha(R),'files':records,'capture':p['capture'],'physicalEnvelope':{'x':[-1,1],'y':[-.5,.5],'heightMaximum':1.5,'ground':0},'resourceClosure':{'nativeBlend':'Standalone, no linked libraries or image dependencies. All wood and metal procedural/native materials and all58 editable meshes included.','recipe':str(E/'source/recipe-round01.py')},'remainingDifferences':r.get('remainingDifferences',[]),'scope':'Only the exact four static native captures and inspected previews are approved. Native animation remains deferred; original production assets unchanged.'}
(F/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps({'final':str(F),'manifest':str(F/'manifest.json'),'files':{k:v['sha256'] for k,v in records.items()}},indent=2))
