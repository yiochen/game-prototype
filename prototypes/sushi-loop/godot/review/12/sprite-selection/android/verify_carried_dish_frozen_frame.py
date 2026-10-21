"""Use the existing real paused plate frame, including the actual quantized camera value."""
from pathlib import Path
source=Path('/private/tmp/sushi12-sprite-review/verify_carried_dish.py').read_text()
prefix=source[:source.index('launch(REVIEW);')]
exec(compile(prefix,'verify_carried_dish.py [imports and existing report]','exec'))
_,d=save(REVIEW,'D01-actual-camera-source-before')
write('carried-dish-camera-calibration',{'classification':'Supplementary fixture used an unnecessarily exact camera-zero readiness condition after adb pixel quantization; app pan and saved state are valid','requested_camera_x':0,'actual_camera':d['state']['camera'],'use_actual_camera_in_atlas_transform':True,'raw_log':'android-carried-dish.log','successful_log':'android-carried-dish-continuation.log','gameplay_state_injected':False})
tail=source[source.index('attempts=[];candidate=None'):].replace("'log':'android-carried-dish.log'","'log':'android-carried-dish-continuation.log'")
exec(compile(tail,'verify_carried_dish.py [real frozen source frame]','exec'))
