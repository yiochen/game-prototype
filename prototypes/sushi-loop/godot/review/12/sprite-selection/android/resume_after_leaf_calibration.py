"""Continue after the initial upward leaf target was correctly blocked by the context capsule."""
import argparse,sys,time,json,hashlib,subprocess
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,'/private/tmp/sushi12-sprite-review')
from qa_common import *
from touch_geometry import *
from sprite_pixels import *
from render_readiness import rendered,hold,cancel_hold,held_background
args=SimpleNamespace(normal_apk=PROJECT/'build/sushi-loop-restaurant-editor-release-v0.4.5.apk',review_apk=PROJECT/'build/sushi-loop-restaurant-editor-review-release-v0.4.5.apk',runtime_commit=(BASE/'runtime-commit.txt').read_text().strip())
normal_receipt=json.loads(args.normal_apk.with_suffix('.build.json').read_text());review_receipt=json.loads(args.review_apk.with_suffix('.build.json').read_text())
report=json.loads((BASE/'android-editor-verification-progress.json').read_text())
def check(value,label):
 assert value,label
 report['checks'].append(label);write('android-editor-verification-progress',report);print('PASS:',label,flush=True)
def snapshot(label,image=True):
 raw,d=save(REVIEW,label)
 if image:screen(label)
 return raw,d
normal_before=(BASE/'normal-v45-migrated.json').read_bytes();normal_backup=(BASE/'normal-v45-before-review-backup.json').read_bytes();initial=json.loads(json.loads((BASE/'review-initial.json').read_text())['payload'])
before=json.loads(json.loads((BASE/'S11-plant-leaf-selected.json').read_text())['payload']);raw,d=data(REVIEW);identity=d['state']['editor']['selected_id'];assert obj(d,identity)['art_id']=='plant-angular' and obj(d,identity)['x']==6 and obj(d,identity)['y']==4
proof=json.loads((BASE/'S12-plant-leaf-drag-source-point.json').read_text());source=proof['screen_point'];base=cell(before,6,4);target=cell(before,6,3);endpoint=[target[i]+source[i]-base[i] for i in range(2)];logical=[v/SCALE for v in endpoint];t=tool(before);context=[t[0]/SCALE-82,t[1]/SCALE-64,304,148]
assert contains(context,logical)
check(same(before,d),'Leaf drag ending inside the context capsule is rejected with the complete paused state unchanged')
write('leaf-drag-coordinate-calibration',{'classification':'Initial QA destination intersected the existing native context capsule; expected input shielding, not app failure','original_start_screen':source,'original_end_screen':endpoint,'context_logical_bounds':context,'end_is_inside_context':True,'saved_state_unchanged':True,'raw_log':'android-touch-qa.log','successful_continuation_log':'android-touch-continuation.log','corrected_target_tile':[6,5]})
object_drag(d,identity,(6,5),part='raised',label='S12-plant-leaf-drag-clear-endpoint')
_,d=wait_save(REVIEW,lambda d:obj(d,identity).get('y')==5)
check(obj(d,identity)['x']==6 and d['state']['camera']==before['state']['camera'],'Dragging a selected raised leaf retains its source-to-root offset at the clear destination tile6,5')
snapshot('S12-plant-leaf-moved')
count=stock(before,'plant-angular')['count']+1;coins=before['state']['coins'];tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,identity))
check(stock(d,'plant-angular')['count']==count and d['state']['coins']==coins and len(d['state']['objects'])==len(initial['state']['objects']),'Return restores the plant stock with no coin change and retains the original scene objects')
snapshot('S13-plant-returned');write('sprite-selection-case-notes',{'offline_points_from_production_atlases':True,'runtime_backdoor':False,'gameplay_state_injected':False,'notes':['No carried dish was present in the initial paused6.7-second service frame; a separate real Live→Edit continuation will cover it.'],'coordinate_calibration':'See leaf-drag-coordinate-calibration.json; downward clear destination6,5 succeeded'})
paused=d
source=(BASE/'run_editor_qa.py').read_text();tail=source[source.index('# Use the deliberately disconnected stool; no customer owns it.'):]
exec(compile(tail,str(BASE/'run_editor_qa.py')+' [remaining regressions]','exec'))
