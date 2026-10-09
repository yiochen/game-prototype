"""Non-artistic atlas extraction: source crop, alpha-bounds trim, transparent margin.
Run with a Python runtime providing Pillow. Never recolors or modifies source alpha.
Generated objects sometimes crossed nominal grid lines, so measured clear gutters
are used below. Kept atlases and this metadata make every crop reproducible.
"""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parent
jobs=[]
character_names=['chef','chef_2','customer_1','customer_2','customer_3','customer_4']
for i,name in enumerate(character_names):
 if name in ['customer_1','customer_2','customer_3']:continue
 x=i%3;y=i//3;jobs.append(('characters-atlas.png',name,(x*512,y*512,(x+1)*512,(y+1)*512)))
prop_names=['submarine','gear','rock','seat','plant','salmon','cucumber','shrimp','eel']
# The submarine's full propeller ends below the nominal418px first row.
rows=[0,434,836,1254]
for i,name in enumerate(prop_names):
 x=i%3;y=i//3;jobs.append(('props-atlas.png',name,(x*418,rows[y],(x+1)*418,rows[y+1])))
jobs.extend([
 ('creatures-atlas.png','creature_salmon',(0,0,535,435)),
 ('creatures-atlas.png','creature_shrimp',(535,0,1000,482)),
 ('creatures-atlas.png','creature_eel',(1000,0,1536,458)),
 ('creatures-atlas.png','kelp',(0,435,535,1024)),
 ('creatures-atlas.png','coral',(535,482,1000,1024)),
 ('creatures-atlas.png','portal',(1000,458,1536,1024)),
 # Root's2x2 atlas has taller upper props and shorter lower panel objects.
 ('ui-props-atlas.png','rubble_cluster',(0,0,682,736)),
 ('ui-props-atlas.png','blackboard',(682,0,1254,736)),
 ('ui-props-atlas.png','paper_panel',(0,736,628,1254)),
 ('ui-props-atlas.png','coral_panel',(628,736,1254,1254)),
])
for row in range(2):
 for column in range(3):
  name=('customer_walk_' if row==0 else 'customer_')+str(column+1)
  jobs.append(('customer-poses-atlas.png',name,(column*512,row*512,(column+1)*512,(row+1)*512)))
metadata={'operation':'crop only; source RGBA preserved;16px transparent margin','atlases':{},'sprites':{}}
for atlas,name,region in jobs:
 im=Image.open(ROOT/atlas).convert('RGBA')
 alpha=im.getchannel('A')
 assert alpha.getextrema()[0]==0,atlas+' is not transparent'
 metadata['atlases'][atlas]={'size':list(im.size),'mode':im.mode,'zero_alpha_fraction':round(alpha.histogram()[0]/(im.width*im.height),4)}
 cell=im.crop(region)
 # Ignore invisible residual alpha to locate its meaningful painted silhouette;
 # original RGBA (including antialiasing) is retained within a generous crop.
 box=cell.getchannel('A').point(lambda a:255 if a>16 else 0).getbbox()
 assert box,name
 left=max(0,box[0]-3);top=max(0,box[1]-3);right=min(cell.width,box[2]+3);bottom=min(cell.height,box[3]+3)
 cropped=cell.crop((left,top,right,bottom))
 padded=Image.new('RGBA',(cropped.width+32,cropped.height+32),(0,0,0,0))
 padded.paste(cropped,(16,16))
 padded.save(ROOT/(name+'.png'))
 metadata['sprites'][name]={'atlas':atlas,'source_region':list(region),'trim': [left,top,right,bottom],'padding':16,'output_size':list(padded.size)}
 print(name,padded.size)
(ROOT/'atlas-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
