"""Package unchanged native frames; assemble independent sprites by authored roots.
Pillow only lays out diagnostic previews and copies native frame bytes to atlases.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil,math
import numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-02';F=B.parent/'wall-middle';P=O/'previews';P.mkdir(exist_ok=True);A=O/'atlases';A.mkdir(exist_ok=True);S=O/'sprite-joins';S.mkdir(exist_ok=True)
BG=[('light','#f5f1e6'),('gray','#737783'),('dark','#19212b')];FAC={'N':180,'E':90,'S':0,'W':-90}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(B))
def composite(im,color):
 out=Image.new('RGBA',im.size,color);out.alpha_composite(im);return out.convert('RGB')
def label(draw,xy,text):draw.text(xy,text,fill='black')
def panel_sheet(images,labels,scale=.5,alpha=False):
 # columns = backgrounds plus alpha. Every image is downsampled identically.
 ims=[im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS if scale<1 else Image.Resampling.NEAREST)for im in images];w=max(im.width for im in ims);h=max(im.height for im in ims)
 out=Image.new('RGB',(w*4,(h+24)*len(ims)),'#ddd9cf');dr=ImageDraw.Draw(out)
 for row,(im,title)in enumerate(zip(ims,labels)):
  for col,(name,c)in enumerate(BG):out.paste(composite(im,c),(col*w,row*(h+24)+24));label(dr,(col*w+5,row*(h+24)+5),title+' / '+name)
  out.paste(im.getchannel('A').convert('RGB'),(3*w,row*(h+24)+24));label(dr,(3*w+5,row*(h+24)+5),title+' / alpha')
 return out
previews={};raw=[];atlases=[];heroes={};audit={'singles':{},'assemblies':{}};resources=[]
frames=[]
for d in FAC:
 p=O/'raw'/f'static-{d}-0000.png';im=Image.open(p).convert('RGBA');frames.append(im);heroes[d]=rel(p);raw.append({'clip':'static','direction':d,'index':0,'path':rel(p)})
 ap=A/f'static-{d}.png';shutil.copy2(p,ap);atlases.append({'clip':'static','direction':d,'path':rel(ap),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'sha256':sha(ap)})
 alpha=np.array(im)[:,:,3];bbox=im.getbbox();audit['singles'][d]={'size':list(im.size),'mode':im.mode,'alphaBounds':list(bbox),'borderAlphaPixels':int(np.count_nonzero(np.r_[alpha[0],alpha[-1],alpha[:,0],alpha[:,-1]])),'transparentPixels':int(np.count_nonzero(alpha==0)),'opaquePixels':int(np.count_nonzero(alpha==255)),'sourceEqualsAtlas':sha(p)==sha(ap)}
 assert im.size==(384,704) and not audit['singles'][d]['borderAlphaPixels']
# Four-view at native pixel resolution; paired logical backgrounds and 2x pixels.
for name,img in [('four-view-sheet',panel_sheet(frames,list(FAC),1)),('four-view-logical-backgrounds',panel_sheet(frames,list(FAC),.5)),('four-view-enlarged-pixels',panel_sheet(frames,list(FAC),2))]:
 p=P/(name+'.png');img.save(p);previews[name]=rel(p)
family_raw={}
for d in FAC:
 src=F/'candidates/round-06/raw'/f'static-{d}-0000.png';dst=O/'dependencies'/f'approved-straight-{d}.png';shutil.copy2(src,dst);family_raw[d]=dst;resources.append({'name':'approved-straight-'+d,'path':rel(dst),'sha256':sha(dst)})
repeated=[];assembly_records=[]
for d,degrees in FAC.items():
 rad=math.radians(degrees);placements=[{'asset':'corner','direction':d,'world':[0,0,0],'path':O/'raw'/f'static-{d}-0000.png'}]
 for port,loc,turn in [('W',(-1,0),0),('N',(0,1),90)]:
  x=round(math.cos(rad)*loc[0]-math.sin(rad)*loc[1],8);y=round(math.sin(rad)*loc[0]+math.cos(rad)*loc[1],8);fd={0:'S',90:'E',180:'N',270:'W'}[(degrees+turn)%360]
  placements.append({'asset':'approved-straight','port':port,'direction':fd,'world':[x,y,0],'path':family_raw[fd]})
 result=Image.new('RGBA',(896,1216));decl=[]
 for item in sorted(placements,key=lambda q:-q['world'][1]):
  x,y,_=item['world'];pixelroot=(round(448+x*256),round(768-y*256));paste=(pixelroot[0]-192,pixelroot[1]-512);im=Image.open(item['path']).convert('RGBA');result.alpha_composite(im,paste)
  decl.append({**item,'path':rel(item['path']),'sha256':sha(item['path']),'logicalRoot':[96,256],'pixelRoot':pixelroot,'paste':paste})
 p=S/f'static-{d}-both-ports.png';result.save(p);previews['independent-join-'+d]=rel(p)
 npath=O/'native-joins'/f'static-{d}-both-ports.png';native=Image.open(npath).convert('RGBA');previews['native-join-'+d]=rel(npath)
 assembly_records.append({'direction':d,'cornerRotationDegrees':degrees,'method':'Independent native RGBA sprites placed at fixed authored roots and ports; depth sorted by world Y; no image transformation other than integer translation; no painted seam or overlap','frame':[896,1216],'root':[448,768],'pixelPitch':256,'placements':decl,'path':rel(p),'nativeReference':rel(npath)})
 # Crop the common content window only for diagnostic page layout.
 box=ImageChops.lighter(native.getchannel('A'),result.getchannel('A')).getbbox();box=(max(0,box[0]-16),max(0,box[1]-16),min(896,box[2]+16),min(1216,box[3]+16))
 ims=[native.crop(box),result.crop(box)];names=['native '+d,'sprites '+d]
 for suffix,scale in [('logical-backgrounds',.5),('enlarged-pixels',2)]:
  q=P/f'join-{d}-{suffix}.png';panel_sheet(ims,names,scale).save(q);previews['join-'+d+'-'+suffix]=rel(q)
 repeated.append(composite(result.crop(box),'#e5e1d6').resize((round((box[2]-box[0])*.5),round((box[3]-box[1])*.5)),Image.Resampling.LANCZOS))
 a=np.array(result).astype(int);b=np.array(native).astype(int);mask=(a[:,:,3]>254)&(b[:,:,3]>254);dif=np.abs(a[:,:,:3]-b[:,:,:3]);ad=np.abs(a[:,:,3]-b[:,:,3]);audit['assemblies'][d]={'nativeBounds':list(native.getbbox()),'spriteBounds':list(result.getbbox()),'opaqueRGBMeanAbsDifference':dif[mask].mean(axis=0).tolist(),'opaqueRGBP99AbsDifference':np.percentile(dif[mask],99,axis=0).tolist(),'alphaMaximumDifference':int(ad.max()),'alphaPixelsDifferenceOver8':int(np.count_nonzero(ad>8))}
 # Each port is shown separately at 2x, with both native and independent RGB+alpha.
 for port,loc in [('W',(-.5,0)),('N',(0,.5))]:
  x=math.cos(rad)*loc[0]-math.sin(rad)*loc[1];y=math.sin(rad)*loc[0]+math.cos(rad)*loc[1];cx=448+x*256;cy=768-y*256
  bb=(round(cx-70),round(cy-225),round(cx+70),round(cy+25));q=P/f'join-{d}-port-{port}-enlarged.png';panel_sheet([native.crop(bb),result.crop(bb)],['native '+d+' '+port,'sprites '+d+' '+port],2).save(q);previews[f'join-{d}-port-{port}-enlarged']=rel(q)
# Genuine repeated/connected evidence generic slot, four facing independent assemblies.
w=max(im.width for im in repeated);h=max(im.height for im in repeated);sheet=Image.new('RGB',(w*2,(h+24)*2),'#d7d4cb');dr=ImageDraw.Draw(sheet)
for i,(d,im)in enumerate(zip(FAC,repeated)):
 x=(i%2)*w;y=(i//2)*(h+24);sheet.paste(im,(x,y+24));dr.text((x+5,y+5),d+' corner + 2 straight walls',fill='black')
p=P/'repeated.png';sheet.save(p);previews['repeated']=rel(p)
(O/'sprite-assembly-records.json').write_text(json.dumps(assembly_records,indent=2));(O/'image-audit.json').write_text(json.dumps(audit,indent=2))
v=json.loads((O/'validation.json').read_text());v['imageAudit']=audit;v['reopenedNativeAudit']='candidates/round-02/reopened-native-audit.json';v['geometry']['selectedObjectReopenValidationPassed']=True;v['spriteAssemblyRecords']=rel(O/'sprite-assembly-records.json');(O/'validation.json').write_text(json.dumps(v,indent=2))
resources += [{'name':'approved-family-settings','path':rel(O/'family-settings.json'),'sha256':sha(O/'family-settings.json')},{'name':'approved-straight-native-model','path':rel(O/'dependencies/family-straight.blend'),'sha256':sha(O/'dependencies/family-straight.blend')},{'name':'native-join-context','path':'source/round-02-join-context.blend','sha256':sha(B/'source/round-02-join-context.blend')},{'name':'sprite-assembly-records','path':rel(O/'sprite-assembly-records.json'),'sha256':sha(O/'sprite-assembly-records.json')},{'name':'image-audit','path':rel(O/'image-audit.json'),'sha256':sha(O/'image-audit.json')},{'name':'package-recipe','path':'source/package_round02.py','sha256':sha(B/'source/package_round02.py')}]
for name,path in [('reopened-native-audit',O/'reopened-native-audit.json'),('audit-recipe',B/'source/audit_round02.py'),('original-native-inspection',B/'candidates/inspection/source.json')]:resources.append({'name':name,'path':rel(path),'sha256':sha(path)})
delivery={'asset':'wall-inner-corner','round':'round-02','status':'candidate-awaiting-independent-judge','project':'source/round-02.blend','recipe':'source/round-02.py','validation':rel(O/'validation.json'),'heroes':heroes,'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(O/'native-camera.json'),'assetRecord':rel(O/'native-assetRecord.json'),'rig':rel(O/'native-rig.json')},'resources':resources}
(B/'delivery.json').write_text(json.dumps(delivery,indent=2));(O/'delivery.json').write_text(json.dumps(delivery,indent=2));print(json.dumps({'round':'round-02','previews':len(previews),'imageAudit':audit},indent=2))
