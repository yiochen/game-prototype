from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageChops,ImageDraw
H=Path(__file__).resolve().parent;ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');report=json.loads((H/'consumer-report.json').read_text())
pairs=[]
for a,b in zip(report['browserModes'][0]['screenshots'],report['browserModes'][1]['screenshots']):
 x=Image.open(H/'consumer'/a['file']).convert('RGBA');y=Image.open(H/'consumer'/b['file']).convert('RGBA');d=ImageChops.difference(x,y);pairs.append({'first':a['file'],'second':b['file'],'decodedExact':x.size==y.size and x.tobytes()==y.tobytes(),'size':list(x.size),'maxRGBA':[v[1] for v in d.getextrema()]})
sheet=Image.new('RGB',(6*195,2*442),'#777777');draw=ImageDraw.Draw(sheet)
for row,mode in enumerate(report['browserModes']):
 for i,item in enumerate(mode['playback']):
  im=Image.open(H/'consumer'/item['file']).convert('RGB').resize((195,422),Image.Resampling.LANCZOS);sheet.paste(im,(i*195,row*442));draw.text((i*195+2,row*442+423),f"{mode['id']} {item['evidence']['elapsed']:.3f}s",fill='white')
sheet.save(H/'consumer/playback-samples-sheet.png')
# Freeze only React source modules actually consumed by esbuild, plus package identity.
meta=json.loads((H/'resources/consumer/bundle-meta.json').read_text());deps=[]
for key in meta['inputs']:
 if '/node_modules/' not in key:continue
 src=(ROOT/key).resolve();rel=src.as_posix().split('/node_modules/',1)[1];dst=H/'resources/consumer/bundle-inputs'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);deps.append({'metafileInput':key,'frozen':str(dst.relative_to(H)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
for name in ['react','esbuild','@playwright/test']:
 src=ROOT/'node_modules'/name/'package.json';dst=H/'resources/consumer/package-identities'/(name.replace('/','-')+'.json');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
(H/'consumer-analysis.json').write_text(json.dumps({'pairs':pairs,'frozenBundleInputs':deps,'scope':'Real current helper functions on replay-published complete frames; logical and phone CSS sizes; both Playwright browser modes; actualrAF two-second playback. Not the full production game or Godot.','playbackCoverage':{b['id']:{d:[r['frame'] for r in b['playbackFinal']['frameRecords'] if r['direction']==d] for d in ['N','E','S','W']} for b in report['browserModes']}},indent=2)+'\n')
print('browserPairs',pairs)
print('support',[(o['object'],o['contactSectionBounds']) for o in json.loads((H/'support-sections.json').read_text())['objects'] if o['contactSectionBounds']])
