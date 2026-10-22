from pathlib import Path
from PIL import Image
import json,hashlib
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-02';report=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  frames=[Image.open(C/'frames'/f'{clip}-{direction}'/f'{i:03}.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS) for i in range(12)]
  for bg in ['light','gray','dark']:
   path=C/'contact-sheets'/f'{clip}-{direction}-{bg}.png';sheet=Image.open(path).convert('RGB');background=sheet.getpixel((0,0));ok=[]
   for i,fr in enumerate(frames):
    expected=Image.new('RGBA',(192,320),(*background,255));expected.alpha_composite(fr);x=i%6*192;y=i//6*352+28
    ok.append(expected.convert('RGB').tobytes()==sheet.crop((x,y,x+192,y+320)).tobytes())
   report.append({'path':str(path.relative_to(C)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'all12CellsExactlyMatchNativeFrames':all(ok),'frameIndices':list(range(12)),'backgroundRGB':list(background),'logicalFrame':[192,320],'placement':'x=(index%6)*192,y=(index//6)*352+28; Lanczos scale0.5 then alpha composite only'})
assert all(r['all12CellsExactlyMatchNativeFrames'] for r in report)
(P/'reviews/round02-independent-sheet-check.json').write_text(json.dumps({'all48SheetsVerified':True,'all192NativeFramesShownOnThreeBackgrounds':True,'sheets':report},indent=2)+'\n')
print('Verified48 sheets /576 diagnostic cells /192 native frames')
