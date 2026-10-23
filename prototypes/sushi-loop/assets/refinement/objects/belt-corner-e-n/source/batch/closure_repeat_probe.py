import bpy,pathlib,math,json,hashlib
R=pathlib.Path(__file__).resolve().parents[3]
for asset,dirs in [('belt-corner-n-w',['E','S','W']),('belt-corner-e-n',['S'])]:
 P=R/asset;O=P/'candidates/round-01/supplemental-01';O.mkdir(exist_ok=True);assert not (O/'supplemental-packet.json').exists(),'Immutable diagnostic already sealed; use a new versioned output';bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_'+asset+'.001'];r=next(o for o in c.objects if '__root.' in o.name);rows=[]
 for d in dirs:
  r.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]
  for frame in [1,25]:
   for repeat in ['a','b']:
    s.frame_set(frame);bpy.context.view_layer.update();p=O/f'repeat-control-{d}-f{frame:02}-{repeat}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);rows.append({'direction':d,'blenderFrame':frame,'repeat':repeat,'path':p.name})
 (O/'repeat-control-provenance.json').write_text(json.dumps({'projectSHA256':hashlib.sha256((P/'source/round-01.blend').read_bytes()).hexdigest(),'method':'Unchanged saved native candidate reopened; no material/geometry/renderer setting edits, repeat frame1 and25 twice. No source save.','renders':rows},indent=2))
