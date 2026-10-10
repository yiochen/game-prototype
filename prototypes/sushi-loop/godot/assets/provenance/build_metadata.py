"""Measure original PNG atlas regions; do not modify any production image pixels."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw
from inspect_atlases import components

base=Path(__file__).parent.parent
production=base/'production'
manifest={}
verification={}

def add(name,sheet,bbox,anchor=(.5,1.0)):
    im=Image.open(production/f'{sheet}.png')
    l,t,r,b=bbox
    l=max(0,l-3);t=max(0,t-3);r=min(im.width,r+3);b=min(im.height,b+3)
    manifest[name]={'file':f'res://assets/production/{sheet}.png','region':[l,t,r-l,b-t],'anchor':list(anchor)}

def grid_components(sheet,columns,rows):
    im=Image.open(production/f'{sheet}.png')
    major=components(production/f'{sheet}.png')[:columns*rows]
    byrow=sorted(major,key=lambda item:(item[1][1]+item[1][3])/2)
    return [box for row in range(rows) for _,box in sorted(byrow[row*columns:(row+1)*columns],key=lambda item:item[1][0])]

chef=grid_components('chef',4,2)
for row,pose in enumerate(['work','hold']):
    for col,direction in enumerate(['down','up','right','left']):
        add(f'chef_{pose}_{direction}','chef',chef[row*4+col])
        if row==0:add(f'chef_{direction}','chef',chef[col])
manifest['chef_work']=manifest['chef_work_down']
manifest['chef_hold']=manifest['chef_hold_down']

guests=grid_components('customers',4,4)
for identity,row in [('a',0),('b',2)]:
    for pose,offset in [('walk',0),('seated',1)]:
        for col,direction in enumerate(['down','up','left','right']):
            key=f'guest_{identity}_{direction}' if pose=='walk' else f'guest_{identity}_{pose}_{direction}'
            add(key,'customers',guests[(row+offset)*4+col])
    manifest[f'guest_{identity}_seated']=manifest[f'guest_{identity}_seated_up']

waiting=grid_components('customers_waiting',4,2)
for row,identity in enumerate(['a','b']):
    for col,direction in enumerate(['down','up','left','right']):
        add(f'guest_{identity}_waiting_{direction}','customers_waiting',waiting[row*4+col])
        manifest[f'guest_{identity}_eating_{direction}']=manifest[f'guest_{identity}_seated_{direction}']
    manifest[f'guest_{identity}_waiting']=manifest[f'guest_{identity}_waiting_up']
    manifest[f'guest_{identity}_eating']=manifest[f'guest_{identity}_eating_up']

props=grid_components('props',4,2)
for name,box in zip(['stool','salmon_nigiri','blackboard','plant','barrel','crate','lantern','plant_tall'],props):add(name,'props',box)

belts=grid_components('belts',3,2)
for name,box in zip(['belt_vertical','belt_horizontal','belt_end_up','belt_end_down','belt_end_left','belt_end_right'],belts):add(name,'belts',box,(.5,.5))
manifest['belt_endpoint']=manifest['belt_end_right']

clutter=Image.open(production/'clutter_spaced.png').getchannel('A')
for i,name in enumerate(['pile_sofa','pile_shelf','pile_cart','covered_dock']):
    x,y=(i%2)*768,(i//2)*512
    l,t,r,b=clutter.crop((x,y,x+768,y+512)).point(lambda n:255 if n>16 else 0).getbbox()
    add(name,'clutter_spaced',[x+l,y+t,x+r,y+b])
manifest['floor_wood']={'file':'res://assets/production/floor_wood.png','region':[0,0,1254,1254],'anchor':[0,0]}
manifest['app_icon']={'file':'res://assets/production/app_icon.png','region':[0,0,1254,1254],'anchor':[.5,.5]}
entrance_alpha=Image.open(production/'entrance.png').getchannel('A')
add('entrance','entrance',entrance_alpha.point(lambda n:255 if n>16 else 0).getbbox())
(production/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

atlasdir=production/'atlas';atlasdir.mkdir(exist_ok=True)
for name,entry in manifest.items():
    x,y,w,h=entry['region']
    (atlasdir/f'{name}.tres').write_text('[gd_resource type="AtlasTexture" load_steps=2 format=3]\n\n[ext_resource type="Texture2D" path="'+entry['file']+'" id="1"]\n\n[resource]\natlas = ExtResource("1")\nregion = Rect2('+', '.join(str(v) for v in [x,y,w,h])+')\nfilter_clip = true\n')

for path in production.glob('*.png'):
    im=Image.open(path)
    alpha=im.getchannel('A') if 'A' in im.getbands() else None
    verification[path.name]={'size':list(im.size),'mode':im.mode,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if alpha:
        hist=alpha.histogram()
        verification[path.name].update({'alpha_range':list(alpha.getextrema()),'fully_transparent_fraction':hist[0]/(im.width*im.height)})
(base/'provenance'/'image-verification.json').write_text(json.dumps(verification,indent=2)+'\n')

# Inspection thumbnail only: source images remain untouched.
keys=['chef_down','chef_up','chef_left','chef_right','chef_hold','guest_a_down','guest_a_waiting_down','guest_a_eating_down','guest_a_waiting_left','guest_a_eating_left','guest_b_waiting_down','guest_b_eating_down','guest_b_waiting_right','guest_b_eating_right','stool','salmon_nigiri','blackboard','belt_horizontal','belt_endpoint','plant','barrel','crate','lantern','pile_sofa','pile_shelf','pile_cart','covered_dock','entrance']
preview=Image.new('RGB',(840,800),'#ead9b9');draw=ImageDraw.Draw(preview)
for i,key in enumerate(keys):
    entry=manifest[key];im=Image.open(production/Path(entry['file']).name)
    x,y,w,h=entry['region'];tile=im.crop((x,y,x+w,y+h))
    tile.thumbnail((105,110),Image.Resampling.LANCZOS)
    left=(i%6)*140+(140-tile.width)//2;top=(i//6)*160+122-tile.height
    preview.paste(tile,(left,top),tile)
    draw.text(((i%6)*140+5,(i//6)*160+133),key,fill='#263947')
preview.save(base/'provenance'/'contact-sheet.png')
print('Wrote',len(manifest),'regions and unmodified-source AtlasTexture resources.')
