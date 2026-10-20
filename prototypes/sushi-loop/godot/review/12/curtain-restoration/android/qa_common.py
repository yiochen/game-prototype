"""Android #12 QA: only the cloned emulator and two exhibition app packages."""
from pathlib import Path
import hashlib,json,os,re,subprocess,time
BASE=Path('/private/tmp/sushi12-curtain-review')
PROJECT=Path('/Users/yiouchen/.codex/worktrees/sushi-loop-tickets/game-prototype/prototypes/sushi-loop/godot')
SDK=Path(os.environ.get('ANDROID_HOME',str(Path.home()/'Library/Android/sdk')))
ADB=SDK/'platform-tools/adb'
SERIAL='emulator-5560'
NORMAL='com.yiochen.sushilooptickets'
REVIEW=NORMAL+'.review12'
def call(*args,timeout=60):
 assert SERIAL=='emulator-5560'
 for retry in range(5):
  result=subprocess.run([str(ADB),'-s',SERIAL,*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
  if result.returncode==0:return result.stdout
  if retry==4:raise RuntimeError(result.stderr.decode(errors='replace') or result.stdout.decode(errors='replace'))
  time.sleep(.5)
def sha(path):
 d=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):d.update(chunk)
 return d.hexdigest()
def data(pkg,filename='session.json'):
 assert pkg in (NORMAL,REVIEW)
 raw=call('exec-out','cat',f'/data/user/0/{pkg}/files/{filename}')
 envelope=json.loads(raw)
 assert hashlib.sha256(envelope['payload'].encode()).hexdigest()==envelope['sha256']
 return raw,json.loads(envelope['payload'])
def save(pkg,label,backup=False):
 raw,d=data(pkg,'session.backup.json' if backup else 'session.json')
 (BASE/(label+'.json')).write_bytes(raw)
 return raw,d
def launch(pkg):
 assert pkg in (NORMAL,REVIEW)
 return call('shell','am','start','-n',pkg+'/com.godot.game.GodotApp')
def wait_save(pkg,predicate,timeout=45):
 deadline=time.monotonic()+timeout;last=None
 while time.monotonic()<deadline:
  time.sleep(.3)
  try:
   raw,d=data(pkg);last=d
   if predicate(d):return raw,d
  except (RuntimeError,json.JSONDecodeError):pass
 raise AssertionError('Saved state did not reach expected transition: '+json.dumps(last and {'elapsed':last['state'].get('elapsed'),'mode':last['state'].get('mode'),'editor':last['state'].get('editor')}))
def home(pkg,label):
 call('shell','input','keyevent','KEYCODE_HOME');time.sleep(1)
 return save(pkg,label)
def screen(label):
 (BASE/(label+'.png')).write_bytes(call('exec-out','screencap','-p'))
def write(name,value):(BASE/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
def installed_hash(pkg):
 path=call('shell','pm','path',pkg).decode().strip().removeprefix('package:')
 return call('shell','sha256sum',path).decode().split()[0]
def tap(x,y):
 call('shell','input','tap',round(x),round(y));time.sleep(.35)
def swipe(start,end,ms=450):
 call('shell','input','swipe',*map(round,start),*map(round,end),ms);time.sleep(.35)
def obj(d,identity):return next((o for o in d['state']['objects'] if o['id']==identity),{})
def stock(d,identity):return next(o for o in d['state']['inventory'] if o['id']==identity)
def same(a,b,tolerance=1e-7):
 if isinstance(a,(float,int)) and isinstance(b,(float,int)):return abs(a-b)<tolerance
 if type(a)!=type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k],tolerance) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y,tolerance) for x,y in zip(a,b))
 return a==b

def package_absent(pkg):
 assert pkg in (NORMAL,REVIEW)
 result=subprocess.run([str(ADB),'-s',SERIAL,'shell','pm','path',pkg],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if result.returncode in (0,1) and not result.stdout.strip() and not result.stderr.strip():return True
 if result.returncode==0 and result.stdout.startswith(b'package:'):return False
 raise RuntimeError('Unexpected package lookup failure')

def process_running(pkg):
 assert pkg in (NORMAL,REVIEW)
 result=subprocess.run([str(ADB),'-s',SERIAL,'shell','pidof',pkg],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if result.returncode==0:return bool(result.stdout.strip())
 if result.returncode==1 and not result.stdout.strip() and not result.stderr.strip():return False
 raise RuntimeError('Unexpected process lookup failure')
