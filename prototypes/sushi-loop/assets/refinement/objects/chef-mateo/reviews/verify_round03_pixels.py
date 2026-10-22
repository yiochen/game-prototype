from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,subprocess,hashlib
B=Path(__file__).resolve().parent.parent;P=B/'candidates/round03';C=json.loads((B/'inputs/catalog-object.json').read_text());sheet=Image.open(P/'previews/all192-native-frames-logical.png').convert('RGB');report={'packetSHA256':hashlib.sha256((P/'packet.json').read_bytes()).hexdigest(),'atlasComparisons':[],'allFrameSheetComparisons':[],'videos':[]};row=0
for clip in C['clips']:
 videoSheet=Image.new('RGB',(2304,1376),'#b6bbc0');dr=ImageDraw.Draw(videoSheet)
 for direction,layout in clip['directions'].items():
  key=clip['id']+'-'+direction;atlas=Image.open(P/'atlases'/f'{key}.png').convert('RGBA');assert atlas.size==tuple(layout['atlasSize'])
  for i,rect in enumerate(layout['rects']):
   f=Image.open(P/'raw-frames'/key/f'{i:03}.png').convert('RGBA');x,y,w,h=rect;ok=f.tobytes()==atlas.crop((x,y,x+w,y+h)).tobytes();assert ok
   comp=Image.new('RGBA',(192,320),'#b6bbc0');comp.alpha_composite(f.resize((192,320),Image.Resampling.LANCZOS));ok2=comp.convert('RGB').tobytes()==sheet.crop((i*192,row*344+24,(i+1)*192,row*344+344)).tobytes();assert ok2
   report['atlasComparisons'].append({'clip':clip['id'],'direction':direction,'index':i,'exact':ok});report['allFrameSheetComparisons'].append({'clip':clip['id'],'direction':direction,'index':i,'exact':ok2})
  video=P/'previews'/f'{key}.mp4';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(video)]))['streams'][0];assert probe['r_frame_rate']=='12/1' and probe['nb_frames']=='12'
  rgb=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(video),'-f','rawvideo','-pix_fmt','rgb24','pipe:1']);assert len(rgb)==12*384*640*3
  for i in range(12):
   step=384*640*3;im=Image.frombytes('RGB',(384,640),rgb[i*step:(i+1)*step]);videoSheet.paste(im.resize((192,320),Image.Resampling.LANCZOS),(i*192,(row%4)*344+24));dr.text((i*192+6,(row%4)*344+6),key+' decoded '+str(i),fill='#18212b')
  report['videos'].append({'path':f'previews/{key}.mp4','decodedAllFrames':12,'probe':probe,'loop':clip['loop']});row+=1
 videoSheet.save(B/'reviews'/f'round03-decoded-videos-{clip["id"]}.png')
report['all192AtlasCellsExact']=all(x['exact'] for x in report['atlasComparisons']);report['all192SheetCellsExact']=all(x['exact'] for x in report['allFrameSheetComparisons']);(B/'reviews/round03-independent-pixel-evidence.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'atlasCells':len(report['atlasComparisons']),'all192AtlasCellsExact':report['all192AtlasCellsExact'],'all192SheetCellsExact':report['all192SheetCellsExact'],'decodedMP4s':len(report['videos'])}))
