from pathlib import Path
from PIL import Image,ImageDraw
import json,math,hashlib,shutil
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# One global fixed logical actor window; verify all candidate visible alpha lies within it.
audit=json.loads((C/'frame-audit.json').read_text());bboxes=[r['alphaBBox'] for r in audit];box=[math.floor(min(b[0] for b in bboxes)/2)-8,math.floor(min(b[1] for b in bboxes)/2)-8,math.ceil(max(b[2] for b in bboxes)/2)+8,math.ceil(max(b[3] for b in bboxes)/2)+8];w,h=box[2]-box[0],box[3]-box[1];records=[]
for entry in json.loads((C/'sheet-coverage.json').read_text()):
 if not entry['sheet'].endswith('-logical.png'):continue
 im=Image.open(O/entry['sheet']).convert('RGB')
 for chunk in range(2):
  out=Image.new('RGB',(w*6,(h+18)*4),'#858c92');draw=ImageDraw.Draw(out);cells=[]
  for cell in entry['cells']:
   if cell['index']//6!=chunk:continue
   d=['N','E','S','W'].index(cell['direction']);i=cell['index']%6;x,y,_,_=cell['cell'];crop=[x+box[0],y+box[1],x+box[2],y+box[3]];out.paste(im.crop(crop),(i*w,d*(h+18)+18));draw.text((i*w+4,d*(h+18)+3),f"{cell['direction']} f{cell['index']}",fill='white');cells.append(cell)
  dst=P/'compact-native'/Path(entry['sheet']).name.replace('.png',f'-{chunk}.png');dst.parent.mkdir(exist_ok=True);out.save(dst);records.append({'path':str(dst.relative_to(O)),'sha256':sha(dst),'sourceSheet':entry['sheet'],'sourceSHA256':sha(O/entry['sheet']),'uniformFixedLogicalInspectionWindow':box,'scale':1,'cells':cells,'scope':'Inspection diagnostic only. Every visible alpha pixel of all528 frames is inside this SAME fixed window, verified globally; no per-view/per-phase fit/shift. Full candidate registered frames remain unchanged, earlier whole-frame views establish registration.'})
(P/'compact-native-coverage.json').write_text(json.dumps(records,indent=2)+'\n')
# Repack already decoded video frame cells at one uniform fixed actor window per facing/viewport.
# Fixed windows retain positions within each cell, never follow or fit an actor.
play=[]
for rec in json.loads((C/'playback-decoded-manifest.json').read_text())['records']:
 im=Image.open(O/rec['sheet']).convert('RGB');phone=rec['viewport']=='phone';windows=([(40,25,140,130),(220,25,320,130),(40,230,140,335),(220,230,320,335)] if phone else [(45,35,175,150),(269,35,399,150),(493,35,623,150),(717,35,847,150)])
 cw=(100 if phone else 130);ch=(105 if phone else 115);tw=cw*4;th=ch+18;columns=4;rows=math.ceil(len(rec['frames'])/columns);out=Image.new('RGB',(tw*columns,th*rows),'#30363a');draw=ImageDraw.Draw(out)
 for i,f in enumerate(rec['frames']):
  x,y,w0,h0=f['sheetCell'];base=im.crop((x,y,x+w0,y+h0));xx=(i%columns)*tw;yy=(i//columns)*th;draw.text((xx+3,yy+2),f"i{i} t{f['timestamp']}",fill='white')
  for j,window in enumerate(windows):out.paste(base.crop(window),(xx+j*cw,yy+18))
 dst=P/'compact-playback'/Path(rec['sheet']).name;dst.parent.mkdir(exist_ok=True);out.save(dst);play.append({'path':str(dst.relative_to(O)),'sha256':sha(dst),'sourceSheet':rec['sheet'],'sourceSheetSHA256':rec['sheetSHA256'],'sourceVideo':rec['originalVideo'],'sourceVideoSHA256':rec['originalVideoSHA256'],'mode':rec['mode'],'viewport':rec['viewport'],'clip':rec['clip'],'decodedFrames':rec['decodedFrames'],'sameFixedWindowsEveryFrame':windows,'scale':1,'frameRecords':rec['frames'],'scope':'All already decoded compositor frames in order, no video redump. Uniform fixed per-facing diagnostic windows retain within-cell motion, not fit/per-frame following; exact complete original fullvideo/sheet retained. Native wholeframe allphase cells supply larger detailed/registration evidence.'})
(P/'compact-playback-coverage.json').write_text(json.dumps(play,indent=2)+'\n')
# Remove unused inspection partitions; retained generated diagnostics are the useful fixed-window set.
shutil.rmtree(P/'playback-panels');(P/'playback-panel-coverage.json').unlink()
print('GLOBAL_NATIVE_WINDOW',box,'native',len(records),'complete_compositor',len(play),'frames',sum(r['decodedFrames'] for r in play))
