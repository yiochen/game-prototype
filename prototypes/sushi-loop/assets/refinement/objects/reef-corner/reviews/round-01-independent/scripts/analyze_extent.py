from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageFilter
p=Path(__file__).resolve().parents[1];e=p/'evidence';a=json.loads((e/'extent-diagnostic/ledger.json').read_text());records=[]
def rgba(x):return np.array(Image.open(p/x).convert('RGBA'))
for mode in a['modes']:
 for size in [128,32]:
  cases={x['settings']['control']:x for x in mode['cases'] if x['settings']['size']==size};im={k:rgba(v['raw']['path']) for k,v in cases.items()};css={k:rgba(v['screenshot']['path']) for k,v in cases.items()}
  for port in ['W','N']:
   base=Image.open(e/f'masks/N-{port}.png');mask=np.array(base.transform((898,1218),Image.Transform.AFFINE,(1,0,-2.5,0,1,-2.5),Image.Resampling.NEAREST))==255;mask&=np.array(Image.fromarray(im['native'][:,:,3]).filter(ImageFilter.MinFilter(3)))==255
   before=np.abs(im['native'][:,:,:3].astype(int)-im['individual'][:,:,:3].astype(int));after=np.abs(im['equal-extent-diagnostic'][:,:,:3].astype(int)-im['individual'][:,:,:3].astype(int));maxpos=np.unravel_index(np.argmax(np.max(before,axis=2)*mask),mask.shape)
   records.append({'mode':mode['name'],'size':size,'port':port,'samples':int(mask.sum()),'rawBeforeRGBMax':int(before[mask].max()),'rawAfterRGBMax':int(after[mask].max()),'rawAfterRGBMean':float(after[mask].mean()),'wholeBeforeRGBMax':int(before.max()),'wholeAfterRGBMax':int(after.max()),'rawAfterAlphaMax':int(np.abs(im['equal-extent-diagnostic'][:,:,3].astype(int)-im['individual'][:,:,3].astype(int)).max()),'worstRawPixel':[int(maxpos[1]),int(maxpos[0])],'worstNativeRGBA':im['native'][maxpos].tolist(),'worstIndividualRGBA':im['individual'][maxpos].tolist(),'worstDiagnosticRGBA':im['equal-extent-diagnostic'][maxpos].tolist()})
  if size==128:
   # Fixed registered N north-port inspection box; display-only2x nearest, no asset alteration.
   box=(100,125,290,235);sheet=Image.new('RGB',(1140,260),'#e7e4db');draw=ImageDraw.Draw(sheet)
   for i,control in enumerate(['native','individual','equal-extent-diagnostic']):
    crop=Image.open(p/cases[control]['screenshot']['path']).convert('RGB').crop(box).resize((380,220),Image.Resampling.NEAREST);sheet.paste(crop,(380*i,35));draw.text((380*i+5,8),mode['name']+' '+control,fill='#183a51')
   sheet.save(e/f'extent-diagnostic/{mode["name"]}-N-local.png')
summary={'scope':'Bounded worst actual Nphase3 comparison only; not production art or runtime change','records':records,'interpretation':'Only verified transparent padding extent and compensating exact integer origin differ. Raw actual observations are retained. Reduced comparison residual supports source-extent nearest sampling component; true rendered field/native profile/actual visible joins are assessed independently. No blanket seam/alpha/RGB waiver.'}
(e/'extent-diagnostic/analysis.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(records,indent=2))
