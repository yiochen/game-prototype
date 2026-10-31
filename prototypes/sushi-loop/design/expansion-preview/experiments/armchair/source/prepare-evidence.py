"""Produce inspection sheets and exact HTML consumer harness from native PNGs."""
import pathlib,json,sys,argparse,hashlib,shutil
from PIL import Image,ImageDraw
P=pathlib.Path(__file__).resolve().parent;EXP=P.parent;PREVIEW=EXP.parents[1]
a=argparse.ArgumentParser();a.add_argument('--round',required=True);arg=a.parse_args();OUT=EXP/'candidates'/arg.round
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
audit=json.loads((OUT/'readback-audit.json').read_text());frames={d:Image.open(OUT/(d+'.png')).convert('RGBA') for d in ['N','E','S','W']};bounds={d:list(im.getbbox()) for d,im in frames.items()};union=[min(b[i] for b in bounds.values()) if i<2 else max(b[i] for b in bounds.values()) for i in range(4)]
common=[union[0]-10,union[1]-10,union[2]+10,union[3]+10]
tilew=common[2]-common[0]+32;tileh=common[3]-common[1]+35;sheet=Image.new('RGB',(tilew*4,tileh*3),'#eee4cd');draw=ImageDraw.Draw(sheet)
for row,bg in enumerate(['#eee4cd','#888888','#242526']):
    draw.rectangle((0,row*tileh,sheet.width,(row+1)*tileh),fill=bg)
    for col,(d,im) in enumerate(frames.items()):
        crop=im.crop(common);sheet.paste(crop,(col*tilew+16,row*tileh+28),crop);draw.text((col*tilew+16,row*tileh+8),d+' · native 1:1 crop',fill='white' if row else '#382718')
sheet.save(OUT/'four-view-sheet.png')
# Pin only the context resources actually used by the consumer harness.
res=P/'resources';res.mkdir(exist_ok=True);reg=json.loads((PREVIEW/'world-registration.json').read_text());context={}
for name in ['barrel-wood','crate-wood','plant-angular']:
    original=PREVIEW/'assets'/(name+'.png');dest=res/(name+'.png')
    if not dest.exists():shutil.copyfile(original,dest)
    context[name]={**reg[name],'src':str(pathlib.Path('../../source/resources')/(name+'.png')),'sha256':sha(dest)}
native={d:{'src':d+'.png','frame_size':[448,576],'root':[224,352],'visible_bounds':[bounds[d][0],bounds[d][1],bounds[d][2]-bounds[d][0],bounds[d][3]-bounds[d][1]],'sha256':sha(OUT/(d+'.png'))} for d in frames}
write(OUT/'consumer-settings.json',{'phone':[390,844],'columns':7,'cellPx':390/7,'logicalCell':128,'root':[224,352],'spriteFormulaSource':'expansion-preview/app.jsx Sprite; native frame/sourceScale retained','consumerFit':'ObjectPreview SVG viewBox equals measured alpha xywh, preserveAspectRatio xMidYMid meet','native':native,'context':context})
html='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
*{box-sizing:border-box}body{margin:0;width:390px;background:#f1e6ca;color:#453327;font:13px system-ui}header{height:54px;padding:10px 15px;background:#715239;color:#fff6db}h1{font-size:16px;margin:0 0 3px}p{margin:0}.board{position:relative;overflow:hidden;width:390px;height:390px;background-color:#c6b493;background-image:linear-gradient(#a99a8060 1px,transparent 1px),linear-gradient(90deg,#a99a8060 1px,transparent 1px);background-size:55.714285714px 55.714285714px}.sprite{position:absolute;pointer-events:none}.selected{filter:drop-shadow(0 0 2px #ffeabb) drop-shadow(0 0 4px #deae3e)}.fading{opacity:.4}label{position:absolute;z-index:400;font-weight:700;color:#fff;background:#5b4837b0;border-radius:4px;padding:1px 4px}.cards{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px}.card{height:285px;border:1px solid #b69462;border-radius:14px;background:#f9eed3;padding:12px;text-align:center}.fit{display:block;width:100%;height:190px;margin:6px 0 12px}button{background:#8c5835;color:#fff8e5;border:0;border-radius:8px;padding:8px 12px;font-weight:bold}.note{padding:0 16px;font-size:11px;line-height:1.45}
</style><header><h1>Mustard armchair · native consumer</h1><p>Seven cells across · 390px phone</p></header><div class="board"></div><div class="cards"><section class="card"><b>Clear this patch?</b><svg class="fit" id="clear"></svg><button>Clear 90 ★</button></section><section class="card"><b>Shared components</b><svg class="fit" id="gallery"></svg><span>Same native image · uniform fit</span></section></div><p class="note">World sprites use the fixed registered root and source scale. Selected glow and fade are consumer CSS. Native frames are unmodified transparent PNGs.</p><script>
const data=DATA;const board=document.querySelector('.board');const cell=390/7;
function sprite(r,x,y,cls=''){let im=new Image;im.className='sprite '+cls;im.src=r.src;Object.assign(im.style,{left:(x-r.root[0]/128)*cell+'px',top:(y-r.root[1]/128)*cell+'px',width:r.frame_size[0]/128*cell+'px',zIndex:Math.round(y*10)});board.append(im)}
const chairs=[['N',1.5,2.5,''],['E',4.5,2.5,''],['S',2.5,5.5,'selected'],['W',5.5,5.5,''],['S',.5,6.5,'fading']];
for(let row=1;row<7;row++)for(let col=0;col<7;col++){if((row+col)%3===0&&!chairs.some(([,x,y])=>Math.abs(col+.5-x)<.6&&Math.abs(row+.5-y)<1.6)){let key=['barrel-wood','crate-wood','plant-angular'][(row*7+col)%3];sprite(data.context[key],col+.5,row+.5)}}
for(const [v,x,y,cls] of chairs){sprite(data.native[v],x,y,cls);const lab=document.createElement('label');lab.textContent=v;lab.style.left=(x-.15)*cell+'px';lab.style.top=(y+.35)*cell+'px';board.append(lab)}
for(const id of ['clear','gallery']){const r=data.native.S,svg=document.getElementById(id);svg.setAttribute('viewBox',r.visible_bounds.join(' '));svg.setAttribute('preserveAspectRatio','xMidYMid meet');svg.innerHTML='<image href="'+r.src+'" width="896" height="1152"/>'}
window.evidenceReady=Promise.all([...document.images].map(i=>i.decode()));
</script>'''.replace('DATA',json.dumps({'native':native,'context':context}))
(OUT/'consumer.html').write_text(html)
replay=Image.open(OUT/'replay-S.png').convert('RGBA');checks={**audit['checks'],'fourExactNativeDimensions':all(im.size==(896,1152) for im in frames.values()),'unclippedAlpha':all(b[0]>0 and b[1]>0 and b[2]<896 and b[3]<1152 for b in bounds.values()),'freshReopenPixelsIdentical':replay.tobytes()==frames['S'].tobytes()}
validation={'asset':'garbage-armchair','round':arg.round,'technicalChecks':checks,'allTechnicalChecksPassed':all(checks.values()),'nativeBounds':audit['nativeBounds'],'nativeRoot':[448,704],'logicalRoot':[224,352],'logicalFrame':[448,576],'nativeFrame':[896,1152],'sourceScale':2,'calibration':audit['calibration'],'maxProjectionErrorPx':audit['maxProjectionErrorPx'],'alphaBoundsXYXY':bounds,'nativeEvidence':'readback-audit.json','consumerSettings':'consumer-settings.json','scope':'Four static native facings and HTML consumers; native animation deferred','originalSHA256':sha(EXP/'backups/original.blend'),'projectSHA256':sha(P/(arg.round+'.blend')),'recipe':'source/recipe-'+arg.round+'.py','reviewStatus':'Independent judgement pending; no editor self-approval'}
write(OUT/'validation.json',validation);print(json.dumps(checks,indent=2))
