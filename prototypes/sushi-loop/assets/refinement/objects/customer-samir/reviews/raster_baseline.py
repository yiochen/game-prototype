from PIL import Image,ImageDraw
import json,pathlib,hashlib,math
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir')
R=P/'reviews'
for mode in ['main','runtime']:
 a=json.loads((R/('baseline-'+mode)/'audit.json').read_text());clips=list(a['clips']);sheet=Image.new('RGB',(4*192+140,len(clips)*330),(110,110,110));d=ImageDraw.Draw(sheet)
 for y,c in enumerate(clips):
  d.text((4,y*330+12),c,fill='white')
  for x,dr in enumerate(['S','E','N','W']):
   im=Image.open(R/('baseline-'+mode)/(c+'-'+dr+'-f05.png')).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS)
   sheet.paste(im,(140+x*192,y*330+10),im);d.text((140+x*192,y*330),dr,fill='white')
 sheet.save(R/('native-'+mode+'-allpose-sheet.jpg'),quality=93)
base=P.parents[2]/'production'
sheet=Image.new('RGB',(4*192,2*330),(110,110,110));d=ImageDraw.Draw(sheet)
for y,kind in enumerate(['native','legacy']):
 for x,dr in enumerate(['S','E','N','W']):
  im=Image.open((R/'baseline-main'/('stand-'+dr+'-f05.png')) if kind=='native' else base/'sprites/customer-samir'/('stand-'+dr+'.png')).convert('RGBA')
  if kind=='legacy':im=im.crop((4*384,0,5*384,640))
  im=im.resize((192,320));sheet.paste(im,(192*x,330*y+10),im);d.text((192*x+5,330*y),kind+' '+dr,fill='white')
sheet.save(R/'native-versus-legacy-cardinals.jpg',quality=95)
foods={
 'source-cucumber':R/'baseline-main/original-packed-food.png',
 'source-salmon':R/'baseline-runtime/original-packed-food.png',
 'canonical-cucumber':P.parents[2]/'production/source/2d/refinement/dish-cucumber/source/round01/dish-cucumber.png',
 'canonical-salmon':P.parents[2]/'production/source/2d/refinement/dish-salmon/source/round01/dish-salmon.png'}
report={}
for name,path in foods.items():
 im=Image.open(path).convert('RGBA');al=im.getchannel('A');th={}
 for threshold in [64,128,192]:
  mask=al.point(lambda x:255 if x>=threshold else 0);L,T,Rt,B=mask.getbbox();row=mask.crop((0,B-1,im.width,B)).getbbox();sx=(row[0]+row[2])/2
  th[str(threshold)]={'occupiedBoxTopOriginEdges':[L,T,Rt,B],'occupiedWidthPx':Rt-L,'occupiedHeightPx':B-T,'bottomRimSupportTopOriginEdges':[sx,B],'bottommostRowExtent':[row[0],row[2]]}
 report[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':im.size,'thresholds':th}
(R/'food-raster-baseline.json').write_text(json.dumps(report,indent=2))
proposal={}
for meal in ['cucumber','salmon']:
 source=report['source-'+meal];target=report['canonical-'+meal];native=json.loads((R/('baseline-'+('main' if meal=='cucumber' else 'runtime'))/'audit.json').read_text())['food'];uv=native['UV'];verts=native['vertices'];W,H=source['size']
 u0,u1=min(p[0] for p in uv),max(p[0] for p in uv);v0,v1=min(p[1] for p in uv),max(p[1] for p in uv)
 x0,x1=min(v[0] for v in verts),max(v[0] for v in verts);y0,y1=min(v[1] for v in verts),max(v[1] for v in verts)
 world_per_source_px=(x1-x0)*1.25/((u1-u0)*W)
 proposals={}
 for t in ['64','128','192']:
  sr=source['thresholds'][t];tr=target['thresholds'][t];old_width=sr['occupiedWidthPx']*world_per_source_px
  target_world_scale=old_width/tr['occupiedWidthPx']
  support_src=sr['bottomRimSupportTopOriginEdges'];support_tgt=tr['bottomRimSupportTopOriginEdges']
  support_local=[x0+(support_src[0]/W-u0)/(u1-u0)*(x1-x0),y0+((1-support_src[1]/H)-v0)/(v1-v0)*(y1-y0)]
  local_per_px=target_world_scale/1.25
  TW,TH=target['size'];newverts=[[support_local[0]+(px-support_tgt[0])*local_per_px,support_local[1]+(support_tgt[1]-py)*local_per_px,0] for px,py in [(0,TH),(TW,TH),(TW,0),(0,0)]]
  proposals[t]={'sourceOccupiedWorldWidth':old_width,'sourceBottomRimLocalXY':support_local,'canonicalWorldUnitsPerPixel':target_world_scale,'newFullUVLocalVertices':newverts,'newFullQuadWorldSize':[TW*target_world_scale,TH*target_world_scale]}
 proposal[meal]={'sourceUVRect':[u0,v0,u1,v1],'sourceQuadLocalRange':[x0,y0,x1,y1],'sourceWorldUnitsPerPixel':world_per_source_px,'thresholdSensitivity':proposals}
(R/'food-mapping-proposal.json').write_text(json.dumps({'pointConvention':'Top-origin image pixel-edge grid: occupied alpha>=threshold pixel box is [L,T,R,B), and bottom-rim support is midpoint of occupied pixel run on bottommost qualifying row at the outside bottom edge, ((rowL+rowR)/2,B). Coordinates are edges, not pixel centers. UV uses bottom-origin v=1-y/H. Use alpha>=128 primary; 64/192 sensitivity is descriptive, not three selectable mappings.','mapping':'One isotropic, global affine map per canonical food from full image edge coordinates to plane local XY. Match actual source occupied width and bottom-rim point using source actual UV rectangle, with full canonical UV[0,1] and aspect preserved. No alpha crop/re-encode/regrade; same map across all frames/facings. Local plane placement/depth/animation remains distinct from image mapping.','proposals':proposal},indent=2))
print(json.dumps({'food':report,'mapping':proposal},indent=2))
