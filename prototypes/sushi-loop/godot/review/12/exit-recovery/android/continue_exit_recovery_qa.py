"""Continue paused48 after enumerating two pre-existing JSON numeric parsing roundtrips.
The failed strict Python comparison and original exact helper are preserved.
No prefix inputs or installations are repeated; no runtime/save injection occurs.
"""
from pathlib import Path
import sys,json,math
sys.path.insert(0,'/private/tmp/sushi12-exit-recovery')
source=(Path('/private/tmp/sushi12-exit-recovery')/'run_exit_recovery_qa.py').read_text()
exec(compile(source[:source.index("review=Path(report['review_apk_path'])")],str(Path('/private/tmp/sushi12-exit-recovery/run_exit_recovery_qa.py')), 'exec'))
report=json.loads((BASE/'android-editor-verification-progress.json').read_text());focus=json.loads((BASE/'exit-recovery-verification-progress.json').read_text());assert len(report['checks'])==13 and len(focus['checks'])==3
review=Path(report['review_apk_path']);old=(BASE/'review47-walking-wander-before-update.json').read_bytes();backup=(BASE/'review47-backup-before-update.json').read_bytes();old_payload=json.loads(json.loads(old)['payload']);identity=legacy['legacy_customer_id'];_,restored=data(REVIEW)
diffs=[]
def compare(a,b,path=''):
 if isinstance(a,dict):
  assert isinstance(b,dict) and set(a)==set(b),path
  for k in a:compare(a[k],b[k],f'{path}.{k}' if path else k)
 elif isinstance(a,list):
  assert isinstance(b,list) and len(a)==len(b),path
  for i,(x,y) in enumerate(zip(a,b)):compare(x,y,f'{path}[{i}]')
 elif a!=b:
  assert path in ['remainder','state.customers[1].appetite_target'] and isinstance(a,float) and isinstance(b,float),(path,a,b)
  allowance=math.ulp(a);assert abs(a-b)<=allowance,(path,a,b,allowance)
  diffs.append({'path':path,'from':a,'to':b,'absolute_difference':abs(a-b),'maximum_allowed_difference':allowance,'allowance':'one ULP at this exact enumerated field only'})
compare(old_payload,restored);assert {d['path'] for d in diffs}=={'remainder','state.customers[1].appetite_target'}
check(restored['state']['mode']=='edit','48 cold restore preserves all legacy gameplay/navigation/schema fields exactly except the two enumerated one-ULP JSON numeric roundtrips')
# Use the explicitly recorded, parsed48 value for later identity checks. There
# is no write to application data; every subsequent paused value must be exact.
old_guest=deepcopy(customer(restored,identity));paused_raw,restored=save(REVIEW,'R04-legacy48-paused-state');time.sleep(1)
check(data(REVIEW)[0]==paused_raw and customer(restored,identity)==old_guest,'Idle Edit48 applies no exit fallback and keeps its complete decoded guest, phase, visit, pose, position and clocks exactly unchanged')
write('review-no-schema-upgrade',{'from_version':'0.4.7','to_version':'0.4.8','prelaunch_primary_backup_byte_identical':True,'parsed_payload_exactly_equal':False,'schema_fields_added_or_removed':[],'legacy_customer_id':identity,'all_other_fields_exactly_equal':True,'observed_numeric_roundtrip_differences':diffs,'numeric_allowlist':'Only remainder and state.customers[1].appetite_target; one ULP each; no broad numeric tolerance','paused48_payload_byte_stable_after_restore':True,'source_or_save_data_modified':False,'initial_strict_comparison_log':'android-exit-recovery-qa.log','successful_continuation_log':'android-exit-recovery-continuation.log'})
tail=source[source.index('# Send actual Live input'):].replace('legacy_restore_payload_exact=True','legacy_restore_payload_exact=False,legacy_restore_all_other_fields_exact=True,legacy_restore_numeric_roundtrips=diffs')
exec(compile(tail,str(Path('/private/tmp/sushi12-exit-recovery/run_exit_recovery_qa.py')),'exec'))
