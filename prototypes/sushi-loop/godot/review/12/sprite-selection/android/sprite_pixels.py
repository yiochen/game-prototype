"""Offline production-atlas point selection; never connects to Android or alters app state."""
from functools import lru_cache
from PIL import Image,ImageFilter
from copy import deepcopy
import math,json
from touch_geometry import *
FACING={'north':'N','east':'E','south':'S','west':'W'}
DIR={'north':(0,-1),'east':(1,0),'south':(0,1),'west':(-1,0)}
DISH={'salmon_nigiri':'dish-salmon','cucumber_maki':'dish-cucumber','eel_nigiri':'dish-eel'}
@lru_cache(maxsize=1)
def catalog():
 root=PROJECT/'assets';r=json.loads((root/'catalog/manifest.json').read_text())['objects']
 for variant in ['recipe-variants','chef-variants','feedback-variants']:
  d=json.loads((root/variant/'manifest.json').read_text())
  for identity,value in d.get('objects',{}).items():
   if identity not in r:continue
   for clip,record in value.get('clips',{}).items():
    record=deepcopy(record)
    for entry in record['directions'].values():entry['_directory']='assets/'+variant
    r[identity]['clips'][clip]=record
 return r
@lru_cache(maxsize=16)
def rgba(path):return Image.open(PROJECT/path).convert('RGBA')
def frame(identity,clip='static',direction='S',seconds=0.):
 obj=catalog()[identity];clips=obj['clips'];action=clips.get(clip,next(iter(clips.values())));entry=action['directions'].get(direction,action['directions'].get('S',{}));assert entry,(identity,clip,direction)
 count=int(entry.get('frames',action.get('frames',1)));index=max(0,math.floor(max(0.,seconds)*float(action.get('fps',12))+.0000001));index=min(index,count-1) if action.get('loop',True) is False else index%count
 region=entry['rects'][index]
 return {'art_id':identity,'clip':clip,'direction':direction,'frame':index,'region':region,'source_path':entry.get('_directory','assets/catalog')+'/'+entry['image'],'root':entry.get('root',action.get('root',obj.get('root',[96,248]))),'size':entry.get('frameSize',action.get('frameSize',obj.get('frameSize',[192,320])))}
def pitch(d):return 672./d['configuration']['floor'].get('viewport_columns',7)
def logical_base(d,x,y):return tuple(v/SCALE for v in cell(d,x,y))
def socket(identity,name,direction='S'):
 value=catalog()[identity].get('sockets',{}).get(direction,{}).get(name,[0,0]);return value.get('position',[0,0]) if isinstance(value,dict) else value

def records(d):
 s=d['state'];floor=d['configuration']['floor'];p=pitch(d);elapsed=s['elapsed'];plan=[]
 def prop(art,x,y,clip='static',direction='S',owner=''):
  plan.append((float(y),0,[('sprite',owner,art,logical_base(d,x,y),clip,direction,elapsed,p)]))
 prop('entry-finished',floor['entrance']['x'],floor['entrance']['y'])
 for x in range(int(floor['world_columns'])):prop('wall-middle',x,-.5)
 for y in range(1,int(floor['rows'])-1):prop('wall-middle',-.5,y,direction='E')
 prop('plant-angular',0,0,'idle');prop('barrel-wood',0,floor['rows']-1);prop('plant-angular',floor['world_columns']-1,floor['rows']-1,'idle')
 for x in range(1,int(floor['world_columns']),5):prop('lantern-gold',x,0,'idle');prop('crate-wood',x,floor['rows']-1)
 for art,x,y in [('garbage-sofa',9.5,5.5),('garbage-shelving',13.5,8.5),('garbage-car',18.,5.5)]:prop(art,x,y,'idle')
 for o in s['objects']:
  owner=o['id'];base=logical_base(d,o['x'],o['y']);direction=FACING.get(o.get('facing'),'S');kind=o['kind']
  if kind=='decor':prop(o.get('art_id','plant-angular'),o['x'],o['y'],'idle' if o.get('art_id')=='plant-angular' else 'static',direction,owner)
  elif kind=='seat':plan.append((o['y'],0,[('sprite',owner,'stool-wood',base,'static',direction,0.,p)]))
  elif kind=='belt':
   delta=DIR[o['facing']];behind=any(a['kind']=='belt' and (a['x'],a['y'])==(o['x']-delta[0],o['y']-delta[1]) for a in s['objects']);ahead=any(a['kind']=='belt' and (a['x'],a['y'])==(o['x']+delta[0],o['y']+delta[1]) for a in s['objects'])
   art='belt-start-e' if not behind else 'belt-end-e' if not ahead else 'belt-straight-e';facing={'east':'S','north':'E','west':'N','south':'W'}[o['facing']]
   plan.append((o['y'],1,[('sprite',owner,art,base,'running',facing,elapsed,p)]))
   if o.get('dish'):
    travel=min(1.,max(0.,o['travel_elapsed']/d['configuration']['service']['belt_seconds_per_cell'])) if ahead else 0.;deck=socket(art,'deck',facing);at=(base[0]+delta[0]*p*travel+deck[0]*p/128.,base[1]+delta[1]*p*travel+deck[1]*p/128.)
    plan.append((o['y'],3,[('sprite',owner,DISH.get(o['dish']['recipe_id'],'dish-salmon'),at,'static','S',0.,p)]))
  elif kind=='chef':
   delta=DIR[o['facing']];active=any(a['kind']=='belt' and (a['x'],a['y'])==(o['x']+delta[0],o['y']+delta[1]) for a in s['objects']);clip=o.get('visual_phase','hold' if o.get('held_dish') else 'work') if active else 'idle'
   if o.get('art_id')=='chef-omar' and o.get('recipe_id')=='cucumber_maki' and clip in ['hold','load']:clip+='-cucumber'
   plan.append((o['y'],2,[('sprite',owner,o.get('art_id','chef-lena'),base,clip,direction,o.get('visual_elapsed',elapsed),p)]))
   face=socket('chef-blackboard','display_face');at=(base[0]+face[0]*p/128.,base[1]+face[1]*p/128.)
   plan.append((o['y']+.4,4,[('sprite',owner,'chef-blackboard',base,'idle','S',0.,p),('sprite',owner,DISH.get(o.get('recipe_id'),'dish-salmon'),at,'static','S',0.,p*.28)]))
 for c in s['customers']:
  at=logical_base(d,c['x'],c['y']);ox=c.get('render_offset_x',0);oy=c.get('render_offset_y',0);happy=c.get('happy_elapsed',100)
  if c.get('preference_phase')=='satisfied' and 0<=happy<.55:oy-=math.sin(math.pi*happy/.55)*.14
  at=(at[0]+ox*p,at[1]+oy*p);phase=c.get('phase','waiting');clip=c.get('visual_phase','eat' if phase=='eating' else 'seated-wait' if phase=='waiting' else 'walk')
  if c.get('restless') and phase=='waiting' and clip in ['seated-wait','seated-wait-empty','restless']:clip='restless'
  elif clip=='seated-wait':clip='seated-wait-empty'
  elif clip=='eat' and isinstance(c.get('meal_dish'),dict) and c['meal_dish'].get('recipe_id')=='salmon_nigiri':clip='eat-salmon'
  plan.append((c['y']+c.get('render_offset_y',0),2,[('sprite','','customer-'+['rosa','ellis','samir','june'][int(c.get('appearance',0))%4],at,clip,FACING.get(c.get('facing'),'S'),c.get('visual_elapsed',elapsed),p)]))
 result=[]
 for _,__,items in sorted(plan,key=lambda q:(q[0],q[1])):
  for _,owner,art,base,clip,direction,seconds,scale in items:
   f=frame(art,clip,direction,seconds);f['owner_id']=owner;f['rect']=[base[0]-f['root'][0]*scale/128.,base[1]-f['root'][1]*scale/128.,f['size'][0]*scale/128.,f['size'][1]*scale/128.];result.append(f)
 return result

def source_pixel(record,point):
 x,y,w,h=record['rect'];rx,ry,rw,rh=record['region'];return (math.floor(rx+(point[0]-x)/w*rw),math.floor(ry+(point[1]-y)/h*rh))
def contains(rect,p):return rect[0]<=p[0]<rect[0]+rect[2] and rect[1]<=p[1]<rect[1]+rect[3]
def picked(rs,p):
 if not (0<=p[0]<720 and 0<=p[1]<CANVAS_H):return None
 for r in reversed(rs):
  if contains(r['rect'],p) and rgba(r['source_path']).getpixel(source_pixel(r,p))[3]>25.5:return r
 return None

def ui_blocked(d,p):
 if p[1]<148 or p[1]>=CANVAS_H-tray_height(d)-120:return True
 selected=d['state']['editor'].get('selected_id','')
 if selected:
  t=tool(d);left=t[0]/SCALE-82;top=t[1]/SCALE-64
  if contains((left,top,304,148),p):return True
 return False

def visible_point(d,owner,art=None,part=None,transparent=False,label=None,underlying=False):
 rs=records(d);candidates=[];root=obj(d,owner);rootpoint=logical_base(d,root['x'],root['y']) if root else None
 for r in reversed(rs):
  if r['owner_id']!=owner or (art and r['art_id']!=art):continue
  im=rgba(r['source_path']);rx,ry,rw,rh=r['region'];alpha=im.getchannel('A').crop((rx,ry,rx+rw,ry+rh));box=alpha.getbbox()
  if not box:continue
  # Avoid mipmapped/antialiased edges and rounded adb coordinate ambiguity.
  mask=alpha.point(lambda a:255 if (a==0 if transparent else a>240) else 0).filter(ImageFilter.MinFilter(7))
  left,top,width,height=r['rect']
  focus=(rootpoint[0],rootpoint[1]-pitch(d)*(.9 if part=='hat' else .45)) if rootpoint else (left+width/2,top+height/2)
  for sy in range(3,rh-3,4):
   for sx in range(3,rw-3,4):
    if not mask.getpixel((sx,sy)):continue
    color=im.getpixel((rx+sx,ry+sy));p=(left+(sx+.5)/rw*width,top+(sy+.5)/rh*height)
    if ui_blocked(d,p):continue
    if part=='hat' and not (color[0]>210 and color[1]>210 and color[2]>190 and p[1]<rootpoint[1]-.55*pitch(d)):continue
    if part=='raised' and not p[1]<rootpoint[1]-.55*pitch(d):continue
    hit=picked(rs,p)
    if transparent:
     if hit and hit['owner_id']:continue
    elif hit is None or hit is not r:continue
    if underlying:
     behind=[q for q in rs[:rs.index(r)] if q['owner_id'] and contains(q['rect'],p) and rgba(q['source_path']).getpixel(source_pixel(q,p))[3]>25.5]
     if not behind:continue
    score=(p[0]-focus[0])**2+(p[1]-focus[1])**2
    candidates.append((score,p,r,(rx+sx,ry+sy),color,hit))
 assert candidates,('No visible unblocked offline atlas point',owner,art,part,transparent)
 _,point,record,source,color,hit=min(candidates,key=lambda q:q[0])
 proof={k:record[k] for k in ['owner_id','art_id','clip','direction','frame','source_path','region','rect']};proof.update(source_pixel=source,rgba=color,logical_point=point,screen_point=pixel(point),source_alpha_threshold=.1,selected_owner_expected='' if transparent else owner,top_record_owner=hit and hit['owner_id'],native_ui_unblocked=True)
 if rootpoint:proof.update(ground_root=rootpoint,grab_offset_tiles=[(point[i]-rootpoint[i])/pitch(d) for i in range(2)])
 if label:write(label+'-source-point',proof)
 return pixel(point)

def object_drag(d,owner,destination,part=None,label=None):
 start=visible_point(d,owner,part=part,label=label);o=obj(d,owner);base=cell(d,o['x'],o['y']);target=cell(d,*destination);end=tuple(target[i]+start[i]-base[i] for i in range(2));swipe(start,end,ms=650)
 return start,end
