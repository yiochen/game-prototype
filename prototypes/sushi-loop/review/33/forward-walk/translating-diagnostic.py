"""Verification only: move registered native frames at their declared walk speed.
No production assets are changed and no alpha fitting or phase reversal is used.
"""
import argparse,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--ids',nargs='+');args=parser.parse_args()
root=Path(__file__).resolve().parents[5]/'prototypes/sushi-loop/assets/production'
library=json.loads((root/'library.json').read_text());args.output.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
records=[];panel_w,panel_h=384,440
for obj in [o for o in library['objects'] if o['id'].startswith('customer-') and (not args.ids or o['id'] in args.ids)]:
 clip=next(c for c in obj['clips'] if c['id']=='walk');count,fps=clip['frames'],clip['fps']
 camera=json.loads((root/obj['source']['camera']).read_text());scale=camera['captureScale'];cal=camera['calibration']
 x_pitch=cal['unitX'][0]/scale;depth_pitch=cal['unitDepth'][1]/scale
 vectors={'N':(0,-depth_pitch),'E':(x_pitch,0),'S':(0,depth_pitch),'W':(-x_pitch,0)}
 names={'N':'North','E':'East','S':'South','W':'West'}
 atlases={direction:Image.open(root/clip['directions'][direction]['image']).convert('RGBA') for direction in names}
 frames=[]
 for tick in range(count*2):
  frame=tick%count;progress=tick/count;canvas=Image.new('RGBA',(panel_w*4,panel_h),'#f4f2e8');draw=ImageDraw.Draw(canvas)
  for index,direction in enumerate(names):
   left=index*panel_w
   for k in range(-3,5):
    x=left+panel_w/2+k*x_pitch;draw.line((x,50,x,panel_h-34),fill='#d7d9cb',width=1)
    y=310+k*depth_pitch;draw.line((left+10,y,left+panel_w-10,y),fill='#d7d9cb',width=1)
   draw.rectangle((left,0,left+panel_w-1,49),fill='#fffef9')
   draw.text((left+12,10),names[direction]+' · '+obj['name'],font=font,fill='#263e43')
   draw.text((left+12,30),f'Frame {frame+1}/{count} · {fps} fps · forward travel',font=small,fill='#586f6c')
   entry=clip['directions'][direction];fw,fh=entry.get('frameSize',clip.get('frameSize',obj['frameSize']));anchor=entry.get('root',clip.get('root',obj['root']));source_scale=entry.get('sourceScale',clip.get('sourceScale',obj['sourceScale']))
   rect=entry.get('rects',[None]*count)[frame]
   if rect is None:
    columns=entry.get('columns',count);rect=[frame%columns*fw*source_scale,frame//columns*fh*source_scale,fw*source_scale,fh*source_scale]
   x,y,w,h=rect;sprite=atlases[direction].crop((x,y,x+w,y+h)).resize((fw,fh),Image.Resampling.LANCZOS)
   vx,vy=vectors[direction];travel=.56*(progress-1)
   gx=left+panel_w/2+vx*travel;gy=310+vy*travel
   canvas.alpha_composite(sprite,(round(gx-anchor[0]),round(gy-anchor[1])))
   draw.text((left+12,panel_h-27),f'.56 world units/cycle · {clip["frames"]/fps:g}s/cycle',font=small,fill='#586f6c')
  frames.append(canvas.convert('RGB'))
 path=args.output/(obj['id']+'-walk-translating.gif')
 durations=[round((i+1)*1000/fps)-round(i*1000/fps) for i in range(len(frames))]
 frames[0].save(path,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2)
 frames[count//4].save(args.output/(obj['id']+'-walk-quarter.png'))
 records.append({'id':obj['id'],'sourceClip':clip['id'],'frames':count,'fps':fps,'cyclesShown':2,'strideWorldUnitsPerCycle':.56,'forwardWorldUnitsPerSecond':.56/(count/fps),'projectedPitch':[x_pitch,depth_pitch],'diagnostic':str(path)})
 print(path)
(args.output/'diagnostic.json').write_text(json.dumps({'purpose':'Verification-only translating native walk frames; fixed canvas/root; no alpha fitting or frame reversal. Native camera ground projection is used. Two cycles then reset.','objects':records},indent=2)+'\n')
