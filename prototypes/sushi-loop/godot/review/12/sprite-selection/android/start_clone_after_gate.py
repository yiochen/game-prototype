"""Start only after parent confirms every Godot import/export has completed."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/private/tmp/sushi12-sprite-review')
from qa_common import *
parser=argparse.ArgumentParser()
parser.add_argument('--exports-complete',action='store_true',required=True)
args=parser.parse_args()
assert args.exports_complete
prep=json.loads((BASE/'qa-preparation.json').read_text())
isolation=json.loads((BASE/'avd-isolation.json').read_text())
assert not isolation['emulator_launched'], 'Clone was already launched; do not start twice'
result=subprocess.run([str(ADB),'devices','-l'],capture_output=True,check=True)
entries=[line for line in result.stdout.decode().splitlines()[1:] if line.strip()]
assert not any(line.split()[0]==SERIAL for line in entries),'Dedicated port is already occupied'
command=[str(SDK/'emulator/emulator'),'-avd','Pixel_8_API_35_Review12Sprite','-port','5560',*isolation['launch_flags']]
env=os.environ.copy();env['ANDROID_AVD_HOME']=str(BASE/'avd');env['ANDROID_EMULATOR_HOME']=str(BASE/'emulator-settings')
log=(BASE/'emulator.log').open('wb')
process=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
write('emulator-process',{'pid':process.pid,'args':command,'isolated_avd_home':env['ANDROID_AVD_HOME'],'isolated_emulator_home':env['ANDROID_EMULATOR_HOME']})
isolation['emulator_launched']=True;write('avd-isolation',isolation)
prep.update(exports_complete_gate_received=True,adb_started=True,emulator_launched=True,existing_device_count=len(entries),dedicated_serial_absent_before_launch=True);write('qa-preparation',prep)
print(json.dumps({'clone_pid':process.pid,'boot_wait':'started','serial':SERIAL}),flush=True)
until=time.monotonic()+180
while time.monotonic()<until:
 assert process.poll() is None,'Clone emulator exited during boot'
 try:
  if call('shell','getprop','sys.boot_completed',timeout=10).strip()==b'1':break
 except (RuntimeError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise AssertionError('Clone boot timeout')
print(call('root').decode().strip(),flush=True)
call('wait-for-device');time.sleep(2)
assert package_absent(REVIEW),'Fresh review package must be absent from copied AVD'
print(json.dumps({'clone_booted':True,'review_package_absent':True,'physical_devices_touched':False}),flush=True)
