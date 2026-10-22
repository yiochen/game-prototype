import bpy,json,sys,os
p=os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
cs=[c for c in bpy.data.collections if 'customer_june' in c.name.lower()]
scs=[s for s in bpy.data.scenes if any('customer_june' in o.name for o in s.objects)]
out={'blenderVersion':bpy.app.version_string,'scenes':[{'name':s.name,'objects':len(s.objects),'camera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage]} for s in scs], 'collections':[]}
for c in cs:
 obs=[]
 for o in c.all_objects:
  d={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'parent':o.parent.name if o.parent else None,'matrix': [list(r) for r in o.matrix_world],'hideRender':o.hide_render,'props':{k:str(o[k])[:500] for k in o.keys() if k!='_RNA_UI'}}
  if o.type=='MESH': d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),materials=[m.name for m in o.data.materials],modifiers=[{'type':m.type,'name':m.name} for m in o.modifiers],groups=[g.name for g in o.vertex_groups],bounds=[list(v) for v in o.bound_box])
  if o.type=='ARMATURE': d['bones']=[{'name':b.name,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform} for b in o.data.bones]
  obs.append(d)
 out['collections'].append({'name':c.name,'objects':obs})
json.dump(out,open(p+'/source/independent-scene-inspection.json','w'),indent=2)
print(json.dumps({'scenes':out['scenes'],'collections':[{'name':c['name'],'objects':len(c['objects'])} for c in out['collections']]},indent=2))
