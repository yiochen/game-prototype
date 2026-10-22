from pathlib import Path
import json,hashlib,math,shutil,subprocess,copy
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent.parent;S=O/'source';C=O/'candidates/round-01';P=C/'previews';P.mkdir(parents=True,exist_ok=True)
ROOT=O.parents[3];G=S/'runtime-godot' if (S/'runtime-godot/objects.json').exists() else ROOT/'godot'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 if a.resolve()!=b.resolve():shutil.copyfile(a,b)
raw=[];atlases=[]
for d in ['N','E','S','W']:
 atlas=Image.new('RGBA',(2304,1408));rects=[]
 for i in range(12):
  f=C/'raw'/('pop-'+d)/f'{i:03}.png';im=Image.open(f).convert('RGBA');assert im.size==(384,704);x=i%6*384;y=i//6*704;atlas.paste(im,(x,y));rects.append([x,y,384,704]);raw.append({'clip':'pop','direction':d,'index':i,'path':f.relative_to(O).as_posix(),'sha256':sha(f)})
 path=C/'atlases'/f'pop-{d}.png';path.parent.mkdir(exist_ok=True);atlas.save(path)
 atlases.append({'clip':'pop','direction':d,'path':path.relative_to(O).as_posix(),'sha256':sha(path),'columns':6,'rows':2,'size':[2304,1408],'rects':rects,'fps':12,'loop':False,'frameOrder':list(range(12))})
# Full registered canvases at logical scale on light/mid/dark backgrounds.
bgs=['#f8f1df','#78888b','#182c3b'];sheet=Image.new('RGB',(4*192,3*376),'#f8f1df');dr=ImageDraw.Draw(sheet)
for row,bg in enumerate(bgs):
 for n,d in enumerate(['N','E','S','W']):
  tile=Image.new('RGBA',(192,352),bg);im=Image.open(C/'raw'/('pop-'+d)/'005.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(n*192,row*376+24));dr.text((n*192+8,row*376+5),d+' 192x352 / root96,256',fill='#111111' if row<2 else '#ffffff')
sheet.save(P/'four-view-backgrounds-logical.png')
# All12 full canvases at64px/cell; do not fit the effect bounds.
for d in ['N','E','S','W']:
 sh=Image.new('RGB',(12*96,200),'#f8f1df');draw=ImageDraw.Draw(sh)
 for i in range(12):
  im=Image.open(C/'raw'/('pop-'+d)/f'{i:03}.png').convert('RGBA').resize((96,176),Image.Resampling.LANCZOS);sh.paste(im,(i*96,24),im);draw.text((i*96+5,6),d+' / '+str(i),fill='#253b3b')
 sh.save(P/f'whole-canvas-64-{d}.png')
# Native1s playback, 12fps, original complete registered canvases in four directions.
vid=C/'video-native';vid.mkdir(exist_ok=True)
for i in range(12):
 sh=Image.new('RGB',(768,400),'#f8f1df');draw=ImageDraw.Draw(sh);draw.text((12,8),f'NATIVE POP / 12fps / nonloop / phase {i}/11 / logical192x352',fill='#253b3b')
 for n,d in enumerate(['N','E','S','W']):
  bg=Image.new('RGBA',(192,352),bgs[n%3]);im=Image.open(C/'raw'/('pop-'+d)/f'{i:03}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);bg.alpha_composite(im);sh.paste(bg.convert('RGB'),(192*n,48));draw.text((192*n+8,30),d,fill='#253b3b')
 sh.save(vid/f'{i:03}.png')
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','12','-i',str(vid/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','15',str(P/'native-pop-all4.mp4')],check=True)
# Snapshot exact current runtime scripts and minimal registered atlas closure.
N=S/'runtime-godot';(N/'scripts').mkdir(parents=True,exist_ok=True)
for name in ['restaurant_view.gd','art_book.gd','typography.gd']:cp(G/'scripts'/name,N/'scripts'/name)
manifest={'objects':json.loads((G/'objects.json').read_text())} if (G/'objects.json').exists() else json.loads((G/'assets/catalog/manifest.json').read_text());ctx={}
for identity,clips in [('customer-ellis',['seated-wait','stand']),('stool-wood',['static']),('floor-cream',['static']),('coin-pop',['pop'])]:
 rec=copy.deepcopy(manifest['objects'][identity]);rec['clips']={k:v for k,v in rec['clips'].items() if k in clips}
 if identity=='coin-pop':
  rec={'frameSize':[192,352],'root':[96,256],'sourceScale':2,'clips':{'pop':{'frames':12,'fps':12,'loop':False,'directions':{a['direction']:{'image':'sprites/coin-pop/pop-'+a['direction']+'.png','rects':a['rects']}for a in atlases}}}}
 for clip in rec['clips'].values():
  for d,entry in clip['directions'].items():
   if identity=='coin-pop':src=C/'atlases'/('pop-'+d+'.png')
   else:src=G/'assets/catalog'/entry['image']
   cp(src,N/'assets/catalog'/entry['image'])
 ctx[identity]=rec
write(N/'objects.json',ctx)
(N/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Coin Pop Isolated Current Runtime"\nrun/main_scene="res://capture.tscn"\n[display]\nwindow/size/viewport_width=1080\nwindow/size/viewport_height=760\nwindow/size/window_width_override=1080\nwindow/size/window_height_override=760\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\n')
(N/'capture.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://capture.gd" id="1"]\n[node name="Capture" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\nscript=ExtResource("1")\n')
original=(G/'scripts/restaurant_view.gd').read_text();sale=original[original.index('\tfor pop in sale_pops:\n'):original.index('\nfunc _render_room_items')]
(S/'runtime-sale-loop-verbatim.gd.txt').write_text(sale)
harness='''extends "res://scripts/restaurant_view.gd"
var output := ""
var sample_time := 0.0
var receipts: Array = []
func _ready() -> void:
 native_composition_enabled = false
 clip_contents = false
 texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
 font = ThemeDB.fallback_font
 heading = font
 art.objects = JSON.parse_string(FileAccess.get_file_as_string("res://objects.json"))
 art.cell_size = 128.0
 var args := OS.get_cmdline_user_args()
 output=args[1]
 for tick in range(36):
  sample_time=tick/30.0
  time=sample_time
  receipts.append({"tick":tick,"age":time,"visible":time<0.9,"alpha":1.0-time/0.9 if time<0.9 else 0.0,"actualArtBookFrame":art.frame_data("coin-pop","pop","S",time).frame,"basePolicy":"cell_base(pop.x,pop.y), no offset"})
  queue_redraw()
  await get_tree().process_frame
  await get_tree().process_frame
  await RenderingServer.frame_post_draw
  get_viewport().get_texture().get_image().save_png(output.path_join("%03d.png" % tick))
 var f := FileAccess.open(output.path_join("runtime-receipts.json"),FileAccess.WRITE)
 f.store_string(JSON.stringify(receipts,"  "))
 print("COIN_RUNTIME_CAPTURE_COMPLETE "+str(receipts.size()))
 get_tree().quit(0)
func _process(_delta: float) -> void:
 pass
func _draw() -> void:
 if font == null: return
 draw_rect(Rect2(0,0,1080,760),Color("f8f1df"))
 caption("ACTUAL GODOT / inherited current sprite registration + verbatim sale loop",Vector2(16,28),19)
 caption("0.9s runtime fade / same customer ground root / age=%.3fs"%sample_time,Vector2(16,53),18)
 for row in range(2):
  cell=128.0 if row==0 else 64.0
  for col in range(3):
   var bg: Color = [Color("f8f1df"),Color("78888b"),Color("182c3b")][col]
   var panel := Rect2(col*360,72+row*344,360,340)
   draw_rect(panel,bg)
   var ink := Color("ffffff") if col==2 else Color("253b3b")
   draw_string(font,Vector2(col*360+12,96+row*344),"cell%dpx / repeated registered instances"%int(cell),HORIZONTAL_ALIGNMENT_LEFT,-1,15,ink)
   var base := Vector2(col*360+98,380 if row==0 else 676)
   floor_origin=base-Vector2.ONE*cell*.5
   for x in [0.0,1.25]:
    var at:=cell_base(x,0)
    sprite("floor-cream",at,"static","S",0.0,cell)
    _seat_at({"facing":"south"},at,cell)
    _customer_at({"appearance":1,"phase":"waiting","visual_phase":"seated-wait","facing":"south","visual_elapsed":sample_time},at,cell)
   sale_pops=[{"x":0.0,"y":0.0,"time":0.0},{"x":1.25,"y":0.0,"time":0.0}]
   _actual_sale_loop()
func _actual_sale_loop() -> void:
'''
harness='\n'.join('\t'*(len(line)-len(line.lstrip(' ')))+line.lstrip(' ') for line in harness.split('\n'))
(N/'capture.gd').write_text(harness+sale+'\n')
# Runtime audit binds the exact current source block, rather than moving stale catalog labels.
write(C/'runtime-source-record.json',{'scope':'Actual Godot viewport fixture, inherited byte-exact current renderer sprite/customer/stool/cell_base methods. Verbatim actual sale loop copied into fixture method. No game simulation claim.','restaurantViewSHA256':sha(N/'scripts/restaurant_view.gd'),'artBookSHA256':sha(N/'scripts/art_book.gd'),'saleLoopSHA256':sha(S/'runtime-sale-loop-verbatim.gd.txt'),'harnessSHA256':sha(N/'capture.gd'),'durationSeconds':.9,'attachment':'cell_base(float(pop.x),float(pop.y))','relocation':False,'nativeFrameScale':2,'cellSizes':[128,64],'facingsRenderedRuntime':['S'],'nativeAllFacings':['N','E','S','W']})
write(C/'packaging-index.json',{'rawFrames':raw,'atlases':atlases})
print('PACKAGING_PHASE_ONE_COMPLETE',N)
