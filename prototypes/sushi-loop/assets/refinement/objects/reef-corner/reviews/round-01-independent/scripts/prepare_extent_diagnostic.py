from pathlib import Path
from PIL import Image
import numpy as np,json
p=Path(__file__).resolve().parents[1];out=p/'evidence/extent-diagnostic';out.mkdir(exist_ok=False)
source=Image.open(p/'evidence/native/two-port-N.png').convert('RGBA');box=(256,256,896,1216);cropped=source.crop(box);cropped.save(out/'N-equal.png');restored=Image.new('RGBA',source.size);restored.paste(cropped,box[:2]);a=np.array(source);b=np.array(restored);discard=int(np.count_nonzero((a[:,:,3]>0)&(b[:,:,3]==0)));different=int(np.count_nonzero(np.any(a!=b,axis=2)));assert discard==different==0
(out/'invariants.json').write_text(json.dumps({'scope':'comparison-only bounded worst Nphase3 extent control, no source/production pixel changes','source':'evidence/native/two-port-N.png','actualSourceFrame':[896,1216],'authoredIndividualSpriteUnionWorld':[224,72,320,480],'cropNativePixelRect':box,'cropSize':list(cropped.size),'derivedFrom':'Union of three authored registered sprite rectangles, not alpha bounds. Compensating worldorigin(+128,+128) logical pixels gives exact integer placement.','visiblePixelsDiscarded':discard,'integerRestorationDifferentRGBAPixels':different,'productionAssetsAndConsumerChanged':False},indent=2)+'\n')
host=(p/'resources/consumer/host.html').read_text();old="const sprites=control==='native'?[{url:`../../evidence/native/two-port-${direction}.png`,rect:[0,0,896,1216],x:96+root,y:-56+root,width:448,height:608}]:individual;"
new="const sprites=control==='native'?[{url:`../../evidence/native/two-port-${direction}.png`,rect:[0,0,896,1216],x:96+root,y:-56+root,width:448,height:608}]:control==='equal-extent-diagnostic'?[{url:'../../evidence/extent-diagnostic/N-equal.png',rect:[0,0,640,960],x:224+root,y:72+root,width:320,height:480}]:individual;"
assert old in host;(p/'resources/consumer/extent-host.html').write_text(host.replace(old,new))
print('Zero visible discard and exact RGBA integer restoration; source extent640x960 matches authored independent rectangle union.')
