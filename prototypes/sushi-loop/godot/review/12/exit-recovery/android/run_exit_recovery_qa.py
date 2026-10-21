"""Focused actual48 proof: preserve legacy Edit state, choose reachable exit, keep true traps, restore exit and seat priority."""
import sys,time,json,math
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-exit-recovery')
from qa_common import *
from touch_geometry import *
from sprite_pixels import visible_point
from render_readiness import rendered
report=json.loads((BASE/'android-editor-verification.json').read_text());legacy=report['legacy47_fixture'];assert legacy['passed'] and report['version_code']==48
focus={'checks':[],'state_injected':False,'runtime_backdoor':False,'legacy_live_trace':[]}
def check(value,label):
 assert value,label
 focus['checks'].append(label);report['checks'].append(label);write('exit-recovery-verification-progress',focus);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
def customer(d,identity):return next((c for c in d['state']['customers'] if c['id']==identity),{})
def snap(label):raw,d=save(REVIEW,label);screen(label);return raw,d
def dist(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def stable_visit(c):return {k:c.get(k) for k in ['id','phase','seat_id','departure_reason','meal_dish','meal_duration','meal_elapsed','meal_fullness','fullness','appetite_target','appearance','first_dish_received','visit_legacy']}
def free_floor(d,c):return all(math.hypot(o['x']-c['x'],o['y']-c['y'])>=.49 for o in d['state']['objects'])
review=Path(report['review_apk_path']);old=(BASE/'review47-walking-wander-before-update.json').read_bytes();backup=(BASE/'review47-backup-before-update.json').read_bytes();old_payload=json.loads(json.loads(old)['payload']);identity=legacy['legacy_customer_id'];old_guest=customer(old_payload,identity)
check(data(REVIEW)[0]==old and data(REVIEW,'session.backup.json')[0]==backup,'Real legacy47 walking/wander save matches its protected primary and backup before upgrade')
print(call('install','-r',review,timeout=180).decode().strip(),flush=True)
check(installed_hash(REVIEW)==report['review_apk_sha256'],'Installed review48 matches the exact signed release hash')
check(data(REVIEW)[0]==old and data(REVIEW,'session.backup.json')[0]==backup,'Review47→48 installation preserves both real legacy walking/wander save files byte for byte before launch')
launch(REVIEW);_,restored=rendered(REVIEW,'R04-legacy48-restored-paused')
# This legacy review fixture has already serialized its numbers under47. Require
# exact parsed equality here, including every field and schema marker.
check(old_payload==restored,'48 cold restore preserves the exact complete legacy walking/wander payload and schema while Edit remains paused')
paused_raw,restored=save(REVIEW,'R04-legacy48-paused-state');time.sleep(1)
check(data(REVIEW)[0]==paused_raw and customer(restored,identity)==old_guest,'Idle Edit48 neither applies exit fallback nor changes the old guest phase, visit, pose, position or clock')
write('review-no-schema-upgrade',{'from_version':'0.4.7','to_version':'0.4.8','prelaunch_primary_backup_byte_identical':True,'parsed_payload_exactly_equal':old_payload==restored,'schema_fields_added_or_removed':[],'legacy_customer_id':identity,'legacy_guest_exactly_equal':customer(restored,identity)==old_guest})
# Send actual Live input without the usual post-tap delay, so the short direct
# departure can be observed before the guest reaches the nearby entrance.
call('shell','input','tap',*map(round,LIVE));end=time.monotonic()+12;trace=[]
while time.monotonic()<end:
 _,d=data(REVIEW);c=customer(d,identity);trace.append({'elapsed':d['state']['elapsed'],'phase':c.get('phase'),'navigation_mode':c.get('navigation_mode'),'departure_reason':c.get('departure_reason'),'x':c.get('x'),'y':c.get('y'),'wander_elapsed':c.get('wander_elapsed')})
 if c.get('phase')=='leaving' and c.get('departure_reason')=='seat_unreachable':break
 assert c,'Legacy guest departed before its direct exit decision could be observed'
 time.sleep(.04)
else:raise AssertionError('Legacy walking/wander did not choose its reachable entrance after Live')
leaving=deepcopy(c)
check(c['navigation_mode']=='goal' and c['wander_elapsed']==0 and c['navigation_retry_elapsed']==0 and c['visual_phase']=='walk','Live converts the old blocked-seat walker directly to goal departure with seat_unreachable, clears scared clock and keeps walking pose')
check(c['seat_id']==old_guest['seat_id'] and all(c[k]==old_guest[k] for k in ['appearance','appetite_target','fullness','meal_dish','meal_elapsed','meal_fullness','first_dish_received','visit_legacy']),'Exit fallback keeps the same guest, assigned seat history and complete meal/visit identity without rerolling or reseating')
snap('R05-seat-unreachable-direct-exit');_,d=wait_save(REVIEW,lambda d:not customer(d,identity),timeout=25)
check(not customer(d,identity),'The legacy blocked-seat guest reaches the available entrance and leaves instead of continuing to wander')
snap('R06-legacy-walker-departed');focus.update(legacy_customer_id=identity,legacy_live_trace=trace,direct_exit_state=leaving,legacy_restore_payload_exact=True)
# Older seated guests below the full wall really cannot reach the entrance.
# Their existing satisfied/unfed departure stays a true trap rather than being
# discarded by the new blocked-seat fallback.
print('Waiting for an actual lower-room guest to finish its visit and need the blocked exit...',flush=True)
inside=set(legacy['inside_seated_ids'])
_,d=wait_save(REVIEW,lambda d:any(c['id'] in inside and c['phase']=='leaving' and c['navigation_mode']=='wander' and c['wander_elapsed']>=1 and c['y']>3.5 and free_floor(d,c) for c in d['state']['customers']),timeout=150)
trapped=next(c for c in d['state']['customers'] if c['id'] in inside and c['phase']=='leaving' and c['navigation_mode']=='wander' and c['wander_elapsed']>=1 and c['y']>3.5 and free_floor(d,c));trapped=deepcopy(trapped);tid=trapped['id'];t_elapsed=d['state']['elapsed']
check(trapped['departure_reason'] in ['satisfied','unfed'] and trapped['visual_phase']=='walk','An already-admitted lower-room guest with no entrance route keeps its real departure reason and scared wandering')
snap('R07-true-trap-still-wanders');_,d=wait_save(REVIEW,lambda d:customer(d,tid).get('navigation_mode')=='wander' and dist(customer(d,tid),trapped)>.3 and d['state']['elapsed']>t_elapsed+.4,timeout=30)
moved=deepcopy(customer(d,tid))
check(stable_visit(moved)==stable_visit(trapped) and moved['wander_elapsed']>trapped['wander_elapsed'] and free_floor(d,moved),'The true trapped guest continues moving on free floor with its original meal/visit and advancing scared clock')
snap('R08-trapped-moved');tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit');before=deepcopy(customer(d,tid));gate=legacy['gate_id'];count=stock(d,'plant-angular')['count'];coins=d['state']['coins']
tap(*visible_point(d,gate,art='plant-angular',label='R09-gate-select'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']==gate)
tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,gate))
check(stock(d,'plant-angular')['count']==count+1 and d['state']['coins']==coins and stable_visit(customer(d,tid))==stable_visit(before),'Returning the real plant gate restores its owned stock and entrance access without changing the paused guest visit or coins')
tap(*cell(d,0,0));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']=='');tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:not customer(d,tid) or customer(d,tid).get('navigation_mode')=='goal',timeout=15);recovered=customer(d,tid)
check(not recovered or (recovered['phase']=='leaving' and recovered['departure_reason']==trapped['departure_reason'] and recovered['wander_elapsed']==0),'The already-leaving guest resumes its original goal departure after gate opening and clears scared feedback')
snap('R09-trapped-exit-route-restored');_,d=wait_save(REVIEW,lambda d:not customer(d,tid),timeout=35)
check(not customer(d,tid),'The previously trapped leaving guest completes its original departure through the reopened entrance')
# With seats and entrance both reachable, a new admitted walker must prefer its
# assigned seat rather than taking the newly introduced exit fallback.
_,d=wait_save(REVIEW,lambda d:any(c['phase']=='walking' and c['navigation_mode']=='goal' and c['departure_reason']=='' and c['seat_id'] for c in d['state']['customers']),timeout=75)
seeking=deepcopy(next(c for c in d['state']['customers'] if c['phase']=='walking' and c['navigation_mode']=='goal' and c['departure_reason']=='' and c['seat_id']));sid=seeking['id']
check(seeking['wander_elapsed']==0 and seeking['seat_id']!='','A v48 walking guest with an available seat route prioritizes that assigned seat despite a reachable entrance')
snap('R10-reachable-seat-first');_,d=wait_save(REVIEW,lambda d:customer(d,sid).get('phase') in ['waiting','eating'],timeout=45);seated=customer(d,sid)
check(seated['seat_id']==seeking['seat_id'] and seated['departure_reason']=='' and seated['appearance']==seeking['appearance'] and seated['appetite_target']==seeking['appetite_target'],'The same goal walker reaches its assigned seat without a seat_unreachable exit or visit reroll')
snap('R11-seat-first-arrived');focus.update(trapped_customer_id=tid,trapped_departure_reason=trapped['departure_reason'],trapped_original_visit=stable_visit(trapped),trapped_moved_position={'x':moved['x'],'y':moved['y']},seat_first_customer_id=sid,seat_first_seat_id=seated['seat_id'])
home(REVIEW,'review-final-after-exit-recovery')
check(data(NORMAL)[0]==(BASE/'normal-v48-restored.json').read_bytes() and data(NORMAL,'session.backup.json')[0]==(BASE/'normal-v48-before-review-backup.json').read_bytes(),'All review47/48 real-input exit and seat-priority cases leave both normal48 app saves untouched')
log=call('logcat','-d','-s','godot:V','AndroidRuntime:E').decode(errors='replace');errors=[line for line in log.splitlines() if any(x in line for x in ['SCRIPT ERROR','ERROR:','FATAL EXCEPTION','Fatal signal'])]
check(not errors,'No app script error or Android crash occurs through legacy recovery, true wandering, restored departure or seat priority')
focus.update(passed=True,combined_assertion_count=len(report['checks']));report['exit_recovery']=focus;report['runtime_errors']=errors
write('exit-recovery-verification',focus);write('android-editor-verification',report);write('android-editor-verification-progress',report)
print(json.dumps({'exit_assertions':len(focus['checks']),'combined_assertions':len(report['checks']),'passed':True}),flush=True)
