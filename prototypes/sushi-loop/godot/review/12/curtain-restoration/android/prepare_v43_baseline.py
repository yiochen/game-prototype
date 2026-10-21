"""Run only after root ready signal; actual old v43 normal touch baseline, clone only."""
import sys,time,json
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-curtain-review')
from qa_common import *
from touch_geometry import *
from render_readiness import rendered
apk=PROJECT/'build/sushi-loop-restaurant-editor-release-v0.4.3.apk'
receipt=json.loads(apk.with_suffix('.build.json').read_text())
assert receipt['package']==NORMAL and receipt['version_code']==43 and receipt['version_name']=='0.4.3' and sha(apk)==receipt['apk_sha256']
assert package_absent(REVIEW),'Fresh review app must remain absent'
print(call('install','-r',apk,timeout=180).decode().strip(),flush=True)
launch(NORMAL)
_,d=wait_save(NORMAL,lambda d:d.get('editor_version')==3)
rendered(NORMAL,'old-v43-rendered-before-edit',edit=False)
if d['state']['mode']=='live':
 tap(*EDIT)
 _,d=wait_save(NORMAL,lambda d:d['state']['mode']=='edit')
if d['state']['editor']['layer']!='layout':
 tap(*layer(d,'layout'))
 _,d=wait_save(NORMAL,lambda d:d['state']['editor']['layer']=='layout')
if not d['state']['editor']['tray_open']:
 tap(*layer(d,'layout'))
 _,d=wait_save(NORMAL,lambda d:d['state']['editor']['tray_open'])
if d['state']['editor']['page']==0:
 tap(*page(d,next=True))
 _,d=wait_save(NORMAL,lambda d:d['state']['editor']['page']==1)
assert d['state']['editor']['pages']['layout']==1
rendered(NORMAL,'normal-v43-baseline-rendered')
raw,d=home(NORMAL,'normal-v43-session-before-update')
backup,_=save(NORMAL,'normal-v43-backup-before-update',backup=True)
call('shell','am','force-stop',NORMAL)
write('normal-v43-baseline',{'package':NORMAL,'version_code':43,'apk_sha256':sha(apk),'save_sha256':__import__('hashlib').sha256(raw).hexdigest(),'backup_sha256':__import__('hashlib').sha256(backup).hexdigest(),'editor_version':d['editor_version'],'mode':d['state']['mode'],'editor':d['state']['editor'],'objects':len(d['state']['objects']),'review12_absent':package_absent(REVIEW),'emulator_serial':SERIAL,'state_injected':False,'physical_devices_touched':False})
print('Old normal v43 baseline ready with paused four-slot Layout page 1',flush=True)
