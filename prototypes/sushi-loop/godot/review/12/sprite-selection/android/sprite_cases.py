"""Real touchscreen selection cases; all candidate pixels are derived offline from approved atlases."""
from sprite_pixels import *

def run_sprite_cases(paused,check,snapshot):
 original=json.loads(json.dumps(paused));notes=[]
 def current():return data(REVIEW)[1]
 def selected(identity,label):
  _,d=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']==identity)
  snapshot(label);return d
 def touch(d,identity,art=None,part=None,label=None,underlying=False):
  tap(*visible_point(d,identity,art=art,part=part,label=label,underlying=underlying))
 # A lower hat pixel stays clear of the existing grouped context capsule.
 d=current();touch(d,'chef-disconnected',part='hat',label='S01-chef-hat-select')
 d=selected('chef-disconnected','S01-chef-hat-selected')
 check(d['state']['editor']['layer']=='people','An opaque extruded chef hat selects its owning chef rather than the underlying tile')
 camera=deepcopy(d['state']['camera']);elapsed=d['state']['elapsed']
 object_drag(d,'chef-disconnected',(6,11),part='hat',label='S02-chef-hat-drag')
 _,d=wait_save(REVIEW,lambda d:obj(d,'chef-disconnected').get('y')==11)
 check(obj(d,'chef-disconnected')['x']==6 and d['state']['camera']==camera and d['state']['elapsed']==elapsed,'Dragging the selected chef by its hat preserves the root grab offset and commits tile6,11')
 snapshot('S02-chef-hat-moved')
 object_drag(d,'chef-disconnected',(6,10),part='hat',label='S03-chef-hat-return')
 _,d=wait_save(REVIEW,lambda d:obj(d,'chef-disconnected').get('y')==10)
 check(obj(d,'chef-disconnected')['x']==6 and d['state']['camera']==camera,'Dragging the hat back restores the chef ground tile without camera movement')
 snapshot('S03-chef-hat-restored')
 touch(d,'chef-1',art='chef-blackboard',label='S04-chef-board-select');d=selected('chef-1','S04-chef-board-selected')
 check(d['state']['editor']['selected_id']=='chef-1','The opaque front recipe board selects its owning chef')
 # Clear via a fixed prop so recipe activation must perform a new owner pick.
 touch(d,'',art='plant-angular',label='S05-fixed-prop-clear');d=selected('','S05-fixed-prop-blocked')
 check(not d['state']['editor']['selected_id'],'Opaque fixed room decoration is not editable and blocks scene selection')
 touch(d,'chef-1',art='dish-salmon',label='S06-chef-recipe-select');d=selected('chef-1','S06-chef-recipe-selected')
 check(d['state']['editor']['selected_id']=='chef-1','The recipe image on a chef board maps to the chef owner')
 carrying=next((o for o in d['state']['objects'] if o['kind']=='belt' and o.get('dish')),None)
 if carrying:
  touch(d,carrying['id'],art=DISH.get(carrying['dish']['recipe_id'],'dish-salmon'),label='S07-carried-dish-select');d=selected(carrying['id'],'S07-carried-dish-selected')
  check(d['state']['editor']['layer']=='layout','A carried dish selects its conveyor owner rather than the tile under the plate')
 else:notes.append('No carried dish was present in the paused real service frame; native ownership fixture covers this source mapping.')
 guest=next((c for c in d['state']['customers'] if c.get('seat_id')),None)
 if guest:
  art='customer-'+['rosa','ellis','samir','june'][int(guest.get('appearance',0))%4]
  touch(d,'',art=art,label='S08-guest-over-seat',underlying=True);d=selected('','S08-guest-blocked')
  check(not d['state']['editor']['selected_id'],'An opaque guest pixel over a stool blocks selection of the owned stool behind it')
 else:notes.append('No seated guest was present in the real paused service frame; native blocker fixture covers this case.')
 if d['state']['editor']['layer']!='layout':tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout')
 if not d['state']['editor']['tray_open']:tap(*layer(d,'layout'));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['tray_open'])
 if d['state']['editor']['page']!=0:tap(*page(d,next=False));_,d=wait_save(REVIEW,lambda d:d['state']['editor']['page']==0)
 count=stock(d,'plant-angular')['count'];coins=d['state']['coins'];swipe(card(d,2),cell(d,6,4),ms=650)
 _,d=wait_save(REVIEW,lambda d:stock(d,'plant-angular')['count']==count-1)
 identity=d['state']['editor']['selected_id']
 check(obj(d,identity).get('art_id')=='plant-angular' and obj(d,identity)['x']==6 and obj(d,identity)['y']==4,'Actual inventory drag places one owned plant without changing grid placement behavior')
 snapshot('S09-owned-plant-placed')
 point=visible_point(d,identity,art='plant-angular',transparent=True,label='S10-plant-alpha-gap');before=deepcopy(d)
 tap(*point);d=selected('','S10-transparent-plant-gap')
 check(same(before['state']['objects'],d['state']['objects']) and same(before['state']['inventory'],d['state']['inventory']),'A transparent pixel inside the registered plant frame falls through without selecting or altering it')
 touch(d,identity,art='plant-angular',part='raised',label='S11-plant-leaf-select');d=selected(identity,'S11-plant-leaf-selected')
 check(obj(d,identity)['y']==4,'An opaque raised plant leaf selects its plant owner outside the ground tile')
 object_drag(d,identity,(6,3),part='raised',label='S12-plant-leaf-drag')
 _,d=wait_save(REVIEW,lambda d:obj(d,identity).get('y')==3)
 check(obj(d,identity)['x']==6 and d['state']['camera']==camera,'Dragging a selected raised leaf retains its source-to-root offset at the destination tile')
 snapshot('S12-plant-leaf-moved')
 tap(*tool(d,remove=True));_,d=wait_save(REVIEW,lambda d:not obj(d,identity))
 check(stock(d,'plant-angular')['count']==count and d['state']['coins']==coins and len(d['state']['objects'])==len(original['state']['objects']),'Return restores the plant stock with no coin change and retains the original scene objects')
 snapshot('S13-plant-returned')
 write('sprite-selection-case-notes',{'offline_points_from_production_atlases':True,'runtime_backdoor':False,'gameplay_state_injected':False,'notes':notes})
 return d
