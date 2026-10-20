"""One real Live→Edit source-owner case for the plate absent from the first paused frame."""
import sys,json,time
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-sprite-review')
from qa_common import *
from touch_geometry import *
from sprite_pixels import *
from render_readiness import rendered
report=json.loads((BASE/'android-editor-verification.json').read_text());assert len(report['checks'])==68
launch(REVIEW);rendered(REVIEW,'D00-live-before-dish-case',edit=False)
tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
rendered(REVIEW,'D00-edit-before-dish-case')
# The regression pan remains proven in its historical states. Restore the
# camera with a normal gesture so left-hand conveyor plates are visible here.
if d['state']['camera']['x']>0:
 shift=d['state']['camera']['x']*pitch(d);swipe(pixel((220.,350.)),pixel((220.+shift,350.)),ms=650)
 _,d=wait_save(REVIEW,lambda d:abs(d['state']['camera']['x'])<.000001)
attempts=[];candidate=None
for attempt in range(12):
 _,d=save(REVIEW,'D01-paused-source-attempt-'+str(attempt))
 attempts.append({'attempt':attempt,'elapsed':d['state']['elapsed'],'carried_dish_owners':[o['id'] for o in d['state']['objects'] if o['kind']=='belt' and o.get('dish')]})
 for o in d['state']['objects']:
  if o['kind']!='belt' or not o.get('dish'):continue
  try:
   point=visible_point(d,o['id'],art=DISH.get(o['dish']['recipe_id'],'dish-salmon'),label='D01-carried-dish-select')
   candidate=(o['id'],point);break
  except AssertionError:continue
 if candidate:break
 tap(*LIVE);wait_save(REVIEW,lambda d:d['state']['mode']=='live');time.sleep(.6+.2*(attempt%3))
 tap(*EDIT);_,d=wait_save(REVIEW,lambda d:d['state']['mode']=='edit')
 rendered(REVIEW,'D01-source-frame-'+str(attempt))
assert candidate,'No visible real carried dish appeared during the bounded Live/Edit service checks'
identity,point=candidate;before=deepcopy(d);tap(*point)
_,after=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']==identity)
expected=deepcopy(before);expected['state']['editor']['selected_id']=identity;expected['state']['editor']['layer']='layout';expected['state']['editor']['page']=expected['state']['editor']['pages']['layout']
assert same(expected,after),'Plate selection changed more than the expected editor owner selection'
label='A carried dish selects its conveyor owner rather than the tile under the plate'
report['checks'].append(label)
report['continuations']=[{'kind':'leaf endpoint calibration','note':'Initial upward endpoint hit the existing context capsule and was correctly rejected. Unchanged-state assertion plus clear downward endpoint passed.','log':'android-touch-continuation.log'},{'kind':'carried dish source','note':'The initial6.7-second paused frame had no plate; this real Live→Edit continuation covered the source without state injection.','log':'android-carried-dish.log'}]
write('android-editor-verification',report);write('android-editor-verification-progress',report)
raw,after=save(REVIEW,'D02-carried-dish-selected');screen('D02-carried-dish-selected')
write('carried-dish-continuation',{'passed':True,'assertions':[label],'combined_assertion_count':len(report['checks']),'owner':identity,'attempts':attempts,'before_elapsed':before['state']['elapsed'],'after_elapsed':after['state']['elapsed'],'source_point_proof':'D01-carried-dish-select-source-point.json','gameplay_state_injected':False,'runtime_backdoor':False})
assert data(NORMAL)[0]==(BASE/'normal-v45-migrated.json').read_bytes() and data(NORMAL,'session.backup.json')[0]==(BASE/'normal-v45-before-review-backup.json').read_bytes()
home(REVIEW,'review-final-after-source-continuation')
print('PASS: '+label,flush=True);print(json.dumps({'continuation_assertions':1,'combined_assertions':len(report['checks']),'passed':True}),flush=True)
