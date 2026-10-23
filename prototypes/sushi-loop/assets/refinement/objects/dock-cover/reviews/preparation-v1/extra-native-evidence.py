from pathlib import Path
p=Path(__file__).with_name('audit-native.py');s=p.read_text();exec(s[:s.index("audit={'sourceSHA256'")])
raw={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'note':'Correct visible evaluated matrices and source geometry. The earlier hidden raw inventory matrices were stale; use this and native-phase-audit for measurements.','geometry':[],'inbetweenRenders':[]}
actions.apply_clip(asset,rig,'covered',1,'S',sc);sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
for o in objs:
 eo=o.evaluated_get(dg);me=eo.to_mesh();raw['geometry'].append({'name':o.name,'matrix':[list(a) for a in eo.matrix_world],'verticesWorld':[list(eo.matrix_world@v.co) for v in me.vertices],'polygons':[[i for i in p.vertices] for p in me.polygons],'uvLayers':[{ 'name':u.name,'uv':[list(v.uv) for v in u.data]} for u in me.uv_layers],'materials':[m.name if m else None for m in me.materials],'hideRender':o.hide_render});eo.to_mesh_clear()
for clip in ['covered','uncover']:
 for d in ['S','E']:
  for f in [1.5,6.5,11.5]:
   actions.apply_clip(asset,rig,clip,1,d,sc);sc.frame_set(math.floor(f),subframe=f%1);sc.view_layers[0].update();q=OUT/'native-inbetweens'/f'{clip}-{d}-{f}.png';q.parent.mkdir(exist_ok=True);sc.render.filepath=str(q);bpy.ops.render.render(write_still=True,scene=sc.name);raw['inbetweenRenders'].append({'clip':clip,'direction':d,'frame':f,'path':str(q.relative_to(OBJ/'reviews')),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()})
(OUT/'native-evaluated-geometry.json').write_text(json.dumps(raw,indent=2)+'\n')
