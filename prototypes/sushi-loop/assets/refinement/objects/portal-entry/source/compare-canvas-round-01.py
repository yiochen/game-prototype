"""Measure read-back of actual compositor canvases; stdin bytes are ephemeral analysis input."""
from pathlib import Path
import json,sys,base64,io,hashlib
from PIL import Image,ImageChops,ImageStat
H=Path(__file__).resolve().parent.parent/'candidates/round-01'
records=json.load(sys.stdin);out=[]
for r in records:
    data=base64.b64decode(r['png'].split(',',1)[1]);im=Image.open(io.BytesIO(data)).convert('RGBA')
    p=H/'frames/enter'/r['direction']/f"{r['frame']:03d}.png";frame=Image.open(p).convert('RGBA')
    expected=Image.new('RGBA',im.size,(0,0,0,0));expected.paste(frame,(1,1))
    diff=ImageChops.difference(im,expected);mask=expected.getchannel('A').point(lambda a:255 if a==255 else 0)
    visible=expected.getchannel('A').point(lambda a:255 if a>0 else 0)
    od=ImageStat.Stat(diff,mask=mask);vd=ImageStat.Stat(diff,mask=visible)
    out.append({'direction':r['direction'],'frame':r['frame'],'canvasSize':list(im.size),'imageSmoothingEnabled':r['smoothing'],'plan':r['plan'],'actualDecodedRGBA_SHA256':hashlib.sha256(im.tobytes()).hexdigest(),'expectedDecodedRGBA_SHA256':hashlib.sha256(expected.tobytes()).hexdigest(),'sourceFrame':str(p.relative_to(H.parent.parent)),'reference':'Original published RGBA at integer1,1 in transparent386x770 shared canvas; no source modification. Browser read-back may quantize semi-transparent RGB.','decodedExact':im.tobytes()==expected.tobytes(),'maxRGBA':[x[1] for x in diff.getextrema()],'meanRGBAVisible':vd.mean,'opaqueMaxRGBA':od.extrema,'alphaExact':im.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),'nonzeroRGBAtAlphaZeroIgnoredForVisibleAssessment':True})
print(json.dumps(out))
