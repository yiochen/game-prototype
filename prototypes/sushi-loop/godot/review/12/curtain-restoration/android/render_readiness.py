"""Observe rendered application pixels before cold-start input or screenshot evidence."""
from qa_common import *
import io
from PIL import Image

def rendered(pkg,label,edit=True,timeout=45):
 until=time.monotonic()+timeout;consecutive=0
 while time.monotonic()<until:
  raw=call('exec-out','screencap','-p')
  im=Image.open(io.BytesIO(raw)).convert('RGB')
  # Observe enough gold/red ink in the fixed HUD regions. This tolerates the
  # revised visible-face alignment without mistaking the teal splash for UI.
  gold=sum(r>220 and g>130 and b<140 for r,g,b in im.crop((35,35,230,225)).getdata())
  red=sum(r>210 and g<150 and b<150 for r,g,b in im.crop((800,50,1040,195)).getdata())
  coin_drawn=gold>200
  live_drawn=red>500
  if coin_drawn and (not edit or live_drawn):
   consecutive+=1
   if consecutive>=2:
    (BASE/(label+'.png')).write_bytes(raw)
    return save(pkg,label)
  else:consecutive=0
  time.sleep(.3)
 (BASE/(label+'-readiness-timeout.png')).write_bytes(raw)
 raise AssertionError('Rendered game UI readiness timeout: '+label)

def hold(point,label,duration=3000):
 # A stationary actual Android touchscreen swipe holds down until release.
 # The caller observes both held and released states before sending more input.
 point=tuple(map(round,point))
 process=subprocess.Popen([str(ADB),'-s',SERIAL,'shell','input','swipe',str(point[0]),str(point[1]),str(point[0]),str(point[1]),str(duration)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 time.sleep(.65)
 screen(label)
 assert process.poll() is None,'Held touch ended before paused-state sampling'
 held=data(REVIEW)[1]
 stdout,stderr=process.communicate(timeout=10)
 assert process.returncode==0,stderr.decode(errors='replace')
 time.sleep(.3)
 return held

def cancel_hold(start,end,label,duration=2400):
 start=tuple(map(round,start));end=tuple(map(round,end))
 process=subprocess.Popen([str(ADB),'-s',SERIAL,'shell','input','swipe',str(start[0]),str(start[1]),str(end[0]),str(end[1]),str(duration)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 time.sleep(.3);screen(label+'-down')
 time.sleep(.65);screen(label+'-outside')
 stdout,stderr=process.communicate(timeout=10)
 assert process.returncode==0,stderr.decode(errors='replace')
 time.sleep(.3);screen(label+'-released')


def held_background(point,label,duration=30000):
 # One actual touchscreen gesture spans Home and rendered warm resume. There
 # is no new DOWN after resume; the original gesture's eventual UP is orphaned.
 point=tuple(map(round,point))
 pid_before=call('shell','pidof',REVIEW).decode().strip()
 process=subprocess.Popen([str(ADB),'-s',SERIAL,'shell','input','swipe',str(point[0]),str(point[1]),str(point[0]),str(point[1]),str(duration)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 time.sleep(.65);screen(label+'-held')
 held=data(REVIEW)[1]
 call('shell','input','keyevent','KEYCODE_HOME');time.sleep(1)
 background=data(REVIEW)[1]
 launch(REVIEW)
 _,resumed=rendered(REVIEW,label+'-resumed-before-release')
 assert process.poll() is None,'Original touch released before rendered resume'
 pid_after=call('shell','pidof',REVIEW).decode().strip()
 stdout,stderr=process.communicate(timeout=40)
 assert process.returncode==0,stderr.decode(errors='replace')
 time.sleep(.4);screen(label+'-orphan-released')
 _,released=save(REVIEW,label+'-orphan-released')
 return {'held':held,'background':background,'resumed':resumed,'released':released,'pid_before':pid_before,'pid_after':pid_after}
