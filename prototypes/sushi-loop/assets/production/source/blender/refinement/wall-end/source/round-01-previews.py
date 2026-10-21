"""Unmodified registered RGBA assembly and review sheets only; no sprite edits."""
import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[1];C=B/'candidates/round-01';M=B.parent/'wall-middle/candidates/round-06'
O=C/'previews';O.mkdir(exist_ok=True);A=C/'atlases';A.mkdir(exist_ok=True);J=C/'sprite-joins';J.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backgrounds={'light':(242,238,228),'gray':(122,126,132),'dark':(24,29,39)};directions='NESW';previews={};frames={d:Image.open(C/'raw'/f'static-{d}-0000.png').convert('RGBA')for d in directions}
def back(im,bg):
 a=Image.new('RGBA',im.size,bg+(255,));a.alpha_composite(im);return a.convert('RGB')
def save(im,name):
 p=O/(name+'.png');im.save(p);previews[name]=str(p.relative_to(B))
def sheet_cells(cells,size,rows,bg=(122,126,132)):
 out=Image.new('RGB',(size[0]*len(cells[0]),(size[1]+28)*rows),bg);dr=ImageDraw.Draw(out)
 for r,row in enumerate(cells):
  for c,(name,im)in enumerate(row):out.paste(im,(c*size[0],r*(size[1]+28)+28));dr.text((c*size[0]+5,r*(size[1]+28)+7),name,fill='white')
 return out
save(sheet_cells([[(d,back(frames[d],backgrounds['gray']))for d in directions]],(384,704),1),'four-view-sheet')
save(sheet_cells([[(d+' / '+name,back(frames[d],bg).resize((192,352),Image.Resampling.LANCZOS))for d in directions]for name,bg in backgrounds.items()],(192,352),3),'four-view-logical-backgrounds')
save(sheet_cells([[(d+' alpha',Image.merge('RGB',(frames[d].getchannel('A'),)*3).resize((192,352),Image.Resampling.LANCZOS))for d in directions]],(192,352),1),'four-view-logical-alpha')
# Alpha and RGB enlarged surface evidence, using full rendered alpha bounds.
boxes={d:frames[d].getchannel('A').getbbox()for d in directions};w=max((q[2]-q[0])*3 for q in boxes.values());h=max((q[3]-q[1])*3 for q in boxes.values());rows=[]
for name,bg in backgrounds.items():
 row=[]
 for d in directions:
  crop=back(frames[d],bg).crop(boxes[d]);cell=Image.new('RGB',(w,h),bg);cell.paste(crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST),(0,0));row.append((d+' 3x native / '+name,cell))
 rows.append(row)
save(sheet_cells(rows,(w,h),3),'four-view-enlarged-backgrounds')
orig={d:Image.open((B/'../../../production/sprites/wall-end'/f'static-{d}.png').resolve()).convert('RGBA')for d in directions}
save(sheet_cells([[(d+' source',back(orig[d],backgrounds['gray']).resize((192,352),Image.Resampling.LANCZOS))for d in directions],[(d+' round01',back(frames[d],backgrounds['gray']).resize((192,352),Image.Resampling.LANCZOS))for d in directions]],(192,352),2),'source-candidate-logical')
metrics={};placements={};neighbor_hashes={};joinims=[]
for d in directions:
 shutil.copy2(C/'raw'/f'static-{d}-0000.png',A/f'static-{d}.png')
 npath=M/'raw'/f'static-{d}-0000.png';neighbor_hashes[d]={'path':'../wall-middle/candidates/round-06/raw/'+npath.name,'sha256':sha(npath)};neighbor=Image.open(npath).convert('RGBA')
 native=Image.open(C/'native-joins'/f'static-{d}-W-neighbor.png').convert('RGBA');out=Image.new('RGBA',native.size)
 offset={'N':(256,0),'E':(0,256),'S':(-256,0),'W':(0,-256)}[d]
 ps=[('wall-end',frames[d],(256,256)),('wall-middle',neighbor,(256+offset[0],256+offset[1]))];ps.sort(key=lambda p:p[2][1]);placements[d]=[]
 for asset,im,p in ps:out.alpha_composite(im,p);placements[d].append({'asset':asset,'frameOrigin':list(p),'root':[p[0]+192,p[1]+512]})
 out.save(J/f'static-{d}-W-neighbor.png');joinims.append((d,out))
 aa=np.asarray(native).astype(float);bb=np.asarray(out).astype(float);union=(aa[:,:,3]>0)|(bb[:,:,3]>0);opaque=(aa[:,:,3]>250)&(bb[:,:,3]>250);delta=np.abs(aa[:,:,:3]-bb[:,:,:3]);ad=np.abs(aa[:,:,3]-bb[:,:,3]);metrics[d]={'alphaMaxDelta':float(ad.max()),'alphaMeanDeltaOnUnion':float(ad[union].mean()),'opaqueRGBMeanDelta':float(delta[opaque].mean()),'opaqueRGBP99Delta':float(np.percentile(delta[opaque],99)),'opaqueRGBMaxDelta':float(delta[opaque].max()),'pixelsOpaqueRGBDeltaOver10':int((delta.max(axis=2)[opaque]>10).sum())}
 rows=[[(d+' native / '+name,back(native,bg).resize((448,608),Image.Resampling.LANCZOS)),(d+' independent / '+name,back(out,bg).resize((448,608),Image.Resampling.LANCZOS))]for name,bg in backgrounds.items()]
 save(sheet_cells(rows,(448,608),3),f'join-{d}-logical-backgrounds')
 # Whole alpha proof at logical scale for both methods.
 save(sheet_cells([[(d+' native alpha',Image.merge('RGB',(native.getchannel('A'),)*3).resize((448,608),Image.Resampling.LANCZOS)),(d+' independent alpha',Image.merge('RGB',(out.getchannel('A'),)*3).resize((448,608),Image.Resampling.LANCZOS))]],(448,608),1),f'join-{d}-logical-alpha')
 box={'N':(568,526,584,800),'S':(312,526,328,800),'E':(393,706,503,899),'W':(393,450,503,643)}[d]
 rows=[]
 for title,im in [('native',native),('independent',out)]:
  row=[]
  for name,bg in backgrounds.items():
   cr=back(im,bg).crop(box);row.append((title+' '+name,cr.resize((cr.width*4,cr.height*4),Image.Resampling.NEAREST)))
  alpha=im.getchannel('A').crop(box);rgb=Image.merge('RGB',(alpha,)*3).resize((alpha.width*4,alpha.height*4),Image.Resampling.NEAREST);row.append((title+' alpha',rgb));rows.append(row)
 save(sheet_cells(rows,((box[2]-box[0])*4,(box[3]-box[1])*4),2),f'join-{d}-RGB-alpha-enlarged')
 x1,y1,x2,y2=box;mask=opaque[y1:y2,x1:x2];dd=delta[y1:y2,x1:x2][mask];metrics[d]['seamRegion']={'box':list(box),'opaqueRGBMeanDelta':float(dd.mean()),'opaqueRGBP99Delta':float(np.percentile(dd,99)),'opaqueRGBMaxDelta':float(dd.max()),'alphaMaxDelta':float(ad[y1:y2,x1:x2].max())}
 diff=np.zeros(aa.shape,dtype=np.uint8);diff[:,:,:3]=np.clip(delta*8,0,255);diff[:,:,3]=union*255;save(back(Image.fromarray(diff),backgrounds['dark']),f'join-{d}-difference-x8')
 previews['native-join-'+d]=str((C/'native-joins'/f'static-{d}-W-neighbor.png').relative_to(B));previews['independent-join-'+d]=str((J/f'static-{d}-W-neighbor.png').relative_to(B))
# Repeated preview name means actual approved-neighbor assembly, not end/end.
save(sheet_cells([[(d+' W-approved-neighbor',back(im,backgrounds['gray']).resize((448,608),Image.Resampling.LANCZOS))for d,im in joinims]],(448,608),1),'repeated')
alpha={}
for d,im in frames.items():
 a=np.asarray(im)[:,:,3];box=im.getchannel('A').getbbox();alpha[d]={'size':list(im.size),'alphaBounds':list(box),'clipped':box[0]==0 or box[1]==0 or box[2]==384 or box[3]==704,'nonzeroPixels':int((a>0).sum()),'rawSHA256':sha(C/'raw'/f'static-{d}-0000.png'),'atlasSHA256':sha(A/f'static-{d}.png')}
(C/'assembly-validation.json').write_text(json.dumps({'method':'Exact registered root pitch256; depth sorted alpha-over native end and exact approved wall-middle RGBA bytes. No pixel correction or overlap extension.','canvas':[896,1216],'mainRoot':[448,768],'placements':placements,'neighborSources':neighbor_hashes,'nativeIndependentComparison':metrics,'rawAlphaChecks':alpha},indent=2));(C/'previews-map.json').write_text(json.dumps(previews,indent=2));print(json.dumps(metrics,indent=2))
