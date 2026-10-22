from pathlib import Path
from PIL import Image,ImageDraw
import json
base=Path(__file__).resolve().parents[2];out=base/'evidence/source-filter-study';rows=[]
for d in ['S','E']:
 for native_filter,name,path in [(1.5,'historical',base/'evidence'/f'source-native-{d}.png'),(.01,'narrow',out/f'narrow-filter-native-{d}.png')]:
  im=Image.open(path).convert('RGBA')
  for mode,kernel in [('lanczos',Image.Resampling.LANCZOS),('box',Image.Resampling.BOX)]:
   p=im.resize((384,704),kernel);p.save(out/f'{name}-{mode}-{d}.png');canvas=Image.new('RGBA',(896,1280));anchor=(448,768)
   for shift in [-1,0,1]:
    dx,dy=(shift*256,0) if d=='S' else (0,shift*256)
    canvas.alpha_composite(p,(anchor[0]-192+dx,anchor[1]-496+dy))
   canvas.save(out/f'join-{name}-{mode}-{d}.png')
   # At source S seam x=+0.5, z~0.5; sample the true interior meeting line.
   seam=[canvas.getpixel((x,672))[3] for x in [575,576]] if d=='S' else None
   rows.append({'direction':d,'nativeFilterSize':native_filter,'wholeCanvasKernel':mode,'publishedFrame':[384,704],'joinedCommonCanvas':[896,1280],'sampleAlphaAtSSeam':seam,'path':f'join-{name}-{mode}-{d}.png'})
sheet=Image.new('RGB',(1024,576),(184,199,202));draw=ImageDraw.Draw(sheet)
for i,(name,label) in enumerate([('historical-lanczos','historical filter1.5 + LANCZOS'),('historical-box','historical filter1.5 + BOX'),('narrow-lanczos','native filter0.01 + LANCZOS'),('narrow-box','native filter0.01 + BOX')]):
 im=Image.open(out/f'join-{name}-S.png');# whole original evidence retained; sheet crops are diagnostic windows, never assets
 crop=im.crop((40,445,856,850)).resize((480,238),Image.Resampling.LANCZOS);x=(i%2)*512;y=(i//2)*288;draw.text((x+10,y+10),label,fill=(20,28,35));sheet.paste(crop,(x+10,y+34),crop)
sheet.save(out/'sampling-comparison-sheet.png')
(out/'analysis.json').write_text(json.dumps({'scope':'Technical source-only study; historical pixels retained. No candidate, source edit or approved alternative. Whole frames only, no per-edge repair, alpha clamps, profile inflation or warps.','cases':rows,'finding':'Native filter0.01 plus whole-frame BOX gives fully opaque S seam samples at the exact registered cut, while historical/LANCZOS and single-method changes retain partial-alpha seams. Root must decide this explicit capture change before editor freeze. E requires actual browser and native all-facing follow-through; these diagnostics do not approve style.'},indent=2)+'\n')
# Separate v2 fixture/drivers retain original browser evidence hashes.
s=(base/'resources/drivers/consumer-fixture.html').read_text();s=s.replace("['N','E','S','W']","['S','E']").replace('source-published-${p.direction}.png','source-filter-study/narrow-box-${p.direction}.png').replace('Unmodified rock-half-width source','Source-only filter0.01 + whole-frame BOX study')
(base/'resources/drivers/consumer-filter-study.html').write_text(s)
s=(base/'resources/drivers/capture_browser.mjs').read_text();s=s.replace("'evidence/browser'","'evidence/browser-filter-study'").replace('consumer-fixture.html','consumer-filter-study.html').replace('capture_browser.mjs','capture_browser_filter_study.mjs')
(base/'resources/drivers/capture_browser_filter_study.mjs').write_text(s)
print(json.dumps([r for r in rows if r['direction']=='S']))
