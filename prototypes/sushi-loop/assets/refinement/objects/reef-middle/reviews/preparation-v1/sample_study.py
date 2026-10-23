import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
from PIL import Image
BASE=Path(__file__).resolve().parent;E=BASE/'evidence/study-filter001'
for d in ['N','E','S','W']:
 for prefix in ['single','three-joined']:
  i=Image.open(E/'native'/(prefix+'-'+d+'.png')).convert('RGBA');p=E/'packed'/(prefix+'-'+d);p.mkdir(parents=True)
  i.resize((i.width//2,i.height//2),Image.Resampling.BOX).save(p/'sheet.png')
(E/'sampling-study-policy.json').write_text(json.dumps({'status':'source-only proposal, not adopted','nativeChange':{'render.filter_size':.01},'publishChange':'Uniform complete 4x frame to2x BOX; original default1.5 plus wholeframe LANCZOS baseline retained. No mask/alpha/RGB edits or geometry overlap.','cameraRootMaterialsGeometryAndLights':'unchanged from source replay'},indent=2)+'\n')
s=(BASE/'capture_consumer.cjs').read_text();s=s.replace("const BASE=__dirname;", "const BASE=__dirname;const OUT=path.join(BASE,'evidence/study-filter001');")
s=s.replace('/evidence/packed/','/evidence/study-filter001/packed/').replace("path.join(BASE,'evidence/consumer')","path.join(OUT,'consumer')").replace("path.join(BASE,'evidence',file)","path.join(OUT,file)").replace("path.join(BASE,'evidence/consumer-report.json')","path.join(OUT,'consumer-report.json')")
(BASE/'capture_consumer_study.cjs').write_text(s)
print('study sampling complete')
