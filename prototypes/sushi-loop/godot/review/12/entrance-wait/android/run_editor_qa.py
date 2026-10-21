"""Run only after final runtime commit/build approval; actual adb touch inputs."""
import argparse,sys,time,json,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-entrance-review')
from qa_common import *
from touch_geometry import *
from sprite_pixels import visible_point,object_drag
from migration_compare import expected_admission_upgrade
from render_readiness import rendered,hold,cancel_hold,held_background
parser=argparse.ArgumentParser()
parser.add_argument('--normal-apk',type=Path,required=True)
parser.add_argument('--review-apk',type=Path,required=True)
parser.add_argument('--runtime-commit',required=True)
args=parser.parse_args()
normal_receipt=json.loads(args.normal_apk.with_suffix('.build.json').read_text())
review_receipt=json.loads(args.review_apk.with_suffix('.build.json').read_text())
assert normal_receipt['package']==NORMAL and review_receipt['package']==REVIEW
assert normal_receipt['version_code']==47 and review_receipt['version_code']==47
assert normal_receipt['version_name']=='0.4.7' and review_receipt['version_name']=='0.4.7'
assert normal_receipt['source_files']==review_receipt['source_files']
assert normal_receipt['signer_sha256']==review_receipt['signer_sha256']
assert sha(args.normal_apk)==normal_receipt['apk_sha256'] and sha(args.review_apk)==review_receipt['apk_sha256']
assert all(sha(PROJECT/name)==digest for name,digest in normal_receipt['source_files'].items()), 'Runtime changed after APK build'
report={'runtime_commit':args.runtime_commit,'emulator_serial':SERIAL,'input':'Actual adb input tap/swipe/keyevent, production offline release','physical_devices_touched':False,'checks':[]}
def check(value,label):
 assert value,label
 report['checks'].append(label)
 write('android-editor-verification-progress',report)
 print('PASS:',label,flush=True)
def snapshot(label,image=True):
 raw,d=save(REVIEW,label)
 if image:screen(label)
 return raw,d
# Preserve a real old production-app Edit state with an in-place signed upgrade.
v46=(BASE/'normal-v46-session-before-update.json').read_bytes()
v46_backup=(BASE/'normal-v46-backup-before-update.json').read_bytes()
check(data(NORMAL)[0]==v46 and data(NORMAL,'session.backup.json')[0]==v46_backup,'Existing v46 primary and backup match the protected paused baseline')
print(call('install','-r',args.normal_apk,timeout=180).decode().strip(),flush=True)
check(installed_hash(NORMAL)==normal_receipt['apk_sha256'],'Installed normal APK matches final release SHA256')
check(data(NORMAL)[0]==v46 and data(NORMAL,'session.backup.json')[0]==v46_backup,'Normal v46→v47 installation preserves both save files byte for byte before launch')
launch(NORMAL)
rendered(NORMAL,'normal-v47-upgraded-rendered')
normal_before,normal_data=home(NORMAL,'normal-v47-migrated')
normal_backup,_=save(NORMAL,'normal-v47-before-review-backup',backup=True)
call('shell','am','force-stop',NORMAL)
old=json.loads(json.loads(v46)['payload'])
write('normal-admission-migration',{'from_admission_version':old.get('customer_admission_version',0),'to_admission_version':normal_data.get('customer_admission_version'),'expected_legacy_state_preserved':same(expected_admission_upgrade(old),normal_data),'allowed_changes':['customer_admission_version=1','missing entrance_wait_seconds=4','per-guest entrance_wait_elapsed=0 and wander_elapsed=0'],'old_random_state':old['random_state'],'new_random_state':normal_data['random_state'],'old_remainder':old['remainder'],'new_remainder':normal_data['remainder'],'old_elapsed':old['state']['elapsed'],'new_elapsed':normal_data['state']['elapsed']})
check(same(expected_admission_upgrade(old),normal_data),'Normal v46→v47 preserves all legacy state while adding only neutral admission and feedback fields')
# A separate package demonstrates fresh starter content without resetting it.
check(package_absent(REVIEW),'Review12 package is absent before first installation')
print(call('install',args.review_apk,timeout=180).decode().strip(),flush=True)
check(installed_hash(REVIEW)==review_receipt['apk_sha256'],'Installed review APK matches final release SHA256')
call('logcat','-c')
launch(REVIEW)
raw,initial=wait_save(REVIEW,lambda d:d['state'].get('mode')=='live')
(BASE/'review-initial.json').write_bytes(raw)
check(initial.get('customer_navigation_version')==1 and initial.get('customer_admission_version')==1 and len(initial['state']['objects'])==16 and initial['configuration']['starting_coins']==120,'Fresh review starts admission/navigation version1 and the original two-menu scene with owned supplies')
rendered(REVIEW,'review-fresh-live',edit=False)
held=hold(EDIT,'00-edit-pointer-down')
check(held['state']['mode']=='live','Edit press feedback is captured on pointer down before its release enters Edit')
raw,paused=wait_save(REVIEW,lambda d:d['state'].get('mode')=='edit')
raw,paused=rendered(REVIEW,'01-edit-paused')
shop_before=data(REVIEW)[1];held=hold(shop(paused),'01a-shop-pointer-down')
check(same(shop_before,held),'Shop pointer down preserves exact paused state before release feedback')
check(same(shop_before,data(REVIEW)[1]),'Quiet cream Shop shows unavailable feedback while preserving the paused restaurant')
screen('01b-shop-unavailable');time.sleep(1.4)
cancel_before=data(REVIEW)[1]
cancel_hold(layer(paused,'people'),pixel((104.,1000.)),'01c-people-cancel')
check(same(cancel_before,data(REVIEW)[1]),'Dragging a People press outside cancels without changing layer, tray or paused state')
press_home=held_background(layer(paused,'people'),'01d-people-background')
check(same(paused,press_home['held']),'People pointer remains armed only visually before release or background')
check(same(paused,press_home['background']),'Home during a held People touch preserves every paused saved field')
check(press_home['pid_before']==press_home['pid_after'] and same(paused,press_home['resumed']),'Same-process rendered resume cancels held People press without changing layer or tray')
check(same(paused,press_home['released']),'The original People gesture orphan release after resume performs no action')
tap(*layer(paused,'people'))
_,fresh_people=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='people')
check(fresh_people['state']['editor']['tray_open'],'A fresh People press after background cancellation works normally')
snapshot('01e-fresh-people-after-background')
tap(*layer(fresh_people,'layout'))
_,restored_layout=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout')
check(same(paused,restored_layout),'Returning to Layout after cancelled-touch verification retains the complete original paused state')

time.sleep(2)
check(same(paused,data(REVIEW)[1]),'Edit freezes customer paths, food, chef progress, timers, fractional remainder and RNG')
# Use the deliberately disconnected stool; no customer owns it.
check(not any(c['seat_id']=='seat-5' for c in paused['state']['customers']),'Disconnected stool is free for touch editing')
tap(*visible_point(paused,'seat-5',label='S14-stool-select'))
raw,selected=wait_save(REVIEW,lambda d:d['state']['editor']['selected_id']=='seat-5')
snapshot('02-selected-stool')
old_facing=obj(selected,'seat-5')['facing']
tap(*tool(selected))
raw,rotated=wait_save(REVIEW,lambda d:obj(d,'seat-5')['facing']!=old_facing)
check(rotated['state']['editor']['selected_id']=='seat-5','Touch rotation changes facing and retains selection')
snapshot('03-rotated-stool')
object_drag(rotated,'seat-5',(6,7),label='S15-stool-valid-drag')
raw,moved=wait_save(REVIEW,lambda d:obj(d,'seat-5').get('y')==7)
check(obj(moved,'seat-5')['x']==6 and moved['state']['editor']['selected_id']=='seat-5','Selected-object drag commits its new tile immediately')
snapshot('04-moved-stool')
invalid_before=data(REVIEW)[1]
object_drag(moved,'seat-5',(2,6),label='S16-stool-occupied-drag')
invalid_after=data(REVIEW)[1]
check(same(invalid_before,invalid_after),'Occupied-tile drop restores the complete prior saved arrangement')
snapshot('05-invalid-drop-rejected')
tray_before=data(REVIEW)[1]
swipe(visible_point(tray_before,'seat-5',label='S17-stool-tray-drag'),pixel((500.,CANVAS_H-200.)),ms=650)
tray_after=data(REVIEW)[1]
check(same(tray_before,tray_after),'Selected-object release over the inventory tray rejects the drop even above a valid underlying floor tile')
snapshot('05b-tray-drop-rejected')
layer_before=data(REVIEW)[1]
swipe(visible_point(layer_before,'seat-5',label='S18-stool-control-drag'),layer(layer_before,'people'),ms=650)
layer_after=data(REVIEW)[1]
check(same(layer_before,layer_after),'Selected-object release over a layer control rejects its underlying floor tile and leaves layer selection unchanged')
snapshot('05c-layer-control-drop-rejected')
invalid_after=layer_after
count=stock(invalid_after,'stool-plain')['count'];coins=invalid_after['state']['coins']
tap(*tool(invalid_after,remove=True))
raw,removed=wait_save(REVIEW,lambda d:not obj(d,'seat-5'))
check(stock(removed,'stool-plain')['count']==count+1 and removed['state']['coins']==coins,'Touch removal returns one stool to inventory without a coin refund')
snapshot('06-returned-to-inventory')
swipe(card(removed,1),cell(removed,6,7),ms=650)
raw,placed=wait_save(REVIEW,lambda d:stock(d,'stool-plain')['count']==count)
placed_id=placed['state']['editor']['selected_id']
check(placed_id.startswith('editor-object-') and obj(placed,placed_id).get('x')==6 and obj(placed,placed_id).get('y')==7,'Inventory drag places one owned stool and selects it')
snapshot('07-inventory-placed')
held=hold(page(placed,next=True),'08a-next-page-pointer-down')
check(held['state']['editor']['page']==0,'Narrow pager press feedback begins before release advances the four-good Layout page')
raw,paged=wait_save(REVIEW,lambda d:d['state']['editor']['page']==1)
check(paged['state']['editor']['layer']=='layout','Four-good Layout paging advances to the remaining owned inventory')
snapshot('08-inventory-next-page')
# The final one-good page narrows and recentres the drawer; carets move with it.
next_disabled_before=data(REVIEW)[1]
tap(*page(paged,next=True))
check(same(next_disabled_before,data(REVIEW)[1]),'Bare disabled Next target on the narrowed final page blocks underlying floor and preserves every saved field')
tap(*page(paged,next=False))
_,previous_page=wait_save(REVIEW,lambda d:d['state']['editor']['page']==0)
previous_expected=json.loads(json.dumps(paged));previous_expected['state']['editor']['page']=0;previous_expected['state']['editor']['pages']['layout']=0
check(same(previous_expected,previous_page),'Bare Previous target returns to the four-good page with only remembered page fields changed')
snapshot('08b-inventory-previous-page')
tap(*page(previous_page,next=True))
_,paged_again=wait_save(REVIEW,lambda d:d['state']['editor']['page']==1)
check(same(paged,paged_again),'Bare Next target returns to the narrow one-good page without mutating restaurant or stock')
paged=paged_again
# The restored beige backing owns blank gutters outside the narrow drawer and
# its bare paging targets. Tapping or swiping there must not reach the world.
gutter_before=data(REVIEW)[1]
tap(*pixel((70.,CANVAS_H-190.)))
check(same(gutter_before,data(REVIEW)[1]),'Blank beige gutter tap preserves selection, camera, stock and every paused field')
snapshot('08c-beige-gutter-tap-blocked')
swipe(pixel((70.,CANVAS_H-190.)),pixel((70.,CANVAS_H-95.)),ms=650)
check(same(gutter_before,data(REVIEW)[1]),'Blank beige gutter swipe is shielded from world pan and drag input')
snapshot('08d-beige-gutter-swipe-blocked')

held=hold(layer(paged,'people'),'09a-people-pointer-down')
check(held['state']['editor']['layer']=='layout','Independent People curtain press feedback begins before the release changes layer')
raw,people=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='people')
check(people['state']['editor']['tray_open'] and len([i for i in people['state']['inventory'] if i['kind']=='chef'])==3,'People switches to the shared three-profile roster tray')
snapshot('09-people-tray')
popup_before=data(REVIEW)[1]
pid_before=call('shell','pidof',REVIEW).decode().strip()
tap(*card(people,0));time.sleep(.4)
snapshot('09a-staff-details-popup')
check(same(popup_before,data(REVIEW)[1]),'Opening a chef profile is inspection and preserves the paused Edit save')
call('shell','input','keyevent','4');time.sleep(.5)
check(call('shell','pidof',REVIEW).decode().strip()==pid_before,'System Back closes staff details without leaving the running app')
check(same(popup_before,data(REVIEW)[1]),'System Back from staff details preserves exact paused Edit state')
snapshot('09b-staff-popup-closed-by-back')
# close_inspection restores keyboard focus to the inspected card. Activating
# the focused control must reopen that profile without changing paused state.
call('shell','input','keyevent','KEYCODE_DPAD_CENTER');time.sleep(.4)
screen('09c-focused-profile-reopened')
check(same(popup_before,data(REVIEW)[1]),'Activating restored People card focus reopens inspection without mutating the restaurant')
call('shell','input','keyevent','KEYCODE_DPAD_CENTER');time.sleep(.4)
screen('09d-focused-close-activated')
check(same(popup_before,data(REVIEW)[1]) and call('shell','pidof',REVIEW).decode().strip()==pid_before,'Focused Close button returns to the roster and preserves the running paused app')

tap(*layer(people,'people'))
raw,collapsed=wait_save(REVIEW,lambda d:not d['state']['editor']['tray_open'])
check(collapsed['state']['editor']['layer']=='people','Active layer tap collapses its tray while retaining the layer')
snapshot('10-people-tray-collapsed')
tap(*layer(collapsed,'floor'))
raw,floor=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='floor' and d['state']['editor']['tray_open'])
prior=floor
tap(*card(floor,0))
check(same(prior,data(REVIEW)[1]),'Current unavailable floor swatch cannot mutate the restaurant')
snapshot('11-floor-disabled')
tap(*layer(floor,'layout'))
raw,layout=wait_save(REVIEW,lambda d:d['state']['editor']['layer']=='layout' and d['state']['editor']['page']==1)
check(layout['state']['editor']['tray_open'],'Changing layers restores Layout page and opens its tray')
# One outside swipe clears selection and pans at the same fixed tile pitch.
start=cell(layout,3,3);end=(start[0]-288,start[1])
swipe(start,end,ms=550)
raw,panned=wait_save(REVIEW,lambda d:d['state']['camera']['x']>layout['state']['camera']['x'])
check(panned['state']['editor']['selected_id']=='' and panned['state']['mode']=='edit','One outside swipe deselects and pans continuously without leaving Edit')
snapshot('12-edit-panned')
tap(*layer(panned,'layout'))
raw,preserved=wait_save(REVIEW,lambda d:not d['state']['editor']['tray_open'])
raw,preserved=snapshot('13-edit-before-lifecycle')
# Background, force-stop and Back must not advance paused simulation or RNG.
home_before,before=home(REVIEW,'review-edit-home-before')
time.sleep(3)
check(data(REVIEW)[0]==home_before,'Home background keeps the paused save byte-stable')
launch(REVIEW)
raw,after_home=rendered(REVIEW,'14-edit-home-reopened')
check(same(before,after_home),'Home return retains exact paused Edit state, layer, tray, camera and RNG')
call('shell','am','force-stop',REVIEW);time.sleep(1)
check(data(REVIEW)[0]==raw,'Force-stop preserves the last immediate editor save')
launch(REVIEW)
raw,after_force=rendered(REVIEW,'15-edit-force-stop-reopened')
check(same(after_home,after_force),'Cold reopen retains the exact paused restaurant and inventory')
call('shell','input','keyevent','KEYCODE_BACK');time.sleep(1)
check(not process_running(REVIEW),'Android Back from the editor exits the app after saving')
back_raw,back=save(REVIEW,'review-edit-back-before-reopen')
time.sleep(2)
check(data(REVIEW)[0]==back_raw,'Android Back saves a stable paused restaurant before closing')
launch(REVIEW)
raw,after_back=rendered(REVIEW,'16-edit-back-reopened')
check(same(back,after_back),'Android Back reopen retains exact mode, remembered page, layer, tray and service state')
paused_elapsed=after_back['state']['elapsed']
held=hold(LIVE,'17a-live-pointer-down')
check(same(after_back,held),'Live press feedback is captured while the complete restaurant is still paused until release')
raw,resumed=wait_save(REVIEW,lambda d:d['state']['mode']=='live' and d['state']['elapsed']>paused_elapsed)
check(resumed['state']['elapsed']>paused_elapsed,'Top-right Live resumes the preserved service simulation')
time.sleep(1)
home(REVIEW,'review-live-after-edit')
launch(REVIEW)
rendered(REVIEW,'17-live-resumed',edit=False)
home(REVIEW,'review-final')
check(data(NORMAL)[0]==normal_before and data(NORMAL,'session.backup.json')[0]==normal_backup,'Review12 installation and all editing/lifecycle checks leave normal app primary and backup untouched')
log=call('logcat','-d','-s','godot:V','AndroidRuntime:E').decode(errors='replace')
(BASE/'runtime-logcat.txt').write_text(log)
errors=[line for line in log.splitlines() if any(text in line for text in ('SCRIPT ERROR','ERROR:','FATAL EXCEPTION','Fatal signal'))]
check(not errors,'No Godot script errors or Android runtime crashes during actual APK interaction')
report.update(customer_navigation_version=initial['customer_navigation_version'],customer_admission_version=initial['customer_admission_version'],upgrade_preserved_legacy_state=True,customer_admission_migration="0 to 1: admission marker, missing four-second tuning and two neutral feedback clocks only",normal_apk_path=str(args.normal_apk),review_apk_path=str(args.review_apk),render_readiness='Actual game pixels required before all cold-reopen input/captures',review_gameplay_state_injected=False,old_normal_baseline_state_injected=False,version_name=normal_receipt['version_name'],version_code=normal_receipt['version_code'],normal_package=normal_receipt['package'],review_package=review_receipt['package'],signer_sha256=normal_receipt['signer_sha256'],runtime_source_file_count=len(normal_receipt['source_files']),normal_apk_sha256=normal_receipt['apk_sha256'],review_apk_sha256=review_receipt['apk_sha256'],runtime_source_fingerprint=review_receipt['runtime_source_fingerprint'],review_initial_coins=initial['state']['coins'],paused_elapsed=paused_elapsed,final_camera=after_back['state']['camera'],saved_editor=after_back['state']['editor'],runtime_errors=errors,runtime_warnings=[line for line in log.splitlines() if 'WARNING:' in line])
write('android-editor-verification',report)
print(json.dumps({'checks':len(report['checks']),'passed':True,'report':str(BASE/'android-editor-verification.json')}))
