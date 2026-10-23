from pathlib import Path
p=Path('prototypes/sushi-loop/assets/refinement/objects/wall-outer-corner/source/round-02.py')
s=p.read_text().replace('round-02','round-03')
needle=" mesh=bpy.data.meshes.new(name+' native continuous bend surface');mesh.from_pydata(verts,[],faces);mesh.update()"
insert=""" # Weld collapsed inner-turn samples into actual continuous native topology.
 # Identical points use identical path coordinates there. Preserve custom loop
 # treatment after welding; no render geometry extension or image correction.
 vnew=[];cnew=[];nnew=[];remap={};canonical={}
 for i,v in enumerate(verts):
  key=tuple(round(k,7)for k in v)
  if key not in canonical:
   canonical[key]=len(vnew);vnew.append(v);cnew.append(coords[i]);nnew.append(normal_specs[i])
  remap[i]=canonical[key]
 fnew=[]
 for f in faces:
  f2=[]
  for i in f:
   j=remap[i]
   if not f2 or f2[-1]!=j:f2.append(j)
  if len(f2)>1 and f2[0]==f2[-1]:f2.pop()
  if len(set(f2))>=3:fnew.append(tuple(f2))
 verts,coords,normal_specs,faces=vnew,cnew,nnew,fnew
 mesh=bpy.data.meshes.new(name+' native continuous bend surface');mesh.from_pydata(verts,[],faces);mesh.update()"""
assert needle in s
s=s.replace(needle,insert)
p.with_name('round-03.py').write_text(s)

