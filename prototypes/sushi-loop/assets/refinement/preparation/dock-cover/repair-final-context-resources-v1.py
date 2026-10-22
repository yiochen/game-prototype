from pathlib import Path
import hashlib,json,shutil,re
r=Path(__file__).resolve().parents[2];f=r/'objects/dock-cover';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=f/'brief-v3-final-context.json';assert h(old)=='95e23f52c1a18cf4f38d5b425ad33341fb78797a29cc001642446efc00106d26';b=json.loads(old.read_text());fixed={};repairs=[]
for alias,value in b['technicalResources'].items():
 if (f/value).is_file():fixed[alias]=value;continue
 assert re.fullmatch('[0-9a-f]{64}',value) and (f/alias).is_file() and h(f/alias)==value,(alias,value)
 fixed['final-context:'+alias]=alias;repairs.append({'path':alias,'sha256':value,'reason':'Sealer expects alias-to-relative-path; previous descriptor stored SHA as its value.'})
assert len(repairs)==31
record={'asset':'dock-cover','scope':'Technical file-list correction only; all native/style/camera/geometry/motion/contact/visibility/envelope requirements unchanged. No candidate approval.','originalBrief':{'path':'brief-v3-final-context.json','sha256':h(old)},'nativeContractSHA256':h(f/'inputs/root-native-contract-v3-final-context.json'),'verifiedFileRepairs':repairs,'replacementBrief':'brief-v4-resource-paths.json','preservation':'Original v3 brief, executed freeze script and all referenced files remain byte-exact.'}
p=f/'inputs/root-resource-path-reconciliation-v1.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');fixed['final-context:resource-path-reconciliation']='inputs/root-resource-path-reconciliation-v1.json';fixed['final-context:main-release']='inputs/final-main-release-v1.json';assert all((f/path).is_file() for path in fixed.values());b['technicalResources']=fixed;b['resourcePathReconciliation']={'path':str(p.relative_to(f)),'sha256':h(p)};new=f/'brief-v4-resource-paths.json';assert not new.exists();new.write_text(json.dumps(b,indent=2)+'\n');shutil.copyfile(new,f/'brief.json');print('New technical-only brief',h(new),'all',len(fixed),'resource paths valid; old v3 retained')
