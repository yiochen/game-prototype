import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dependencies/python-library'))
from PIL import Image,ImageChops,ImageStat,ImageDraw
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;BASE=RES.parent;OUT=BASE.parent/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
proof=[]
for d in 'NESW':
 src=OUT/f'native/static/{d}/000.png';im=Image.open(src).convert('RGBA');out=OUT/f'frames/static/{d}/000.png';out.parent.mkdir(parents=True,exist_ok=True);im.resize((384,704),Image.Resampling.BOX).save(out);atlas=OUT/f'atlases/static-{d}.png';atlas.parent.mkdir(parents=True,exist_ok=True);atlas.write_bytes(out.read_bytes());recap=Image.open(OUT/f'evidence/recapture/native-{d}.png').convert('RGBA');proof.append({'direction':d,'nativeSHA256':sha(src),'publishedSHA256':sha(out),'nativeFrame':list(im.size),'publishedFrame':[384,704],'wholeFrameBOX':True,'savedSourceReplayRGBAExact':im.tobytes()==recap.tobytes(),'alphaBoundsNative':im.getchannel('A').getbbox(),'alphaBoundsPublished':Image.open(out).getchannel('A').getbbox()})
for d in 'NESW':
 src=OUT/f'evidence/canonical/native-{d}.png';Image.open(src).resize((384,704),Image.Resampling.BOX).save(OUT/f'evidence/canonical/published-{d}.png')
 for fixture in ['L','W','N']:
  src=OUT/f'evidence/family/native-{fixture}-{d}.png';Image.open(src).resize((896,1216),Image.Resampling.BOX).save(OUT/f'evidence/family/published-{fixture}-{d}.png')
dump(OUT/'publication-proof.json',{'method':'Complete native4x to published2x BOX. No fitting, repair, shifting or recolor.','frames':proof})
cap=[]
for p in ['W','N']:
 for kind in ['albedo','normal']:
  a=Image.open(OUT/f'evidence/cap-fields/{p}-reference-{kind}.png').convert('RGBA');b=Image.open(OUT/f'evidence/cap-fields/{p}-candidate-{kind}.png').convert('RGBA');diff=ImageChops.difference(a,b);mask=a.getchannel('A');masked=Image.new('RGBA',a.size);masked.paste(diff,mask=mask);cap.append({'port':p,'field':kind,'maxChannelDiff':diff.getextrema(),'meanChannelDiff':ImageStat.Stat(diff,mask).mean,'alphaExact':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'decodedRGBAExact':a.tobytes()==b.tobytes()})
dump(OUT/'cap-field-results.json',{'method':'Actual saved-candidate and exact canonical planar cap materials rendered as emission albedo and actual bump-normal field. N candidate is native Rz-90 for direct comparison to canonical E; its shader Object.Y input is -cornerLocalX. No image repair.','results':cap})
# Native four-view sheet, all full registered frames.
sheet=Image.new('RGBA',(768*4,1408),(0,0,0,0))
for i,d in enumerate('NESW'):sheet.alpha_composite(Image.open(OUT/f'native/static/{d}/000.png').convert('RGBA'),(768*i,0))
sheet.save(OUT/'four-view-native.png')
# Full logical and phone views, every background; one fixed registration.
bgs=['#eef2ed','#909090','#172539'];sheet=Image.new('RGB',(768,3*(352+88+24)),bgs[0]);draw=ImageDraw.Draw(sheet)
for r,bg in enumerate(bgs):
 y=r*464;draw.rectangle((0,y,767,y+463),fill=bg)
 for i,d in enumerate('NESW'):
  im=Image.open(OUT/f'frames/static/{d}/000.png').convert('RGBA');lg=im.resize((192,352),Image.Resampling.BOX);ph=im.resize((48,88),Image.Resampling.BOX);sheet.paste(lg,(i*192,y+16),lg);sheet.paste(ph,(i*192+72,y+372),ph);draw.text((i*192+8,y+3),d,fill='white' if r==2 else '#172539')
sheet.save(OUT/'single-use-sizes.png')
# Field sheet renders actual output, side by side, visually inspectable.
sheet=Image.new('RGB',(1024,1024),'#909090')
for r,p in enumerate(['W','N']):
 for c,role in enumerate(['reference','candidate']):
  im=Image.open(OUT/f'evidence/cap-fields/{p}-{role}-albedo.png').convert('RGBA');sheet.paste(im,(c*512,r*512),im)
sheet.save(OUT/'cap-field-sheet.png')
print('PUBLICATION',all(x['savedSourceReplayRGBAExact'] for x in proof),'CAP',cap)
