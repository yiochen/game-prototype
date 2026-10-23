from pathlib import Path
p=Path('source/round-03.py').read_text().replace('round-03','round-04').replace('Round 03','Round 04').replace("'round':3","'round':4")
p=p.replace("o.data.materials.append(navy);bevel(o,.007,4)","o.data.materials.append(navy)")
p=p.replace("o.location.z=.825;o.data.materials.append", "o.location.z=.813;o.data.materials.append")
start=p.index('vs=[];fs=[];mi=[]\nlimits=')
end=p.index('# A shallow internal liner closes',start)
block='''# Keep the same five plank boundaries, but build a shallow curved top that is readable
# at logical size. Native top maximum remains exactly z=.838, original lid envelope.
vs=[];fs=[];mi=[]
limits=[-.5,-.17,-.055,.075,.19,.5]
plank_mats=[material('Native crowned lid plank %d'%i,h,.57,.2) for i,h in enumerate(['E2AE5C','E8B665','E5B15F','E9B768','E3AE5B'])]
for m in plank_mats:
 nodes=m.node_tree.nodes;links=m.node_tree.links;pbr=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 basecolor=tuple(pbr.inputs['Base Color'].default_value)
 coord=nodes.new('ShaderNodeTexCoord');coord.object=root
 sep=nodes.new('ShaderNodeSeparateXYZ');links.new(coord.outputs['Object'],sep.inputs[0])
 absolute=nodes.new('ShaderNodeMath');absolute.operation='ABSOLUTE';links.new(sep.outputs['Y'],absolute.inputs[0])
 square=nodes.new('ShaderNodeMath');square.operation='MULTIPLY';links.new(absolute.outputs[0],square.inputs[0]);links.new(absolute.outputs[0],square.inputs[1])
 spread=nodes.new('ShaderNodeMath');spread.operation='MULTIPLY';spread.inputs[1].default_value=7;spread.use_clamp=True;links.new(square.outputs[0],spread.inputs[0])
 mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=basecolor;mix.inputs[2].default_value=(basecolor[0]*.84,basecolor[1]*.78,basecolor[2]*.70,1)
 links.new(spread.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],pbr.inputs['Base Color'])
for i in range(5):
 poly=clip_x(clip_x(outline,limits[i]+(.002 if i else 0),True),limits[i+1]-(.002 if i<4 else 0),False)
 xmin=min(x for x,y in poly);xmax=max(x for x,y in poly)
 xs=sorted(set([xmin+(xmax-xmin)*j/12 for j in range(13)]+[x for x,y in poly]))
 ny=21;nx=len(xs);offset=len(vs)
 for x in xs:
  ys=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if abs(a[0]-b[0])<1e-9:
    if abs(x-a[0])<1e-7:ys.extend([a[1],b[1]])
   elif min(a[0],b[0])-1e-7<=x<=max(a[0],b[0])+1e-7:
    t=(x-a[0])/(b[0]-a[0]);ys.append(a[1]+t*(b[1]-a[1]))
  lo=min(ys);hi=max(ys);tx=2*(x-xmin)/(xmax-xmin)-1
  for j in range(ny):
   ty=2*j/(ny-1)-1;y=lo+(hi-lo)*j/(ny-1)
   z=.021-.011*abs(tx)**4-.005*abs(ty)**4
   vs.append((x,y,z))
 for a in range(nx-1):
  for j in range(ny-1):
   fs.append((offset+a*ny+j,offset+(a+1)*ny+j,offset+(a+1)*ny+j+1,offset+a*ny+j+1));mi.append(i)
 boundary=[offset+a*ny for a in range(nx)]
 boundary += [offset+(nx-1)*ny+j for j in range(1,ny)]
 boundary += [offset+a*ny+ny-1 for a in range(nx-2,-1,-1)]
 boundary += [offset+j for j in range(ny-2,0,-1)]
 bottom=[]
 for idx in boundary:
  x,y,z=vs[idx];bottom.append(len(vs));vs.append((x,y,-.016))
 fs.append(tuple(reversed(bottom)));mi.append(i)
 for j in range(len(boundary)):
  k=(j+1)%len(boundary);fs.append((boundary[j],bottom[j],bottom[k],boundary[k]));mi.append(i)
mesh=bpy.data.meshes.new('Original five lid planks - gently crowned closed solids');mesh.from_pydata(vs,[],fs);mesh.update();lid.data=mesh
for m in plank_mats:mesh.materials.append(m)
for face,idx in zip(mesh.polygons,mi):face.material_index=idx;face.use_smooth=True
for m in list(lid.modifiers):lid.modifiers.remove(m)
bevel(lid,.0025,3).harden_normals=False
# Replace the two original hoop solids with an actual rounded ring cross-section,
# preserving their native 14-gon perimeter and exact original z extents.
profile=[(.375,.030),(.393,.030),(.401,.028),(.406,.022),(.407,.014),(.407,-.014),(.406,-.022),(.401,-.028),(.393,-.030),(.375,-.030),(.370,-.020),(.370,.020)]
for ob in [o for o in collection.all_objects if '__iron_band_' in o.name]:
 original=[(ob.data.vertices[2*j].co.x,ob.data.vertices[2*j].co.y) for j in range(14)]
 points=[]
 for a,b in zip(original,original[1:]+original[:1]):
  for j in range(4):points.append((a[0]+(b[0]-a[0])*j/4,a[1]+(b[1]-a[1])*j/4))
 verts=[];faces=[];nk=len(profile);nt=len(points)
 for x,y in points:
  for radius,z in profile:verts.append((x*radius/.407,y*radius/.407,z))
 for a in range(nt):
  for j in range(nk):faces.append((a*nk+j,((a+1)%nt)*nk+j,((a+1)%nt)*nk+(j+1)%nk,a*nk+(j+1)%nk))
 me=bpy.data.meshes.new('Native navy hoop - rounded cross section');me.from_pydata(verts,[],faces);me.update();ob.data=me;me.materials.append(navy)
 for face in me.polygons:face.use_smooth=True
# Restrained geometry-normal tint supports the rounded edge at display size, with no
# horizontal azimuth preference, per-view change, texture image, or glossy highlight.
nodes=navy.node_tree.nodes;links=navy.node_tree.links;pbr=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');pbr.inputs['Roughness'].default_value=.48;pbr.inputs['Specular IOR Level'].default_value=.15
geom=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geom.outputs['Normal'],sep.inputs[0])
mapn=nodes.new('ShaderNodeMapRange');mapn.inputs['From Min'].default_value=-.65;mapn.inputs['From Max'].default_value=.9;mapn.inputs['To Min'].default_value=0;mapn.inputs['To Max'].default_value=1;mapn.clamp=True;links.new(sep.outputs['Z'],mapn.inputs['Value'])
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=rgba('102B58');mix.inputs[2].default_value=rgba('2D5289');links.new(mapn.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],pbr.inputs['Base Color'])
'''
p=p[:start]+block+p[end:]
p=p.replace("'roughnessNavy':.5", "'roughnessNavy':.48")
p=p.replace("'Native stave inward thickness'", "'Native stave inward thickness'")
p=p.replace("'Original 14-gon lid split along its original four seam positions into five native plank solids; four seam objects retained as recessed backing.'", "'Original 14-gon lid and four seam positions retained as five gently crowned plank solids with recessed native seam backing and broad restrained root-local warm variation.'")
p=p.replace("'Bevels provide real silhouette changes confined inside native mesh envelope.'", "'Real rounded hoop cross-sections and shallow plank crowns provide visible edge volume within the native bounds. Navy normal tint depends on world Z only; wood variation depends on root-local Y squared. Neither uses a horizontal light key or per-view treatment.'")
Path('source/round-04.py').write_text(p)
for name in ['audit','package']:
 p=Path('source/'+name+'-round-03.py').read_text().replace('round-03','round-04').replace("'round':3","'round':4").replace('round":3','round":4')
 if name=='package':
  p=p.replace("'round':3", "'round':4").replace("'roughnessNavy':.5", "'roughnessNavy':.48")
  p=p.replace("'Original lid perimeter and four seam positions retained as five real beveled plank solids.'", "'Original lid perimeter and four seam positions retained as five gently crowned solids with soft recessed contacts and broad restrained warm variation.'")
  p=p.replace("'Honey wood with readable lower staves, navy hoops, symmetric soft physical lighting.'", "'Honey wood and readable lower staves retained; navy hoops now have rounded native cross-sections and restrained upward-normal satin edge transitions under the same symmetric light.'")
 Path('source/'+name+'-round-04.py').write_text(p)
