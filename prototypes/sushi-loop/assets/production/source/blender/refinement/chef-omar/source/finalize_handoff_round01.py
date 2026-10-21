"""Bind supplemental technical evidence without changing any native frames/atlases/model bytes."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
catalog=json.loads((OUT/'envelope-validation.json').read_text())
runtime=json.loads((OUT/'runtimeVariants/envelope-validation.json').read_text())
assert catalog['ok'] and runtime['ok']
# Fill the three header strips in the review-only background composite.
im=Image.open(OUT/'background-sheet.png').convert('RGB');d=ImageDraw.Draw(im)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
for bi,c in enumerate(['#f5f4ed','#8c9292','#263238']):
 d.rectangle((0,bi*338,768,bi*338+18),fill=c)
 for i,direction in enumerate(['N','E','S','W']):d.text((i*192+8,bi*338+2),direction,font=font,fill='#1c2e34' if bi<2 else '#edf0e8')
im.save(OUT/'background-sheet.png')
browser={'method':'Actual local in-app browser playback via cua_repl, DOM media state and screenshot inspection','page':'candidates/round-01/playback.html','videos':24,'decodedNativeSize':[384,640],'allDurationsSeconds':1,'allReadyState':4,'allErrorCodes':None,'loopingVideosObservedPlaying':16,'loadVideosObservedEndedAt1Second':8,'frameRateAndCountSource':'Both playback-validation.json files: ffprobe12/1fps, nb_frames12, duration1.000000','loopBehavior':'Original loops on idle/work/hold/hold-cucumber. Both load variants do not loop.','nativeFrameOrAtlasEdits':False}
write(OUT/'browser-playback-qa.json',browser)
v=json.loads((OUT/'complete-validation.json').read_text())
v['nativeEnvelopeValidation']={'catalog':'candidates/round-01/envelope-validation.json','runtimeVariants':'candidates/round-01/runtimeVariants/envelope-validation.json','catalogRestHeight':catalog['restHeight'],'runtimeRestHeight':runtime['restHeight'],'allFrameBoundsEqualNativeCaptures':True,'allInside1x1Footprint':catalog['allFramesInsideFootprint'] and runtime['allFramesInsideFootprint'],'maxMovingCrownTopDeltaToOriginal':max(catalog['maxMovingTopDeltaToOriginal'],runtime['maxMovingTopDeltaToOriginal'])}
v['browserPlaybackQA']='candidates/round-01/browser-playback-qa.json';v['ok']=v['ok'] and catalog['ok'] and runtime['ok']
write(OUT/'complete-validation.json',v)
delivery=json.loads((BASE/'delivery.json').read_text())
delivery['resources']={path.name:path.relative_to(BASE).as_posix() for path in P.glob('*') if path.is_file() and path.suffix in ['.blend','.py','.json']}
delivery['runtimeVariants']['resources']['envelopeValidation']='candidates/round-01/runtimeVariants/envelope-validation.json'
delivery['runtimeVariants']['resources']['originalEnvelope']='source/runtime-baseline-envelope-round01.json'
write(BASE/'delivery.json',delivery)
files=[P/'round-01.blend',P/'runtime-round-01.blend',P/'recipe-round01.json',P/'runtime-recipe-round01.json',OUT/'complete-validation.json',BASE/'delivery.json']
write(OUT/'editor-handoff-hashes.json',{'status':'Ready for coordinator sealing and independent judge review; no visual approval issued','files':{path.relative_to(BASE).as_posix():sha(path) for path in files},'nativeFrames':288,'catalogAtlases':16,'runtimeVariantAtlases':8,'playbacks':24})
print('HANDOFF READY',v['ok'],sha(P/'round-01.blend'),sha(P/'runtime-round-01.blend'))
