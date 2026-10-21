"""Actual UI-only route closure, wandering, reopen and route restoration after the main55 checks."""
import sys,time,json,math
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-entrance-review')
from qa_common import *
from touch_geometry import *
from sprite_pixels import visible_point
from render_readiness import rendered
report=json.loads((BASE/'android-editor-verification.json').read_text());assert report['version_code']==47 and len(report['checks'])==55
assert installed_hash(REVIEW)==report['review_apk_sha256']
focus={'checks':[],'state_injected':False,'runtime_backdoor':False,'route_wall_row':3,'gate_tile':[4,3]}
def check(value,label):
 assert value,label
 focus['checks'].append(label);report['checks'].append(label);write('guest-wandering-verification-progress',focus);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
def snap(label):
 raw,d=save(REVIEW,label);screen(label);return raw,d
def customer(d,identity):return next((c for c in d['state']['customers'] if c['id']==identity),{})
def dist(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def visit(c):
 fields=['id','phase','seat_id','meal_dish','meal_duration','meal_elapsed','meal_fullness','fullness','appetite_target','first_dish_received','visit_legacy','departure_reason']
 return {key:c[key] for key in fields if key in c}
def row_clear(d):return all(math.hypot(x-c['x'],3-c['y'])>=.65 for x in range(7) for c in d['state']['customers'])
def free_floor(d,c):
 floor=d['configuration']['floor']
 return 0<=c['x']<floor['columns'] and 0<=c['y']<floor['rows'] and all(math.hypot(o['x']-c['x'],o['y']-c['y'])>=.49 for o in d['state']['objects'])
launch(REVIEW);rendered(REVIEW,'W00-live-before-route-fixture',edit=False);tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
# A generous real pan reaches the bounded left edge. All later source/drop
# coordinates use the actual saved camera rather than requiring exact zero.
if d['state']['camera']['x']>.05:
 swipe(pixel((220.,350.)),pixel((520.,350.)),ms=650);_,d=save(REVIEW,'W00-camera-normalized')
for attempt in range(12):
 if row_clear(d):break
 tap(*LIVE);wait_save(REVIEW,lambda d:d['state']['mode']=='live');time.sleep(.8)
 tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
else:raise AssertionError('No real paused frame had a guest-clear row3 for the UI-only fixture')
if d['state']['editor']['layer']!='layout':tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout')
if not d['state']['editor']['tray_open']:tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['tray_open'])
if d['state']['editor']['page']!=0:tap(*page(d,next=False));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['page']==0)
_,d=rendered(REVIEW,'W00-edit-before-wall');before=deepcopy(d);coins=d['state']['coins'];belt_stock=stock(d,'belt-tile')['count'];plant_stock=stock(d,'plant-angular')['count'];assert belt_stock>=6 and plant_stock>=1
assert not any(o['y']==3 and 0<=o['x']<7 for o in d['state']['objects'])
seated={c['id']:deepcopy(c) for c in d['state']['customers'] if c['phase'] in ['waiting','eating']};assert seated,'Real scene must contain seated guests for the preservation proof'
placed=[]
for x in [0,1,2,3,5,6]:
 count=stock(d,'belt-tile')['count'];tap(*card(d,0));tap(*cell(d,x,3))
 _,d=wait_save(REVIEW,lambda d:stock(d,'belt-tile')['count']==count-1);identity=d['state']['editor']['selected_id'];assert obj(d,identity).get('x')==x and obj(d,identity).get('y')==3;placed.append(identity)
# Final non-seat gate closes the only gap while remaining returnable later.
tap(*card(d,2));tap(*cell(d,4,3));_,d=wait_save(REVIEW,lambda d:stock(d,'plant-angular')['count']==plant_stock-1);gate=d['state']['editor']['selected_id'];assert obj(d,gate).get('art_id')=='plant-angular'
check(all(any(o['x']==x and o['y']==3 for o in d['state']['objects']) for x in range(7)),'Actual inventory drops fill row3 and the final empty-tile plant gate is accepted despite disconnecting the guest route')
check(d['state']['coins']==coins and stock(d,'belt-tile')['count']==belt_stock-6 and stock(d,'plant-angular')['count']==plant_stock-1,'Route closure consumes only the seven owned supplies without a purchase or coin change')
check(all(same(c,customer(d,identity)) for identity,c in seated.items()),'Seated guests retain their complete seated meal and visit state while the layout closes their route')
snap('W01-route-closed');focus.update(gate_id=gate,barrier_ids=placed+[gate],seated_customer_ids=list(seated),closure_elapsed=d['state']['elapsed'])
tap(*LIVE);print('Waiting for a real walking or leaving guest to need the blocked route...',flush=True)
_,d=wait_save(REVIEW,lambda d:any(c.get('navigation_mode')=='wander' and c['phase'] in ['walking','leaving'] and c.get('visual_phase')=='walk' and free_floor(d,c) for c in d['state']['customers']),timeout=120)
wander=next(c for c in d['state']['customers'] if c.get('navigation_mode')=='wander' and c['phase'] in ['walking','leaving'] and c.get('visual_phase')=='walk' and free_floor(d,c));identity=wander['id'];first=deepcopy(wander);elapsed=d['state']['elapsed']
check(wander.get('visual_phase')=='walk' and free_floor(d,wander),'An unreachable walking or leaving guest enters wander mode on free floor with the existing walk animation')
snap('W02-guest-wandering')
_,d=wait_save(REVIEW,lambda d:customer(d,identity).get('navigation_mode')=='wander' and dist(customer(d,identity),first)>.3 and d['state']['elapsed']>elapsed+.5,timeout=30)
moved=customer(d,identity)
check(free_floor(d,moved) and dist(first,moved)>.3,'The same blocked guest visibly moves across free floor instead of remaining stuck or disappearing')
check(same(visit(first),visit(moved)),'Wandering preserves the guest identity, assigned goal, departure phase and meal/visit state')
check(moved['wander_elapsed']>first['wander_elapsed'] and abs((moved['wander_elapsed']-first['wander_elapsed'])-(d['state']['elapsed']-elapsed))<.11,'The persisted scared-bubble clock advances with the same actual wandering simulation interval')
snap('W03-wander-moved');tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit');_,paused=rendered(REVIEW,'W04-wander-paused');assert customer(paused,identity)['navigation_mode']=='wander'
raw,paused=home(REVIEW,'W04-wander-home-save');time.sleep(1)
check(data(REVIEW)[0]==raw,'Edit and Home keep the wandering save byte-stable including the scared-bubble clock, navigation, service and RNG')
call('shell','am','force-stop',REVIEW);time.sleep(.5)
check(data(REVIEW)[0]==raw,'Force-stop preserves the saved wandering position, origin, cursor and retry clock')
launch(REVIEW);_,reopened=rendered(REVIEW,'W05-wander-cold-reopened')
check(same(paused,reopened),'Cold reopen restores every paused field including fractional wandering route bookkeeping and the guest visit')
old_guest=deepcopy(customer(reopened,identity));old_elapsed=reopened['state']['elapsed'];tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:customer(d,identity).get('navigation_mode')=='wander' and dist(customer(d,identity),old_guest)>.2 and d['state']['elapsed']>old_elapsed,timeout=30)
check(same(visit(old_guest),visit(customer(d,identity))) and free_floor(d,customer(d,identity)) and customer(d,identity)['wander_elapsed']>old_guest['wander_elapsed'],'Live resumes the restored wandering movement with the same guest and visit')
snap('W06-wander-resumed');tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit');count=stock(d,'plant-angular')['count'];coins=d['state']['coins']
tap(*visible_point(d,gate,art='plant-angular',label='W07-gate-select'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']==gate)
tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,gate))
check(stock(d,'plant-angular')['count']==count+1 and d['state']['coins']==coins,'Returning the plant gate restores the route and owned stock without altering coins')
snap('W07-route-reopened');tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:not customer(d,identity) or customer(d,identity).get('navigation_mode')=='goal',timeout=30)
recovered=customer(d,identity)
check(not recovered or recovered.get('seat_id')==first['seat_id'],'The same wandering guest automatically resumes its goal route or completes departure when the layout is reopened')
snap('W08-goal-route-restored');focus.update(customer_id=identity,initial_wander_phase=first['phase'],initial_goal_seat_id=first['seat_id'],first_wander_position={'x':first['x'],'y':first['y']},moved_position={'x':moved['x'],'y':moved['y']},restored_navigation_mode=recovered.get('navigation_mode','departed'),state_injected=False)
home(REVIEW,'review-final-after-wandering')
check(data(NORMAL)[0]==(BASE/'normal-v47-migrated.json').read_bytes() and data(NORMAL,'session.backup.json')[0]==(BASE/'normal-v47-before-review-backup.json').read_bytes(),'The complete route-block/wander/reopen/unblock proof leaves both normal app saves untouched')
log=call('logcat','-d','-s','godot:V','AndroidRuntime:E').decode(errors='replace');errors=[line for line in log.splitlines() if any(s in line for s in ['SCRIPT ERROR','ERROR:','FATAL EXCEPTION','Fatal signal'])]
check(not errors,'No app runtime error or crash occurs during the actual blocked-route wandering proof')
focus.update(passed=True,combined_assertion_count=len(report['checks']));report['guest_wandering']=focus;report['runtime_errors']=errors
write('guest-wandering-verification',focus);write('android-editor-verification',report);write('android-editor-verification-progress',report)
print(json.dumps({'focused_assertions':len(focus['checks']),'combined_assertions':len(report['checks']),'passed':True}),flush=True)
