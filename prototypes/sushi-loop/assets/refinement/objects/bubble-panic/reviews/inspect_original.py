from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, importlib.util, json
ROOT=Path(__file__).resolve().parents[5]
EXP=Path(__file__).resolve().parent.parent
PROD=ROOT/'assets/production'
# This file creates judge evidence only. It never publishes or changes source artwork.
SOURCE=PROD/'source/2d/generated/bubble-panic.png'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_publisher',EXP/'inputs/original-2d-pipeline/publish_2d.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=PROD/'source/2d'
obj=json.loads((EXP/'inputs/catalog-object.json').read_text())
report={'asset':'bubble-panic','pipeline':'existing-imagegen-2d','source':{'path':str(SOURCE.relative_to(ROOT)),'sha256':sha(SOURCE)},'publisher':{'path':'inputs/original-2d-pipeline/publish_2d.py','sha256':sha(EXP/'inputs/original-2d-pipeline/publish_2d.py')},'clips':[],'allPixelsMatch':True}
frames=[]
for clip in obj['clips']:
 entry=clip['directions']['S']; path=PROD/entry['image']; atlas=Image.open(path).convert('RGBA'); record={'clip':clip['id'],'frames':clip['frames'],'fps':clip['fps'],'loop':clip['loop'],'atlasPath':str(path.relative_to(ROOT)),'atlasSize':list(atlas.size),'sha256':sha(path),'aliasesIdentical':len({json.dumps(e,sort_keys=True) for e in clip['directions'].values()})==1,'directions':list(clip['directions']),'frameEvidence':[]}
 for i,rect in enumerate(entry['rects']):
  x,y,w,h=rect; frame=atlas.crop((x,y,x+w,y+h)); replay=module.generated_frame(obj,clip,i)
  match=frame.tobytes()==replay.tobytes();report['allPixelsMatch'] &= match
  a=frame.getchannel('A'); record['frameEvidence'].append({'index':i,'rect':rect,'mode':frame.mode,'alphaExtrema':list(a.getextrema()),'alphaBoundsGt8':a.point(lambda x:255 if x>8 else 0).getbbox(),'pixelSHA256':hashlib.sha256(frame.tobytes()).hexdigest(),'publisherReplayExact':match})
  frames.append((clip['id'],i,frame))
 record['uniqueFrames']=len({f['pixelSHA256'] for f in record['frameEvidence']});report['clips'].append(record)
report['uniqueRequiredFrames']=len(frames);report['logicalAliasSlots']=len(frames)*4
report['snapshotEqualsIdle0']=Image.open(EXP/'inputs/original.png').convert('RGBA').tobytes()==frames[12][2].tobytes()
for label,color in [('light','#fff8e8'),('gray','#888888'),('dark','#182c36')]:
 sheet=Image.new('RGB',(1200,1332),color);draw=ImageDraw.Draw(sheet)
 for n,(clip,i,frame) in enumerate(frames):
  x=n%6*200;y=n//6*222
  # Same fixed region across every source frame; no silhouette fit.
  panel=Image.new('RGBA',(192,192),color);panel.alpha_composite(frame.crop((96,296,288,488)))
  sheet.paste(panel.convert('RGB'),(x+4,y+22));draw.text((x+5,y+4),f'{clip} {i:02}',fill='white' if label=='dark' else '#111111')
 sheet.save(EXP/'reviews'/f'original-all36-{label}.png')
raw=Image.open(EXP/'inputs/target.png').convert('RGBA');bb=raw.getchannel('A').point(lambda x:255 if x>8 else 0).getbbox();cut=raw.crop(bb); normalized=cut.resize((164,round(cut.height/cut.width*164)),Image.Resampling.LANCZOS)
source=frames[12][2].crop((96,296,288,488))
baseTarget=Image.new('RGBA',(192,192));baseTarget.alpha_composite(normalized,(round(96-normalized.width/2),round(96-normalized.height/2)))
refsheet=Image.new('RGB',(960,660),'#888888');draw=ImageDraw.Draw(refsheet)
refs=[('original idle0',source),('target normalized for inspection only',baseTarget),('approved heart context',Image.open(EXP/'inputs/approved-feedback-family-heart.png').convert('RGBA').crop((96,296,288,488))),('approved smile context',Image.open(EXP/'inputs/approved-feedback-family-smile.png').convert('RGBA').crop((96,296,288,488)))]
for n,(name,im) in enumerate(refs):
 x=n*240;draw.text((x+4,4),name,fill='#111111');refsheet.paste(im.resize((384,384),Image.Resampling.NEAREST).convert('RGB'),(x+4,30)) if False else None
 panel=Image.new('RGBA',(192,192),'#888888');panel.alpha_composite(im);refsheet.paste(panel.convert('RGB'),(x+20,30))
 for j,(width,c) in enumerate([(82,'#fff8e8'),(36,'#888888'),(32,'#182c36')]):
  # Entire 192px physical review region corresponds to96logical px.
  scale=width/164;mini=im.resize((round(192*scale),round(192*scale)),Image.Resampling.LANCZOS)
  panel=Image.new('RGBA',(200,130),c);panel.alpha_composite(mini,(round(100-mini.width/2),round(65-mini.height/2)));refsheet.paste(panel.convert('RGB'),(x+20,240+j*136));draw.text((x+23,243+j*136),f'art width {width}px',fill='#eeeeee' if j==2 else '#111111')
refsheet.save(EXP/'reviews/reference-size-context.png')
report['referenceEvidence']={'targetRawSHA256':sha(EXP/'inputs/target.png'),'targetRawSize':list(raw.size),'targetAlphaBoundsGt8':bb,'inspectionNormalizedSize':list(normalized.size),'sourceArtNormalizationLogicalWidth':82,'normalizationRule':'one crop alpha>8, proportional width164 physical only; raw unchanged'}
(EXP/'reviews/original-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='clips'},indent=2))
for c in report['clips']:print(c['clip'],c['atlasSize'],c['uniqueFrames'],c['aliasesIdentical'])
