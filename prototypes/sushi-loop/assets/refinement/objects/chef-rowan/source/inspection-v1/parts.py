import bpy,json
for o in bpy.data.collections['S33_CHARACTER_chef_rowan.001'].objects:
 if o.type!='MESH':continue
 vs=[v.co for v in o.data.vertices]
 print(json.dumps(dict(name=o.name,lo=[round(min(v[i] for v in vs),5) for i in range(3)],hi=[round(max(v[i] for v in vs),5) for i in range(3)],groups=[g.name for g in o.vertex_groups],mods=[dict(type=m.type,width=getattr(m,'width',None),segments=getattr(m,'segments',None)) for m in o.modifiers])))
