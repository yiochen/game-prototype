"""Frozen Godot native-grid/mip/presenter arithmetic on actual current-consumer RGBA.

This is a CPU arithmetic reference, not a claim of GPU/Canvas byte identity.
The actual Canvas consumer is separately exercised unchanged in consumer_capture.mjs.
"""
import sys, json, hashlib, math
from pathlib import Path
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
H=Path(__file__).resolve().parent; O=H.parent.parent
D=O/'candidates/round-02/native-present-reference'; D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def q8(a): return np.floor(np.clip(a,0,1)*255+.5).astype(np.uint8)
def mip_chain(image):
    h,w=image.shape[:2];aw=math.ceil((w+32-.001)/16)*16;ah=math.ceil((h+32-.001)/16)*16
    native=np.zeros((ah,aw,4),np.uint8)
    a=image.astype(np.float64)/255; a[:,:,:3]*=a[:,:,3:4]
    native[16:16+h,16:16+w]=q8(a); levels=[native]
    for i in range(4):
        a=levels[-1].astype(np.float64)/255
        levels.append(q8((a[::2,::2]+a[1::2,::2]+a[::2,1::2]+a[1::2,1::2])/4))
    return levels
def axis_weights(n,scale,level,shift):
    footprint=max(1/scale/2**level,1.0)
    low=((np.arange(n)+.5)/scale-shift+16)/2**level-footprint/2
    first=np.floor(low+1e-6).astype(int)
    ids=first[:,None]+np.arange(3)[None,:]
    weights=np.maximum(0,np.minimum(low[:,None]+footprint,ids+1)-np.maximum(low[:,None],ids))/footprint
    return ids,weights
def present(levels,dimensions,pitch,shift):
    scale=pitch/256;span=1/scale;level=max(0,min(4,math.floor(math.log2(max(span,1))+1e-6)))
    a=levels[level].astype(np.float64)/255
    w,h=[math.ceil(n*scale) for n in dimensions]
    xi,xw=axis_weights(w,scale,level,shift);yi,yw=axis_weights(h,scale,level,shift)
    # Exact separable evaluation of the frozen <=3x3 texel-overlap loops.
    temp=np.zeros((a.shape[0],w,4));out=np.zeros((h,w,4))
    for j in range(3):
        valid=(xi[:,j]>=0)&(xi[:,j]<a.shape[1]);temp[:,valid]+=a[:,xi[valid,j]]*xw[None,valid,j,None]
    for j in range(3):
        valid=(yi[:,j]>=0)&(yi[:,j]<a.shape[0]);out[valid]+=temp[yi[valid,j]]*yw[valid,j,None,None]
    return out,level
def composite(out,color):
    rgb=np.array([int(color[i:i+2],16)/255 for i in (1,3,5)])
    result=np.ones(out.shape);result[:,:,:3]=out[:,:,:3]+rgb[None,None,:]*(1-out[:,:,3:4])
    return q8(result)
def self_check():
    # A half-transparent red impulse must remain premultiplied through reduction.
    a=np.zeros((16,16,4),np.uint8);a[4:6,4:6]=[255,0,0,128]
    levels=mip_chain(a);sample=levels[1][10,10]
    assert tuple(sample)==(128,0,0,128), sample
    out,l=present(levels,[16,16],128,0)
    assert l==1 and np.max(np.abs(out[2,2]-np.array([128/255,0,0,128/255])))<1e-12
    assert np.all(out[:,:,:3]<=out[:,:,3:4]+1e-12)
    return {'halfTransparentRed2x2MeanRGBA8':sample.tolist(),'alphaMultipliedExactlyOnce':True,'exact2xLevel':l}
checks=self_check();ev=json.loads((O/'candidates/round-02/consumer/consumer-evidence.json').read_text())
records=[];examples=[]
for row in ev['nativeFrames']:
    if (row['clip'],row['index']) not in [('covered',0),('uncover',5),('uncover',11)]:continue
    image=np.array(Image.open(O/row['path']).convert('RGBA'));h,w=image.shape[:2];levels=mip_chain(image)
    assert all(np.all(a[:,:,:3].astype(int)<=a[:,:,3:4].astype(int)+1)for a in levels)
    for phase in (0,.25,.5,.75):
        for pan in (0,.25,.5,.75):
            for label,pitch in [('logical',128),('phone',390/7),('landscape',(390*9/16)/7)]:
                shift=(phase-pan)*2;out,level=present(levels,[w,h],pitch,shift)
                assert np.all(out[:,:,:3]<=out[:,:,3:4]+1e-12)
                r={'mode':row['mode'],'clip':row['clip'],'direction':row['direction'],'index':row['index'],'source':row['path'],'sourceSHA256':row['sha256'],'commonLogicalRootPhase':phase,'independentLogicalCameraPan':pan,'nativeGridFraction':[(shift%1),(shift%1)],'nativeUniformOffset':shift,'size':label,'pixelsPerCell':pitch,'dimensions':[out.shape[1],out.shape[0]],'mipLevel':level,'premultipliedRGBLeAlpha':True,'backgrounds':[]}
                for bg,color in [('light','#f5f2e9'),('gray','#777777'),('dark','#18252a')]:
                    a=composite(out,color);rr={'background':bg,'decodedRGBASHA256':hashlib.sha256(a.tobytes()).hexdigest()}
                    if row['mode']=='upgraded-dock-ready' and row['clip']=='uncover' and row['index']==11 and phase==.25 and pan==.5:
                        p=D/f'{row["direction"]}-{label}-{bg}.png';Image.fromarray(a).save(p);rr.update(path=str(p.relative_to(O)),sha256=sha(p));examples.append(p)
                    r['backgrounds'].append(rr)
                records.append(r)
    print('PRESENTER',row['mode'],row['clip'],row['direction'],row['index'],flush=True)
bound={n:sha(H/'resources/consumer'/n) for n in ('native_pixel_compositor.gd','native_world_layer.gd','native_reduce2.gdshader','native_present.gdshader')}
payload={'asset':'dock-cover','stage':'candidate evidence; independent review pending','sourceProjectSHA256':sha(H/'cover.blend'),'method':'Faithful float64 CPU reference of frozen native compositor allocation and presenter arithmetic, starting with exact actual570 consumer nativeCanvas RGBA. Premultiply once into RGBA8, guard16/alignment16, four quantized 2x2 area-mean mip levels; shader floor(log2(footprint)+1e-6), exact <=3x3 texel intersection weights, premultiplied background blending. Uniform common-root/camera fractions are removed from native-grid input and restored once in presentation. All objects retain their exact authored projections/relative roots. This isolates presenter arithmetic; it does not claim Godot GPU execution or cross-projection native scene RGB identity. Actual whole-canvas browser consumer evidence is separate.','frozenCodeSHA256':bound,'selfChecks':checks,'contexts':48,'presentationCases':len(records),'backgroundCases':len(records)*3,'records':records}
(D/'evidence.json').write_text(json.dumps(payload,indent=2)+'\n')
sheet=Image.new('RGB',(3*520,4*380),'#777777');dr=ImageDraw.Draw(sheet)
for y,d in enumerate('NESW'):
    for x,label in enumerate(('logical','phone','landscape')):
        im=Image.open(D/f'{d}-{label}-gray.png').convert('RGB');im.thumbnail((510,345));sheet.paste(im,(x*520+(520-im.width)//2,y*380+28));dr.text((x*520+10,y*380+7),f'{d} {label} / common .25 / camera .5',fill='white')
sheet.save(D/'presenter-sheet.png');print('COMPLETE',len(records),len(records)*3)
