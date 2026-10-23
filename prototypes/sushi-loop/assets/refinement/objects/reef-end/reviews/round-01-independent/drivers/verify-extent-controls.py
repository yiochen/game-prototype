import sys
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageChops
import json
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01';records=[]
for backend in ['full-chromium','headless-shell']:
 report=json.loads((C/'extent-diagnostic'/(backend+'-results.json')).read_text())
 for r in report['controls']:
  full=Image.open(C/'native/contexts'/(r['kind']+'-'+r['d']+'.png')).convert('RGBA');cropped=Image.open(O/r['cropPath']).convert('RGBA');p=r['crop'];box=(p['x'],p['y'],p['x']+p['width'],p['y']+p['height']);assert cropped.size==(p['width'],p['height'])
  expected=full.crop(box);assert all(ch.getbbox() is None for ch in ImageChops.difference(cropped,expected).split())
  discarded=full.getchannel('A').copy();discarded.paste(0,box);visible=sum(x>0 for x in discarded.getdata());assert visible==0
  restored=Image.new('RGBA',full.size);restored.paste(cropped,(p['x'],p['y']));difference=ImageChops.difference(full,restored);assert all(ch.getbbox() is None for ch in difference.split())
  records.append({'backend':backend,'kind':r['kind'],'direction':r['d'],'crop':p,'sourceCropExact':True,'visiblePixelsDiscarded':visible,'integerRestorationRGBAExact':True,'diagnosticSource':r['cropPath']})
assert len(records)==16
(B/'evidence/independent-extent-control-findings.json').write_text(json.dumps({'candidatePacketSHA256':'48e08fc7f305a01eb9855350ad4a39c5487bf69da8024d832bae2d4eec8140f3','controls':records,'scope':'Comparison-only source-extent diagnostic source crops verified independently against raw native sources. All visible pixels retained, exact integer RGBA restoration. This is not a runtime crop, framing change, alpha/RGB repair, local seam waiver or family approval.'},indent=2)+'\n')
print('16 controls:0 visible pixels discarded; exact integerRGBA restoration; comparison only')
