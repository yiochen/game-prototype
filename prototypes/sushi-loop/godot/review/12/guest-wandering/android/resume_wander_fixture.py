"""Return the observed off-target long-swipe piece, then continue via exact real card/world taps."""
from pathlib import Path
source=Path('/private/tmp/sushi12-wander-review/run_wander_qa.py').read_text()
exec(compile(source[:source.index('launch(REVIEW);')],'run_wander_qa.py [imports and proof helpers]','exec'))
original=json.loads(json.loads((BASE/'W00-edit-before-wall.json').read_text())['payload']);before=deepcopy(original);coins=before['state']['coins'];belt_stock=stock(before,'belt-tile')['count'];plant_stock=stock(before,'plant-angular')['count'];seated={c['id']:deepcopy(c) for c in before['state']['customers'] if c['phase'] in ['waiting','eating']}
_,d=data(REVIEW);bad=d['state']['editor']['selected_id'];assert obj(d,bad).get('kind')=='belt' and (obj(d,bad)['x'],obj(d,bad)['y'])==(6,4);assert d['state']['camera']=={'x':0.,'y':0.}
write('wall-placement-coordinate-calibration',{'classification':'The sixth automated long inventory swipe landed one row below the intended cell; caught before route closure','input':'adb input swipe 288 2163 972 768 650','expected_tile':[6,3],'observed_tile':[6,4],'observed_object_id':bad,'actual_saved_camera':d['state']['camera'],'first_five_tiles':[[0,3],[1,3],[2,3],[3,3],[5,3]],'raw_log':'android-wander-qa.log','continuation_log':'android-wander-continuation.log','recovery':'Return misplaced belt and use supported card-tap then world-tap placement; no state injection','production_source_changed':False})
tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,bad) and stock(d,'belt-tile')['count']==1)
tap(*card(d,0));tap(*cell(d,6,3));_,d=wait_save(REVIEW,lambda d:stock(d,'belt-tile')['count']==0);fixed=d['state']['editor']['selected_id'];assert (obj(d,fixed)['x'],obj(d,fixed)['y'])==(6,3),'Exact tapped belt target did not land at6,3'
placed=[o['id'] for o in d['state']['objects'] if o['kind']=='belt' and o['y']==3];assert len(placed)==6
snap('W00-six-belts-corrected');print('Fixture corrected through actual Return and card/world taps: all6 belts are on row3.',flush=True)
tail=source[source.index('# Final non-seat gate closes the only gap'):]
tail=tail.replace("swipe(card(d,2),cell(d,4,3),ms=650);","tap(*card(d,2));tap(*cell(d,4,3));")
exec(compile(tail,'run_wander_qa.py [route proof after coordinate correction]','exec'))
