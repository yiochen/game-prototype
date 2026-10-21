"""Real input proof: unadmitted guests wait puzzled, pause/reopen, leave or claim a newly usable seat."""
import sys,time,json,math
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-entrance-review')
from qa_common import *
from touch_geometry import *
from sprite_pixels import visible_point
from render_readiness import rendered
report=json.loads((BASE/'android-editor-verification.json').read_text())
assert report['version_code']==47 and report.get('guest_wandering',{}).get('passed')
assert installed_hash(REVIEW)==report['review_apk_sha256']
focus={'checks':[],'state_injected':False,'runtime_backdoor':False,'wait_seconds':4.0,'arrival_trace':[]}
def check(value,label):
 assert value,label
 focus['checks'].append(label);report['checks'].append(label)
 write('entrance-wait-verification-progress',focus);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
def customer(d,identity):return next((c for c in d['state']['customers'] if c['id']==identity),{})
def snap(label):
 raw,d=save(REVIEW,label);screen(label);return raw,d
def gate_clear(d):return all(math.hypot(4-c['x'],3-c['y'])>=.65 for c in d['state']['customers'])
def ensure_layout(d):
 if d['state']['editor']['layer']!='layout':tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout')
 if not d['state']['editor']['tray_open']:tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['tray_open'])
 if d['state']['editor']['page']!=0:tap(*page(d,next=False));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['page']==0)
 return d

def pause_fresh_waiter(label):
 deadline=time.monotonic()+80
 while time.monotonic()<deadline:
  _,d=data(REVIEW)
  ready=next((c for c in d['state']['customers'] if c['phase']=='entrance_wait' and c['entrance_wait_elapsed']<1.5),None)
  if ready:
   identity=ready['id'];tap(*EDIT);_,paused=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
   c=customer(paused,identity)
   if c.get('phase')=='entrance_wait' and c['entrance_wait_elapsed']<2.5:
    save(REVIEW,label);screen(label);return paused,identity
   tap(*LIVE)
  time.sleep(.12)
 raise AssertionError('No fresh real arrival reached entrance_wait in the live closed-route scene')

launch(REVIEW);rendered(REVIEW,'E00-live-before-entrance-fixture',edit=False);tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
if d['state']['camera']['x']>.05:swipe(pixel((220.,350.)),pixel((520.,350.)),ms=650);_,d=data(REVIEW)
for attempt in range(20):
 if gate_clear(d):break
 tap(*LIVE);time.sleep(.35);tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
else:raise AssertionError('Gate cell remained occupied by a guest; preserve direct-overlap protection')
d=ensure_layout(d)
assert all(any(o['x']==x and o['y']==3 and o['kind']=='belt' for o in d['state']['objects']) for x in [0,1,2,3,5,6])
count=stock(d,'plant-angular')['count'];coins=d['state']['coins']
tap(*card(d,2));tap(*cell(d,4,3));_,d=wait_save(REVIEW,lambda d:stock(d,'plant-angular')['count']==count-1)
gate=d['state']['editor']['selected_id'];assert obj(d,gate).get('x')==4 and obj(d,gate).get('y')==3
# Tap a fixed wall prop to clear the context capsule so the entrance bubble is visible.
tap(*cell(d,6,0));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']=='')
check(d['state']['coins']==coins and all(any(o['x']==x and o['y']==3 for o in d['state']['objects']) for x in range(7)),'Real card and world taps close the route again without buying supplies or touching the entrance')
snap('E00-route-closed-for-arrivals');tap(*LIVE)
paused,identity=pause_fresh_waiter('E01-puzzled-entrance-paused');c=customer(paused,identity);entrance=paused['configuration']['floor']['entrance'];clock=c['entrance_wait_elapsed']
check(paused.get('customer_admission_version')==1 and paused['configuration']['customers']['entrance_wait_seconds']==4.0,'Actual review saves use admission version1 and the four-second entrance deadline')
check(c['phase']=='entrance_wait' and c['seat_id']=='' and c['preferred_recipe_id']=='' and c['visual_phase']=='stand' and c['navigation_mode']=='goal' and c['wander_elapsed']==0 and same({'x':c['x'],'y':c['y']},entrance),'The new unseated arrival waits standing at the entrance with no assignment or wandering')
check(0<clock<4 and c['visual_elapsed']==0 and c['preference_elapsed']==0 and c['waiting_elapsed']==0 and c['meal_dish'] is None,'Puzzled feedback advances only its entrance wait clock while preference, body and meal clocks stay neutral')
raw,_=save(REVIEW,'E02-puzzled-before-pause');time.sleep(1.2)
check(data(REVIEW)[0]==raw,'Edit freezes the complete puzzled arrival save, including its four-second deadline, feedback clock and RNG')
raw,paused=home(REVIEW,'E02-puzzled-home-save');time.sleep(1)
check(data(REVIEW)[0]==raw,'Home preserves the waiting arrival and all paused clocks byte for byte')
call('shell','am','force-stop',REVIEW);time.sleep(.4)
check(data(REVIEW)[0]==raw,'Force-stop keeps the exact saved entrance-wait deadline and visitor identity')
launch(REVIEW);_,reopened=rendered(REVIEW,'E03-puzzled-cold-reopened')
check(same(paused,reopened) and customer(reopened,identity)['entrance_wait_elapsed']==clock,'Rendered cold reopen restores the same puzzled visitor and every paused field without consuming wait time')
start=deepcopy(reopened);start_elapsed=start['state']['elapsed'];tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:customer(d,identity).get('phase')=='entrance_wait' and customer(d,identity)['entrance_wait_elapsed']>clock+.4,timeout=10)
check(customer(d,identity)['navigation_mode']=='goal' and customer(d,identity)['wander_elapsed']==0,'Live resumes the same entrance wait without changing the arrival into a wandering guest')
snap('E04-puzzled-live-resumed')
trace=[];deadline=time.monotonic()+12
while time.monotonic()<deadline:
 _,d=data(REVIEW);visitor=customer(d,identity)
 trace.append({'elapsed':d['state']['elapsed'],'present':bool(visitor),'phase':visitor.get('phase'),'navigation_mode':visitor.get('navigation_mode'),'entrance_wait_elapsed':visitor.get('entrance_wait_elapsed')})
 if not visitor:break
 assert visitor['phase']=='entrance_wait' and visitor['navigation_mode']=='goal' and visitor['wander_elapsed']==0,'Unadmitted guest changed to a walking or wandering state'
 time.sleep(.12)
else:raise AssertionError('Unseated arrival did not leave after its four simulation seconds')
spent=d['state']['elapsed']-start_elapsed;remaining=4-clock
check(remaining-.11<=spent<=remaining+.8,'The same unavailable-seat arrival leaves at its remaining four-second simulation deadline after resume')
check(all(not row['present'] or (row['phase']=='entrance_wait' and row['navigation_mode']=='goal') for row in trace),'Every observed pre-departure frame keeps the unadmitted arrival at the door and never in wandering mode')
focus.update(first_arrival_id=identity,paused_entrance_wait_elapsed=clock,remaining_simulation_wait=remaining,observed_simulation_until_departure=spent,arrival_trace=trace)
snap('E05-unavailable-arrival-departed')
# A second real arrival can keep its identity and claim a newly usable seat.
paused,second=pause_fresh_waiter('E06-second-puzzled-arrival');old=deepcopy(customer(paused,second));d=ensure_layout(paused)
# Add a spare stool below the closed route. A seat adjacent to an active belt
# becomes reachable when the plant gate is returned; do not delete a busy seat.
candidates=[(1,5),(3,5),(2,8),(4,8)]
choice=next(((x,y) for x,y in candidates if not any(o['x']==x and o['y']==y for o in d['state']['objects']) and all(math.hypot(x-c['x'],y-c['y'])>=.65 for c in d['state']['customers'])),None)
assert choice,'No free lower-room seat fixture tile without a guest overlap'
seat_stock=stock(d,'stool-plain')['count'];tap(*card(d,1));tap(*cell(d,*choice));_,d=wait_save(REVIEW,lambda d:stock(d,'stool-plain')['count']==seat_stock-1);added_seat=d['state']['editor']['selected_id']
check(obj(d,added_seat).get('kind')=='seat' and same(customer(d,second),old),'A real spare stool placement preserves the waiting arrival and its exact paused feedback clock')
tap(*visible_point(d,gate,art='plant-angular',label='E07-gate-select'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']==gate)
plant_stock=stock(d,'plant-angular')['count'];tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,gate));tap(*cell(d,6,0));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']=='')
check(stock(d,'plant-angular')['count']==plant_stock+1 and same(customer(d,second),old),'Returning the real plant gate makes seating reachable while preserving the same paused entrance visitor')
snap('E07-seat-route-opened-during-wait');tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:customer(d,second).get('phase') in ['walking','waiting','eating'],timeout=10);assigned=deepcopy(customer(d,second))
check(assigned['seat_id']!='' and assigned['navigation_mode']=='goal' and assigned['wander_elapsed']==0 and assigned['entrance_wait_elapsed']==0 and assigned['appetite_target']==old['appetite_target'] and assigned['appearance']==old['appearance'],'The same puzzled arrival claims a newly usable seat before its deadline without rerolling appearance or appetite')
check(assigned['preferred_recipe_id'] in d['configuration']['recipes'] and assigned['path'] and assigned['phase']=='walking','Admission starts a valid goal route and meal preference only after a usable seat exists')
snap('E08-same-arrival-assigned');_,d=wait_save(REVIEW,lambda d:customer(d,second).get('phase') in ['waiting','eating'],timeout=40)
check(customer(d,second)['seat_id']==assigned['seat_id'] and customer(d,second)['navigation_mode']=='goal','The admitted visitor reaches the same assigned seat instead of departing or wandering')
snap('E09-same-arrival-seated');focus.update(second_arrival_id=second,second_paused_entrance_wait_elapsed=old['entrance_wait_elapsed'],added_seat_id=added_seat,added_seat_tile=list(choice),assigned_seat_id=assigned['seat_id'],same_arrival_reached_seat=True)
home(REVIEW,'review-final-after-entrance-wait')
check(data(NORMAL)[0]==(BASE/'normal-v47-migrated.json').read_bytes() and data(NORMAL,'session.backup.json')[0]==(BASE/'normal-v47-before-review-backup.json').read_bytes(),'All entrance waiting, lifecycle and seating recovery inputs leave both normal app saves unchanged')
log=call('logcat','-d','-s','godot:V','AndroidRuntime:E').decode(errors='replace');errors=[line for line in log.splitlines() if any(s in line for s in ['SCRIPT ERROR','ERROR:','FATAL EXCEPTION','Fatal signal'])]
check(not errors,'No app error or crash occurs during actual puzzled waiting, deadline departure and same-visitor seating recovery')
focus.update(passed=True,combined_assertion_count=len(report['checks']));report['entrance_wait']=focus;report['runtime_errors']=errors
write('entrance-wait-verification',focus);write('android-editor-verification',report);write('android-editor-verification-progress',report)
print(json.dumps({'focused_assertions':len(focus['checks']),'combined_assertions':len(report['checks']),'passed':True}),flush=True)
