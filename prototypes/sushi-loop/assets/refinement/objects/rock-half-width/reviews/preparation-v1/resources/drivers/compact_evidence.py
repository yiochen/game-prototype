from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
base=Path(__file__).resolve().parents[2];out=base/'evidence';sheet=Image.new('RGB',(916,1336),(210,220,222));draw=ImageDraw.Draw(sheet);clips=[]
for i,d in enumerate(['N','E','S','W']):
 p=out/f'source-joins-v2/join-{d}.png';im=Image.open(p).convert('RGBA');a=im.getchannel('A');box=a.getbbox();clips.append({'direction':d,'alphaBounds':box,'frame':im.size,'touchesCanvas':box[0]<=0 or box[1]<=0 or box[2]>=im.width or box[3]>=im.height});f=im.resize((448,640),Image.Resampling.BOX);x=(i%2)*458+5;y=(i//2)*668+24;sheet.paste(f,(x,y),f);draw.text((x,y-18),d,fill=(20,35,45))
sheet.save(out/'source-joins-v2/contact-sheet.png');historical=Image.open(out/'source-filter-study/join-historical-lanczos-E.png');study=Image.open(out/'source-filter-study/join-narrow-box-E.png');native=Image.open(out/'source-joins-v2/join-E.png').resize((896,1280),Image.Resampling.LANCZOS)
rows=[]
for y in range(469,481):rows.append({'x':448,'y':y,'historicalRGBA':historical.getpixel((448,y)),'narrowBoxRGBA':study.getpixel((448,y)),'nativeJoinedHistoricalRGBA':native.getpixel((448,y))})
s=Image.new('RGB',(768,200),(189,204,207));dr=ImageDraw.Draw(s)
for i,(label,im) in enumerate([('Historical independent',historical),('Narrow BOX independent',study),('Native joined',native)]):
 dr.text((i*256+8,10),label,fill=(20,30,40));crop=im.crop((424,460,472,489)).resize((240,145),Image.Resampling.NEAREST);s.paste(crop,(i*256+8,32),crop)
s.save(out/'source-filter-study/E-opaque-stripe-zoom.png')
comparisons=[]
for folder in ['browser','browser-filter-study']:
 for size in ['390x844','844x390']:
  p=out/f'{folder}/full-chromium-{size}.png';q=out/f'{folder}/headless-shell-{size}.png';a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');comparisons.append({'full':str(p.relative_to(base)),'shell':str(q.relative_to(base)),'exactDecodedRGBA':a.size==b.size and a.tobytes()==b.tobytes(),'fullSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'shellSHA256':hashlib.sha256(q.read_bytes()).hexdigest()})
package=Path('/Users/yiouchen/dev/game-prototype/node_modules/@playwright/test/package.json');dest=base/'resources/node-loaded/@playwright/test/package.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(package,dest)
(out/'compact-evidence-record.json').write_text(json.dumps({'correctedNativeJoinCoverage':clips,'E_seam_RGB_diagnostic':{'scope':'Source-only RGB stripe survives at opaque cap/top pixel; three-way native/composed diagnostic, not candidate evaluation.','pixels':rows},'browserModePixelComparisons':comparisons,'packageMetadata':{'path':str(dest.relative_to(base)),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}},indent=2)+'\n');print(json.dumps({'allV2JoinsUnclipped':all(not c['touchesCanvas'] for c in clips),'browserComparisons':comparisons}))
