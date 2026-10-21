"""Focused signed47→48 normal upgrade; no schema or gameplay changes while paused."""
import argparse,sys,json
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-exit-recovery')
from qa_common import *
from render_readiness import rendered
parser=argparse.ArgumentParser();parser.add_argument('--normal-apk',type=Path,required=True);parser.add_argument('--review-apk',type=Path,required=True);parser.add_argument('--runtime-commit',required=True);args=parser.parse_args()
n=json.loads(args.normal_apk.with_suffix('.build.json').read_text());r=json.loads(args.review_apk.with_suffix('.build.json').read_text())
assert n['package']==NORMAL and r['package']==REVIEW
assert n['version_code']==48 and r['version_code']==48 and n['version_name']=='0.4.8' and r['version_name']=='0.4.8'
assert n['source_files']==r['source_files'] and n['signer_sha256']==r['signer_sha256']=='9b465ce9e19fc9cfb1a3a34c6fa2e1e452d3bfc9cb6adb5c01918c1fcfc061ed'
assert sha(args.normal_apk)==n['apk_sha256'] and sha(args.review_apk)==r['apk_sha256']
assert all(sha(PROJECT/name)==digest for name,digest in n['source_files'].items())
report={'runtime_commit':args.runtime_commit,'version_name':'0.4.8','version_code':48,'emulator_serial':SERIAL,'input':'Actual adb tap/swipe/keyevent, production offline releases','physical_devices_touched':False,'review_gameplay_state_injected':False,'old_normal_baseline_state_injected':False,'customer_navigation_version':1,'customer_admission_version':1,'checks':[],'prior_47_full_regressions':'../../entrance-wait/android/android-verification-summary.json','repeated_unrelated_editor_checks':False}
def check(value,label):
 assert value,label
 report['checks'].append(label);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
primary=(BASE/'normal-v47-session-before-update.json').read_bytes();backup=(BASE/'normal-v47-backup-before-update.json').read_bytes()
check(data(NORMAL)[0]==primary and data(NORMAL,'session.backup.json')[0]==backup,'Normal47 primary and backup match their protected paused baseline')
print(call('install','-r',args.normal_apk,timeout=180).decode().strip(),flush=True)
check(installed_hash(NORMAL)==n['apk_sha256'],'Installed normal48 matches the exact signed release hash')
check(data(NORMAL)[0]==primary and data(NORMAL,'session.backup.json')[0]==backup,'Normal47→48 installation preserves both save files byte for byte before first launch')
launch(NORMAL);rendered(NORMAL,'normal-v48-upgraded-rendered');normal_raw,after=home(NORMAL,'normal-v48-restored');save(NORMAL,'normal-v48-before-review-backup',backup=True);call('shell','am','force-stop',NORMAL)
before=json.loads(json.loads(primary)['payload']);diff=[]
def compare(a,b,path=''):
 if isinstance(a,dict):
  assert isinstance(b,dict) and set(a)==set(b),path
  for k in a:compare(a[k],b[k],f'{path}.{k}' if path else k)
 elif isinstance(a,list):
  assert isinstance(b,list) and len(a)==len(b),path
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,f'{path}[{i}]')
 elif isinstance(a,(float,int)) and not isinstance(a,bool):
  assert a==b or (path=='remainder' and abs(a-b)<1e-7),(path,a,b)
  if a!=b:diff.append({'path':path,'from':a,'to':b,'absolute_difference':abs(a-b)})
 else:assert a==b,(path,a,b)
compare(before,after)
write('normal-no-schema-upgrade',{'from_version':'0.4.7','to_version':'0.4.8','prelaunch_primary_backup_byte_identical':True,'schema_fields_added_or_removed':[],'parsed_payload_exactly_equal':before==after,'observed_numeric_roundtrip_differences':diff,'remainder_only_tolerance':1e-7,'all_other_fields_exactly_equal':True,'old_random_state':before['random_state'],'new_random_state':after['random_state'],'old_elapsed':before['state']['elapsed'],'new_elapsed':after['state']['elapsed']})
check(same(before,after),'Normal47→48 restores the complete paused payload without schema additions or gameplay/RNG/time changes')
check(package_absent(REVIEW),'Review12 is absent before the real legacy47 fixture installation')
report.update(normal_apk_path=str(args.normal_apk),review_apk_path=str(args.review_apk),normal_package=NORMAL,review_package=REVIEW,signer_sha256=n['signer_sha256'],runtime_source_file_count=len(n['source_files']),runtime_source_fingerprint=n['runtime_source_fingerprint'],normal_apk_sha256=n['apk_sha256'],review_apk_sha256=r['apk_sha256'],upgrade_preserved_legacy_state=True)
write('android-editor-verification',report)
print(json.dumps({'upgrade_assertions':len(report['checks']),'passed':True}),flush=True)
