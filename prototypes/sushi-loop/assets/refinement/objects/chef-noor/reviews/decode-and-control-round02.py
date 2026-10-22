from pathlib import Path
from PIL import Image,ImageDraw
import json,subprocess,numpy as np
b=Path(__file__).resolve().parents[1];c=b/'candidates/round-02';out=b/'reviews';p=json.loads((c/'packet.json').read_text());r={'videos':[],'controls':[],'phoneExactCellMismatches':[]};contexts=Image.new('RGB',(1536,1472),'#f3eee2');dc=ImageDraw.Draw(contexts);contexti=0
for name,v in p['previews'].items():
 if not v['path'].endswith('.mp4'):continue
 f=c/v['path'];meta=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=width,height','-of','json',str(f)]))['streams'][0];w,h=meta['width'],meta['height'];raw=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(f),'-f','rawvideo','-pix_fmt','rgb24','-']);frames=np.frombuffer(raw,dtype=np.uint8).reshape((-1,h,w,3));assert len(frames)==12;rec={'path':v['path'],'decodedFrames':len(frames),'size':[w,h]}
 if v['path'].startswith('playbacks/'):
  ident=Path(v['path']).stem;errors=[]
  for i,fr in enumerate(frames):
   im=Image.open(c/'frames'/ident/f'{i:03d}.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#d1d0c7');bg.alpha_composite(im);errors.append(float(np.abs(fr.astype(float)-np.asarray(bg.convert('RGB')).astype(float)).mean()))
  rec['meanRGBErrorVsCorrespondingNativeComposite']=errors
 else:
  row=contexti;contexti+=1
  for i,fr in enumerate(frames):
   contexts.paste(Image.fromarray(fr).resize((128,160),Image.Resampling.LANCZOS),(i*128,row*184+24));dc.text((i*128+2,row*184+2),name+' '+str(i),fill='#29333b')
 r['videos'].append(rec)
contexts.save(out/'round02-decoded-serving-allframes.png')
control=json.loads((c/'native-replay-calibration.json').read_text());settings=json.loads((c/'source-fresh-replay-settings.json').read_text())
def im(p):return np.asarray(Image.open(p).convert('RGBA')).astype(int)
for clip,d,i in settings['controls']:
 stem=f'{clip}-{d}-{i:03d}';a=im(c/'controls/source'/f'{stem}-a.png');bb=im(c/'controls/source'/f'{stem}-b.png');cc=im(c/'controls/candidate'/f'{stem}-a.png');dd=im(c/'controls/candidate'/f'{stem}-b.png');ee=im(c/'controls/candidate-source-food-control'/f'{stem}-a.png');ff=im(c/'controls/candidate-source-food-control'/f'{stem}-b.png');r['controls'].append({'clip':clip,'direction':d,'index':i,'sourceRepeatMaxRGBA':np.abs(a-bb).max(axis=(0,1)).tolist(),'candidateRepeatMaxRGBA':np.abs(cc-dd).max(axis=(0,1)).tolist(),'restoredSourceRepeatMaxRGBA':np.abs(ee-ff).max(axis=(0,1)).tolist(),'sourceVsRestoredSourceMaxRGBA':np.abs(a-ee).max(axis=(0,1)).tolist(),'candidateVsDeliveredMaxRGBA':np.abs(cc-im(c/'frames'/f'{clip}-{d}'/f'{i:03d}.png')).max(axis=(0,1)).tolist(),'changedFoodActualFullFrameMaxRGBA':np.abs(a-cc).max(axis=(0,1)).tolist()})
for d in ['N','E','S','W']:
 phone=Image.open(c/'phone'/f'all24-source-canonical-{d}.png').convert('RGB')
 for ci,clip in enumerate(['hold','load']):
  for i in range(12):
   x=51+i%3*96;y=52+(ci*4+i//3)*96+16
   for vi,roundid in enumerate(['round-01','round-02']):
    rawim=Image.open(b/'candidates'/roundid/'frames'/f'{clip}-{d}'/f'{i:03d}.png').convert('RGBA').resize((48,80),Image.Resampling.LANCZOS);flat=Image.new('RGBA',rawim.size,'#f3eee2');flat.alpha_composite(rawim);cell=phone.crop((x+vi*48,y,x+(vi+1)*48,y+80))
    if cell.tobytes()!=flat.convert('RGB').tobytes():r['phoneExactCellMismatches'].append([clip,d,i,vi])
(out/'round02-video-controls-independent.json').write_text(json.dumps(r,indent=2)+'\n');print('decoded',len(r['videos']),'controls',len(r['controls']),'phoneCellMismatches',r['phoneExactCellMismatches'])
