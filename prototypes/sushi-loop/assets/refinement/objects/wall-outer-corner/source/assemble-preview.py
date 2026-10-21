import json,sys,hashlib,shutil,math
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[1];ROUND=sys.argv[1]if len(sys.argv)>1 else'round-02';C=B/'candidates'/ROUND;F=B.parent/'wall-middle';FC=F/'candidates/round-06'
for d in('previews','sprite-joins','atlases'):(C/d).mkdir(exist_ok=True)
P=C/'previews';previews={}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
angles={'N':180,'E':90,'S':0,'W':-90};angleNames={0:'S',90:'E',180:'N',270:'W'}
frames={d:Image.open(C/'raw'/f'static-{d}-0000.png').convert('RGBA')for d in angles}
straight={d:Image.open(FC/'raw'/f'static-{d}-0000.png').convert('RGBA')for d in angles}
backgrounds={'light':(242,238,228),'gray':(122,126,132),'dark':(24,29,39)}
def backing(im,bg):
 b=Image.new('RGBA',im.size,bg+(255,));b.alpha_composite(im);return b.convert('RGB')
def save(im,name):
 path=P/(name+'.png');im.save(path);previews[name]=str(path.relative_to(B))
def row_sheet(size,bg):return Image.new('RGB',size,bg)
sheet=row_sheet((768,1140),(255,255,255));draw=ImageDraw.Draw(sheet)
for row,(name,bg)in enumerate(backgrounds.items()):
 for col,d in enumerate(angles):
  sheet.paste(backing(frames[d],bg).resize((192,352),Image.Resampling.LANCZOS),(col*192,row*380+28));draw.text((col*192+10,row*380+8),d+' / '+name,fill='black')
save(sheet,'four-view-logical-backgrounds')
sheet=row_sheet((1536,732),backgrounds['gray']);draw=ImageDraw.Draw(sheet)
for col,d in enumerate(angles):
 sheet.paste(backing(frames[d],backgrounds['gray']),(col*384,28));draw.text((col*384+10,8),d,fill='white')
save(sheet,'four-view-sheet')
metrics={};placements={};nativePaths={};indPaths={};repeatImages=[]
for d,deg in angles.items():
 shutil.copy2(C/'raw'/f'static-{d}-0000.png',C/'atlases'/f'static-{d}.png')
 rad=math.radians(deg)
 def project(x,y):return(round(256*(math.cos(rad)*x-math.sin(rad)*y)),round(-256*(math.sin(rad)*x+math.cos(rad)*y)))
 portPixels={}
 for port,(x,y)in{'W':(-.5,0),'S':(0,-.5)}.items():
  dx,dy=project(x,y);portPixels[port]=(448+dx,768+dy)
 for ports in [('W',),('S',),('W','S')]:
  key=d+'-'+''.join(ports);native=Image.open(C/'native-joins'/f'static-{key}.png').convert('RGBA');assembled=Image.new('RGBA',native.size)
  items=[{'asset':'wall-outer-corner','direction':d,'frame':frames[d],'origin':(256,256),'localPosition':[0,0,0]}]
  for port in ports:
   xy=(-1,0)if port=='W'else(0,-1);dx,dy=project(*xy);sd=angleNames[(deg+(0 if port=='W'else 90))%360]
   items.append({'asset':'wall-middle','direction':sd,'frame':straight[sd],'origin':(256+dx,256+dy),'localPosition':[*xy,0]})
  items.sort(key=lambda a:a['origin'][1])
  for item in items:assembled.alpha_composite(item['frame'],item['origin'])
  ap=C/'sprite-joins'/f'static-{key}.png';assembled.save(ap)
  placements[key]=[{k:(list(v)if isinstance(v,tuple)else v)for k,v in item.items()if k!='frame'}for item in items]
  nativePaths[key]=str((C/'native-joins'/f'static-{key}.png').relative_to(B));indPaths[key]=str(ap.relative_to(B))
  a=np.asarray(native).astype(float);b=np.asarray(assembled).astype(float);union=(a[:,:,3]>0)|(b[:,:,3]>0);opaque=(a[:,:,3]>250)&(b[:,:,3]>250);rgb=np.abs(a[:,:,:3]-b[:,:,:3]);alpha=np.abs(a[:,:,3]-b[:,:,3])
  m={'alphaMaxDelta':float(alpha.max()),'alphaMeanDeltaOnUnion':float(alpha[union].mean()),'opaqueRGBMeanDelta':float(rgb[opaque].mean()),'opaqueRGBP99Delta':float(np.percentile(rgb[opaque],99)),'opaqueRGBMaxDelta':float(rgb[opaque].max()),'pixelsOpaqueRGBDeltaOver10':int((rgb.max(axis=2)[opaque]>10).sum()),'unionPixels':int(union.sum()),'portStrips':{}}
  compare=row_sheet((896,1920),backgrounds['light']);draw=ImageDraw.Draw(compare)
  for row,(name,bg)in enumerate(backgrounds.items()):
   for col,(title,img)in enumerate([('Native join',native),('Independent RGBA',assembled)]):
    compare.paste(backing(img,bg).resize((448,608),Image.Resampling.LANCZOS),(col*448,row*640+28));draw.text((col*448+8,row*640+8),key+' / '+title+' / '+name,fill='black')
  save(compare,f'join-{key}-logical-backgrounds')
  # W/S cut spans exact width and full wall height. Crops are diagnostic surfaces only.
  crops=[]
  for port in ports:
   px,py=portPixels[port];outward=project(*({'W':(-1,0),'S':(0,-1)}[port]))
   vertical=abs(outward[0])>abs(outward[1]);box=(px-18,py-240,px+18,py+48)if vertical else(px-64,py-240,px+64,py+48)
   l,t,r,bottom=box;aa=a[t:bottom,l:r];bb=b[t:bottom,l:r];mask=(aa[:,:,3]>0)|(bb[:,:,3]>0);op=(aa[:,:,3]>250)&(bb[:,:,3]>250);dd=np.abs(aa[:,:,:3]-bb[:,:,:3]);ad=np.abs(aa[:,:,3]-bb[:,:,3])
   m['portStrips'][port]={'box':list(box),'alphaMaxDelta':float(ad.max()),'alphaMeanDeltaOnUnion':float(ad[mask].mean())if mask.any()else 0,'opaqueRGBMeanDelta':float(dd[op].mean())if op.any()else 0,'opaqueRGBP99Delta':float(np.percentile(dd[op],99))if op.any()else 0,'opaqueRGBMaxDelta':float(dd[op].max())if op.any()else 0,'opaquePixelsDeltaOver10':int((dd.max(axis=2)[op]>10).sum())}
   crop=row_sheet((max(768,4*(r-l)*2),640),backgrounds['gray']);draw=ImageDraw.Draw(crop)
   for col,(title,img)in enumerate([('Native RGB',backing(native,backgrounds['gray'])),('Independent RGB',backing(assembled,backgrounds['gray'])),('Native alpha',native.getchannel('A').convert('RGB')),('Independent alpha',assembled.getchannel('A').convert('RGB'))]):
    cr=img.crop(box).resize(((r-l)*2,(bottom-t)*2),Image.Resampling.NEAREST);crop.paste(cr,(col*crop.width//4,36));draw.text((col*crop.width//4+4,10),title,fill='white')
   save(crop,f'join-{key}-{port}-RGB-alpha-enlarged')
  metrics[key]=m
  diff=np.zeros(a.shape,dtype=np.uint8);diff[:,:,:3]=np.clip(rgb*8,0,255);diff[:,:,3]=union*255;save(Image.fromarray(diff),f'join-{key}-RGB-difference-x8')
  if len(ports)==2:
   # Compact combined real-method evidence at logical scale for every facing.
   rep=row_sheet((896,640),backgrounds['gray']);draw=ImageDraw.Draw(rep)
   for col,(title,img)in enumerate([('Native W/S joins',native),('Independent W/S joins',assembled)]):
    rep.paste(backing(img,backgrounds['gray']).resize((448,608),Image.Resampling.LANCZOS),(col*448,28));draw.text((col*448+8,8),d+' / '+title,fill='white')
   repeatImages.append(rep)
repeat=row_sheet((896,2560),backgrounds['gray'])
for i,im in enumerate(repeatImages):repeat.paste(im,(0,i*640))
save(repeat,'repeated')
# Intended-size actual alpha visibility audit.
frameAudit={}
for d,im in frames.items():
 aa=np.asarray(im)[:,:,3];ys,xs=np.nonzero(aa)
 frameAudit[d]={'size':list(im.size),'mode':im.mode,'alphaBounds':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'edgeAlphaPixels':int(np.count_nonzero(aa[0,:])+np.count_nonzero(aa[-1,:])+np.count_nonzero(aa[:,0])+np.count_nonzero(aa[:,-1])),'transparentPixels':int(np.count_nonzero(aa==0)),'softAlphaPixels':int(np.count_nonzero((aa>0)&(aa<255)))}
av={'method':'Exact native registered roots at 256px/world-unit; depth-order alpha-over compositing unchanged independent corner and approved wall-middle RGBA frames. No fitting, recolor, alpha repair, extension or pixel correction.','canvas':[896,1216],'root':[448,768],'frame':[384,704],'pitch':256,'placements':placements,'native':nativePaths,'independent':indPaths,'nativeIndependentComparison':metrics,'toleranceDisclosure':'Separate antialiasing and stochastic native irradiance produce numerical differences. Reported full-frame and W/S port-strip RGB/alpha deltas are evidence for the independent judge; no numeric threshold is an appearance verdict.','frames':frameAudit}
(C/'assembly-validation.json').write_text(json.dumps(av,indent=2));(C/'previews-map.json').write_text(json.dumps(previews,indent=2))
v=json.loads((C/'validation.json').read_text());v['assemblyAudit']='candidates/'+ROUND+'/assembly-validation.json';v['frameAudit']=frameAudit;(C/'validation.json').write_text(json.dumps(v,indent=2))
resources=[{'name':'approved-family-settings','path':'inputs/family-settings.json','sha256':sha(B/'inputs/family-settings.json')},{'name':'approved-straight-project','path':'../wall-middle/source/round-06.blend','sha256':sha(F/'source/round-06.blend')},{'name':'approved-straight-recipe','path':'../wall-middle/source/round-06.py','sha256':sha(F/'source/round-06.py')},{'name':'assembly-validation','path':str((C/'assembly-validation.json').relative_to(B)),'sha256':sha(C/'assembly-validation.json')}]
for d in angles:resources.append({'name':'approved-straight-'+d,'path':'../wall-middle/candidates/round-06/raw/static-'+d+'-0000.png','sha256':sha(FC/'raw'/f'static-{d}-0000.png')})
delivery={'asset':'wall-outer-corner','round':ROUND,'status':'candidate-ready-for-coordinator-seal-and-independent-judge','project':'source/'+ROUND+'.blend','recipe':'source/'+ROUND+'.py','supportingRecipes':['source/assemble-preview.py','source/inspect-source.py'],'validation':str((C/'validation.json').relative_to(B)),'heroes':{d:str((C/'raw'/f'static-{d}-0000.png').relative_to(B))for d in angles},'rawFrames':[{'clip':'static','direction':d,'index':0,'path':str((C/'raw'/f'static-{d}-0000.png').relative_to(B))}for d in angles],'atlases':[{'clip':'static','direction':d,'path':str((C/'atlases'/f'static-{d}.png').relative_to(B)),'sha256':sha(C/'atlases'/f'static-{d}.png'),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]}for d in angles],'previews':previews,'nativeRecords':{'camera':str((C/'native-camera.json').relative_to(B)),'assetRecord':str((C/'native-assetRecord.json').relative_to(B)),'rig':str((C/'native-rig.json').relative_to(B))},'resources':resources,'notes':['Native outside-rounded convex L construction, exact source W/S terminal profiles, shared approved palette/light/cut radiance.','Both W/S pair joins and three-module L joins rendered natively and assembled independently for every facing. RGB/alpha enlarged strips plus logical/light/gray/dark surfaces supplied.','No candidate self-approval; coordinator seals and independent same-object judge decides.']}
(B/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps({k:{a:b for a,b in v.items()if a!='portStrips'}for k,v in metrics.items()},indent=2))

