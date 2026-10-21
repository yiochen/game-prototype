"""Create the legacy walking/wander bug using only signed47 APK input; no state injection."""
import sys,time,json,math
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-exit-recovery')
from qa_common import *
from touch_geometry import *
from sprite_pixels import visible_point
from render_readiness import rendered
report=json.loads((BASE/'android-editor-verification.json').read_text());assert report['version_code']==48
focus={'checks':[],'state_injected':False,'runtime_backdoor':False,'wall_row':3,'gate_tile':[6,3]}
def check(value,label):
 assert value,label
 focus['checks'].append(label);report['checks'].append(label);write('legacy47-fixture-progress',focus);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
def customer(d,identity):return next((c for c in d['state']['customers'] if c['id']==identity),{})
def snap(label):raw,d=save(REVIEW,label);screen(label);return raw,d
def visit(c):return {k:v for k,v in c.items() if k not in ['navigation_mode','path','path_origin','path_index','navigation_retry_elapsed','wander_cursor']}
def row_clear(d):return all(math.hypot(x-c['x'],3-c['y'])>=.65 for x in range(7) for c in d['state']['customers'])
def ensure_layout(d):
 if d['state']['editor']['layer']!='layout':tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout')
 if not d['state']['editor']['tray_open']:tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['tray_open'])
 if d['state']['editor']['page']!=0:tap(*page(d,next=False));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['page']==0)
 return d
legacy=PROJECT/'build/sushi-loop-restaurant-editor-review-release-v0.4.7.apk';receipt=json.loads(legacy.with_suffix('.build.json').read_text());assert receipt['package']==REVIEW and receipt['version_code']==47 and sha(legacy)==receipt['apk_sha256']=='f8bf81d30c04307beff89b1853525a33759d35e773e579fe586f73d6d3702cb5'
assert package_absent(REVIEW);print(call('install',legacy,timeout=180).decode().strip(),flush=True);check(installed_hash(REVIEW)==receipt['apk_sha256'],'Fresh legacy review47 install matches the real signed prior APK')
call('logcat','-c');launch(REVIEW);rendered(REVIEW,'R00-legacy47-fresh-live',edit=False)
_,d=wait_save(REVIEW,lambda d:any(c['phase'] in ['waiting','eating'] and c['y']>3.5 for c in d['state']['customers']),timeout=45)
tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
for attempt in range(20):
 if row_clear(d):break
 tap(*LIVE);time.sleep(.3);tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
else:raise AssertionError('No clear row3 frame for fixture without guest overlap')
d=ensure_layout(d);_,d=snap('R00-legacy-before-wall');stock0=stock(d,'belt-tile')['count'];coins=d['state']['coins'];seated={c['id']:deepcopy(c) for c in d['state']['customers'] if c['phase'] in ['waiting','eating']};assert seated and stock0>=6
for x in range(6):
 count=stock(d,'belt-tile')['count'];tap(*card(d,0));tap(*cell(d,x,3));_,d=wait_save(REVIEW,lambda d:stock(d,'belt-tile')['count']==count-1);item=obj(d,d['state']['editor']['selected_id']);assert (item['x'],item['y'])==(x,3)
check(d['state']['coins']==coins and stock(d,'belt-tile')['count']==stock0-6 and all(same(c,customer(d,i)) for i,c in seated.items()),'Six real owned conveyor placements preserve coins and all paused seated guest dictionaries')
_,d=snap('R01-partial-wall-right-gap');existing={c['id'] for c in d['state']['customers']};tap(*LIVE)
# A right-side gap gives the new walker several upper-corridor cells before
# reaching the crossing, avoiding a timing-sensitive tap directly below the door.
end=time.monotonic()+75
while time.monotonic()<end:
 _,d=data(REVIEW);walker=next((c for c in d['state']['customers'] if c['id'] not in existing and c['phase']=='walking' and c['y']<=2.35 and c['x']<=4.75),None)
 if walker:
  identity=walker['id'];call('shell','input','tap',*map(round,EDIT));_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit');walker=customer(d,identity)
  if walker.get('phase')=='walking' and walker['y']<=2.5 and math.hypot(walker['x']-6,walker['y']-3)>=.8:break
  tap(*LIVE)
 time.sleep(.08)
else:raise AssertionError('No newly assigned upper-corridor walker for real legacy fixture')
walker_before=deepcopy(walker);plant_count=stock(d,'plant-angular')['count'];d=ensure_layout(d);tap(*card(d,2));tap(*cell(d,6,3));_,d=wait_save(REVIEW,lambda d:stock(d,'plant-angular')['count']==plant_count-1);gate=d['state']['editor']['selected_id'];assert (obj(d,gate)['x'],obj(d,gate)['y'])==(6,3)
check(customer(d,identity)['phase']=='walking' and same(visit(customer(d,identity)),visit(walker_before)),'Closing the final gate above an admitted walker preserves its paused phase, visit, position, animation and clocks')
tap(*cell(d,0,0));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']=='');snap('R02-legacy-seat-blocked-door-reachable');entrance=d['configuration']['floor']['entrance'];tap(*LIVE)
_,d=wait_save(REVIEW,lambda d:customer(d,identity).get('phase')=='walking' and customer(d,identity).get('navigation_mode')=='wander' and customer(d,identity).get('wander_elapsed',0)>=1.2 and math.hypot(customer(d,identity)['x']-entrance['x'],customer(d,identity)['y']-entrance['y'])>=1.4,timeout=60)
call('shell','input','tap',*map(round,EDIT));_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit');walker=customer(d,identity)
check(walker['phase']=='walking' and walker['navigation_mode']=='wander' and walker['wander_elapsed']>=1 and walker['departure_reason']=='' and walker['y']<3 and obj(d,walker['seat_id'])['y']>3 and d['configuration']['floor']['columns']==7 and all(any(o['x']==x and o['y']==3 for o in d['state']['objects']) for x in range(7)),'Real47 reproduces walking/wander with scared idle feedback above a complete seven-cell wall, its assigned seat below and entrance reachable above')
snap('R03-legacy47-walking-wander-paused');raw,d=home(REVIEW,'review47-walking-wander-before-update');backup,_=save(REVIEW,'review47-backup-before-update',backup=True);call('shell','am','force-stop',REVIEW)
check(data(REVIEW)[0]==raw and data(REVIEW,'session.backup.json')[0]==backup,'Legacy walking/wander primary and backup remain stable before48 installation')
focus.update(passed=True,legacy_customer_id=identity,legacy_seat_id=walker['seat_id'],legacy_guest=walker,gate_id=gate,inside_seated_ids=list(seated),legacy_review_apk_sha256=receipt['apk_sha256'],legacy_pause_elapsed=d['state']['elapsed'])
report['legacy47_fixture']=focus;write('legacy47-fixture',focus);write('android-editor-verification',report)
print(json.dumps({'legacy_fixture_assertions':len(focus['checks']),'combined_assertions':len(report['checks']),'passed':True}),flush=True)
