"""Curtain restoration UI targets (unchanged from alignment) from current source; re-check frozen source before actual input."""
from qa_common import *
WIDTH=1080.0
HEIGHT=2400.0
SCALE=WIDTH/720.0
CANVAS_H=HEIGHT/SCALE
def pixel(point):return tuple(v*SCALE for v in point)
def cell(d,x,y):
 floor=d['configuration']['floor']
 pitch=(720.-48.)/floor.get('viewport_columns',floor.get('columns',7))
 origin=(24.,max(24.,(CANVAS_H-floor.get('rows',13)*pitch)*.5))
 camera=d['state']['camera']
 return pixel((origin[0]+(x+.5-camera['x'])*pitch,origin[1]+(y+.5-camera['y'])*pitch))
def tray_height(d):return 272. if d['state']['editor']['tray_open'] else 54.
def layer(d,key):
 index=['people','layout','floor'].index(key)
 return pixel(([104.,288.,456.][index],CANVAS_H-tray_height(d)-60.))
def shop(d):return pixel((620.,CANVAS_H-tray_height(d)-60.))
def drawer(d):
 layer=d['state']['editor']['layer'];page=d['state']['editor']['page']
 allowed={'layout':['belt','seat','decor'],'people':['chef'],'floor':['floor']}[layer]
 total=len([item for item in d['state']['inventory'] if item['kind'] in allowed])
 slots=4 if layer=='layout' else 3
 count=max(1,min(slots,total-page*slots))
 card_width={'layout':104.,'people':132.,'floor':160.}[layer]
 contents=count*card_width+(count-1)*8.
 width=contents+24.
 return (720.-width)*.5,width,card_width,count

def page(d,next=True):
 left,width,_,_=drawer(d)
 return pixel((left+width+50. if next else left-50.,CANVAS_H-272.+14.+100.))
def card(d,index):
 left,width,card_width,count=drawer(d)
 assert 0<=index<count
 return pixel((left+12.+index*(card_width+8.)+card_width*.5,CANVAS_H-272.+14.+100.))
def tool(d,remove=False):
 selected=obj(d,d['state']['editor']['selected_id']);base=cell(d,selected['x'],selected['y']);base=(base[0]/SCALE,base[1]/SCALE)
 left=min(max(base[0]-152.,12.),404.)
 upper=148.;lower=max(upper,CANVAS_H-tray_height(d)-120.-168.)
 top=base[1]-236.
 if top<upper and base[1]+80.<=lower:top=base[1]+80.
 top=min(max(top,upper),lower)
 return pixel((left+(222. if remove else 82.),top+64.))
EDIT=pixel((137.,CANVAS_H-101.))
LIVE=pixel((613.,80.))
