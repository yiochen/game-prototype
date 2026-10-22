import bpy,json,pathlib
p=pathlib.Path(__file__).parent;out=[]
for typ in ['objects','meshes','shape_keys','materials','node_groups']:
 for x in getattr(bpy.data,typ):
  a=getattr(x,'animation_data',None)
  if a:out.append({'type':typ,'name':x.name,'action':a.action.name if a.action else None,'nla':len(a.nla_tracks),'drivers':len(a.drivers)})
(p/'frozen-main-animation-inventory.json').write_text(json.dumps(out,indent=2)+'\n')
print(out)
