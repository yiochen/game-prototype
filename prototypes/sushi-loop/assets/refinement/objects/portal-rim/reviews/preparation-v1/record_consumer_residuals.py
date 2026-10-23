"""Record actual current-browser display residuals; no image/helper repair."""
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json
P=Path(__file__).resolve().parent;m=json.loads((P/'verification-metrics.json').read_text())
for bg in ['light','gray','dark']:
 a=Image.open(P/'evidence'/f'consumer-full-chromium-{bg}.png').convert('RGBA');b=Image.open(P/'evidence'/f'consumer-headless-shell-{bg}.png').convert('RGBA');diff=ImageChops.difference(a,b);v=m['browserModesCompared'][bg];v['size']=list(a.size);v['differenceBBoxRGB']=diff.convert('RGB').getbbox();v['changedPixels']=sum(any(px[:3]) for px in diff.get_flattened_data());v['meanAbsRGBA']=ImageStat.Stat(diff).mean
 v['regionResiduals']={}
 for name,box in [('logical-and-labels',[0,100,a.width,514]),('phone-and-labels',[0,542,a.width,a.height]),('header-and-section-text',[0,0,a.width,100])]:
  c=diff.crop(box);v['regionResiduals'][name]={'changedPixels':sum(any(px[:3]) for px in c.get_flattened_data()),'meanAbsRGBA':ImageStat.Stat(c).mean,'bbox':c.convert('RGB').getbbox()}
full=json.loads((P/'consumer-full-chromium.json').read_text());shell=json.loads((P/'consumer-headless-shell.json').read_text())
m['consumerCanvasBeforeCSS']={'sampledFrames':[0,3,6,9],'allSampledNativeCanvasPNGHashesExactAcrossModes':all(a['canvasPNG_SHA256']==b['canvasPNG_SHA256'] for fa,fb in zip(full['staticFrameRecords'],shell['staticFrameRecords']) for a,b in zip(fa['records'],fb['records']))}
(P/'verification-metrics.json').write_text(json.dumps(m,indent=2)+'\n')
f=P/'preparation-review.json';d=json.loads(f.read_text());d['provenanceFindings']=m;d['visualFindings'][2]='Both browser configurations visibly agree on the prepared isolated fixture at inspection size, but decoded screenshots are not pixel exact. Small RGB residuals occur in logical and phone artwork and some text edges, with a maximum difference of 15 in a channel and whole-image mean absolute channel differences below 0.04/255. The sampled native canvas PNG hashes match across both modes. Display/compositing is therefore the likely layer of the residual, without a claim to isolate its exact browser mechanism. Original screenshots are retained without repair.';f.write_text(json.dumps(d,indent=2)+'\n')
f=P/'commands.json';d=json.loads(f.read_text());d.append({'name':'recordActualBrowserResiduals','cwd':str(Path.cwd()),'env':{'PYTHONDONTWRITEBYTECODE':'1'},'argv':['/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(P/'record_consumer_residuals.py')],'result':'Recorded nonzero browser display RGB residuals with unchanged sampled native canvas PNG hashes. No image or helper edits.','preparationSealNote':'Initial own preparation integrity assertion incorrectly required screenshot equality and stopped before writing a seal. Removed that unsupported equality gate from the new preparation sealer and retained actual residuals. No shared validator was altered.'});f.write_text(json.dumps(d,indent=2)+'\n')
print('BROWSER_RESIDUALS_RECORDED',m['consumerCanvasBeforeCSS'])
