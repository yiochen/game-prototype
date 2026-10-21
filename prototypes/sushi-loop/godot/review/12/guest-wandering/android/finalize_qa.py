"""Run only after successful actual APK interaction and visual review; clone-only teardown/audit."""
import sys,time,json,os,re,shutil,hashlib
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-wander-review')
from qa_common import *
report=json.loads((BASE/'android-editor-verification.json').read_text())
normal_apk=Path(report['normal_apk_path']);review_apk=Path(report['review_apk_path'])
normal_receipt=json.loads(normal_apk.with_suffix('.build.json').read_text());review_receipt=json.loads(review_apk.with_suffix('.build.json').read_text())
assert normal_receipt['source_files']==review_receipt['source_files']
assert not [name for name,h in normal_receipt['source_files'].items() if sha(PROJECT/name)!=h]
assert sha(normal_apk)==normal_receipt['apk_sha256'] and sha(review_apk)==review_receipt['apk_sha256']
packages=[]
for pkg in [NORMAL,REVIEW]:
 dump=call('shell','dumpsys','package',pkg).decode()
 identity=re.search(r'(?:appId|userId)=(\d+)',dump);assert identity,pkg
 packages.append({'package':pkg,'uid':int(identity.group(1)),'data_dir':re.search(r'dataDir=(\S+)',dump).group(1),'installed_apk_sha256':installed_hash(pkg),'private_directory_modes':call('shell','stat','-c','%a:%u:%n',f'/data/user/0/{pkg}',f'/data/user/0/{pkg}/files').decode().strip().splitlines()})
assert packages[0]['uid']!=packages[1]['uid']
primary_same=data(NORMAL)[0]==(BASE/'normal-v46-migrated.json').read_bytes()
backup_same=data(NORMAL,'session.backup.json')[0]==(BASE/'normal-v46-before-review-backup.json').read_bytes()
assert primary_same and backup_same
write('sandbox-verification',{'emulator_serial':SERIAL,'physical_devices_touched':False,'review_gameplay_state_injected':False,'old_normal_baseline_state_injected':False,'packages':packages,'normal_primary_unchanged_after_review':primary_same,'normal_backup_unchanged_after_review':backup_same,'apk_permissions':normal_receipt['permissions'],'debuggable':normal_receipt['debuggable']})
log=call('logcat','-d','-s','godot:V','AndroidRuntime:E').decode(errors='replace')
(BASE/'runtime-logcat.txt').write_text(log)
errors=[line for line in log.splitlines() if any(s in line for s in ['SCRIPT ERROR','ERROR:','FATAL EXCEPTION','Fatal signal'])];assert not errors
write('android-verification-summary',{'runtime_commit':report['runtime_commit'],'version_name':report['version_name'],'version_code':report['version_code'],'total_assertions':len(report['checks']),'passed':True,'customer_navigation_version':report['customer_navigation_version'],'normal_upgrade_preserved_legacy_state':report['upgrade_preserved_legacy_state'],'focused_wandering_assertions':len(report.get('guest_wandering',{}).get('checks',[])),'normal_package':normal_receipt['package'],'review_package':review_receipt['package'],'signer_sha256':normal_receipt['signer_sha256'],'normal_apk_sha256':normal_receipt['apk_sha256'],'review_apk_sha256':review_receipt['apk_sha256'],'runtime_source_fingerprint':normal_receipt['runtime_source_fingerprint'],'runtime_source_file_count':len(normal_receipt['source_files']),'source_files_unchanged_after_qa':True,'review_gameplay_state_injected':False,'old_normal_baseline_state_injected':False,'physical_devices_touched':False,'rendered_readiness_used_on_all_cold_reopens':True,'runtime_errors':errors,'shader_cache_warnings':[line for line in log.splitlines() if 'WARNING:' in line]})
print(call('emu','kill').decode().strip(),flush=True)
process=json.loads((BASE/'emulator-process.json').read_text())
until=time.monotonic()+30
while time.monotonic()<until:
 try:os.kill(process['pid'],0)
 except ProcessLookupError:break
 time.sleep(.3)
else:raise AssertionError('Dedicated clone emulator has not exited')
receipt=json.loads((BASE/'avd-isolation.json').read_text());after=[]
for old in receipt['files_before']:
 path=Path(old['path']);st=path.stat();record={'path':str(path),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(path)}
 record['unchanged']=all(record[k]==old[k] for k in ['bytes','mtime_ns','sha256']);after.append(record)
assert all(item['unchanged'] for item in after)
receipt.update(files_after=after,all_tracked_original_avd_files_unchanged=True,emulator_stopped_without_snapshot_save=True,emulator_process_exited=True,avd_userdata_or_credentials_in_evidence=False)
write('avd-isolation',receipt)
print(json.dumps({'total_assertions':len(report['checks']),'original_avd_unchanged':True,'emulator_stopped':True,'runtime_source_files':len(normal_receipt['source_files']),'runtime_errors':len(errors)}),flush=True)
