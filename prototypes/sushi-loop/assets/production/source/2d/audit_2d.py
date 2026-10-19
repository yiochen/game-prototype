"""Validate original cutouts and packed complete frames, independently of Blender."""
from pathlib import Path
import hashlib, json
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
objects=json.loads((HERE/'overrides.json').read_text())
report=[]
for ident,obj in objects.items():
    assert 'blend' not in obj['source'],ident
    if obj['source'].get('artwork'):
        source=ROOT/obj['source']['artwork']
        assert hashlib.sha256(source.read_bytes()).hexdigest()==obj['source']['sha256']
        im=Image.open(source)
        assert im.mode=='RGBA' and im.width>=1024 and im.height>=1024
        alpha_range=im.getchannel('A').getextrema()
        assert alpha_range[0]==0 and alpha_range[1]>=250
    count=0;minimum=99
    for clip in obj['clips']:
        assert clip['fps']==12
        for direction,entry in clip['directions'].items():
            atlas=Image.open(ROOT/entry['image'])
            assert list(atlas.size)==entry['atlasSize']
            hashes=[]
            for x,y,w,h in entry['rects']:
                assert (w,h)==tuple(v*2 for v in obj['frameSize'])
                frame=atlas.crop((x,y,x+w,y+h))
                bounds=frame.getchannel('A').getbbox()
                assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<w and bounds[3]<h,(ident,clip['id'],direction,bounds)
                hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
            unique=len(set(hashes))
            assert unique==entry['uniqueFrames']
            assert clip['frames']==1 or unique>=6,(ident,clip['id'],unique)
            minimum=min(minimum,unique);count+=len(hashes)
    report.append({'object':ident,'pipeline':obj['source']['pipeline'],'framesAcrossContexts':count,'minimumDistinctFramesPerClip':minimum})
out={'objects':len(report),'generatedRasterObjects':sum(o['source']['pipeline']=='imagegen-2d'for o in objects.values()),'procedural2dObjects':sum(o['source']['pipeline']=='procedural-2d'for o in objects.values()),'fullFrameScale':2,'objectsVerified':report}
(HERE/'audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
