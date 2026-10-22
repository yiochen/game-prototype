import sys,runpy,json,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
H=Path(__file__).resolve().parent;S=H/'resources/source/round-01';F=runpy.run_path(str(S/'native_common.py'));globals().update({k:v for k,v in F.items() if k not in ['H','B','R','O']});OUT=H/'native-checks';OUT.mkdir(exist_ok=True)
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return [plain(t) for t in x]
 except:return str(x)
def scalar_rna(o,skip=()):
 d={}
 for p in o.bl_rna.properties:
  if p.identifier in skip or p.is_readonly or p.type not in ['BOOLEAN','INT','FLOAT','ENUM','STRING']:continue
  try:d[p.identifier]=plain(getattr(o,p.identifier))
  except:pass
 return d
def graph(t):
 if not t:return None
 ns=[]
 for n in t.nodes:
  z={'name':n.name,'type':n.bl_idname,'properties':scalar_rna(n,['name','label','location','width','height','dimensions','select','show_options','show_preview','show_texture','hide','color','use_custom_color']),'inputs':[(i.identifier,plain(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]}
  if hasattr(n,'color_ramp'):z['ramp']=[n.color_ramp.color_mode,n.color_ramp.interpolation,[(e.position,plain(e.color)) for e in n.color_ramp.elements]]
  if getattr(n,'node_tree',None):z['group']=graph(n.node_tree)
  ns.append(z)
 return {'nodes':ns,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links],'animated':bool(t.animation_data)}
def meshrecord(o):
 m=o.data
 return {'vertices':[plain(v.co) for v in m.vertices],'edges':[plain(e.vertices) for e in m.edges],'polygons':[(plain(p.vertices),p.material_index,p.use_smooth,plain(p.normal)) for p in m.polygons],'cornerNormals':[plain(n.vector) for n in m.corner_normals],'UV':{u.name:[plain(v.uv) for v in u.data] for u in m.uv_layers},'modifiers':[scalar_rna(z) for z in o.modifiers],'materials':[{'name':z.name,'settings':scalar_rna(z,['name']),'graph':graph(z.node_tree)} for z in m.materials]}
s,root,col=F['open_source']();F['apply']('upgraded-dock-ready');components=json.loads(col['canonicalComponents']);records={q['asset']:{n:meshrecord(bpy.data.objects[n]) for n in q['meshNames']} for q in components};rig=json.loads((H/'resources/candidates/round-01/rig.json').read_text());resolved={clip:{**{o:a for o,a in owners.items() if o in bpy.data.objects},**json.loads(col['canonicalVisibilityActions'])[clip]} for clip,owners in json.loads(root['nativeActions']).items()};assert rig['nativeActions']==resolved
gear={n for q in components for n in q['meshNames']};semantics=[]
for clip,owners in resolved.items():
 for owner,an in owners.items():
  a=bpy.data.actions[an]
  if owner in gear:assert all(fc.data_path in ['hide_viewport','hide_render'] for l in a.layers for st in l.strips for bag in st.channelbags for fc in bag.fcurves)
 for frame in [1,3.5,7,12,13,14]:
  F['apply'](clip,frame,'S');visible=sorted(n for n in gear if not bpy.data.objects[n].hide_render);assert len(visible)==(len(gear) if clip.startswith('upgraded-') else 0);semantics.append({'clip':clip,'frame':frame,'visibleCanonicalMeshCount':len(visible),'statusVisible':not bpy.data.objects['body__status_cyan_lens'].hide_render,'statusScale':plain(bpy.data.objects['body__status_cyan_lens'].scale),'motion':plain(bpy.data.objects['submarine-yellow__body_motion'].matrix_local)})
for clip in ['impact','upgraded-impact']:
 a=[q for q in semantics if q['clip']==clip];assert a[-1]['motion']==a[-2]['motion']
paths={'sub-hull-panels':S/'resources/approved-inputs/inputs/approved-equipment-preparation-v1/sub-hull-panels/source/round-01-neutral.blend','sub-harpoon-mount':S/'resources/approved-inputs/inputs/approved-equipment-preparation-v1/sub-harpoon-mount/source/round-02/project.blend','sub-collector-inlet':S/'resources/approved-inputs/inputs/approved-canonical-equipment-v1/sub-collector-inlet/source/round-02.blend'}
proof=[]
for q in components:
 asset=q['asset'];p=paths[asset];bpy.ops.wm.open_mainfile(filepath=str(p));actual={n:meshrecord(bpy.data.objects[n]) for n in q['meshNames']};diff=[n for n in actual if actual[n]!=records[asset][n]];proof.append({'asset':asset,'sourceSHA256':sha(p),'meshCount':len(actual),'directApprovedProjectVsMainMeshNormalsUVAllModifierParametersMaterialSettingsAndGraphEqual':not diff,'differingObjects':diff,'fingerprint':hd(actual)});assert not diff,(asset,diff)
(OUT/'independent-direct-resource-and-rig.json').write_text(json.dumps({'components':proof,'resolvedRigActualBindingsExact':True,'canonicalActionsVisibilityOnly':True,'baseHiddenUpgradedVisibleAllNativeMomentsSampled':True,'impactNativeTerminal13And14MotionHoldExact':True,'semantics':semantics,'method':'Own direct original approved .blend vs final raw mesh/normal/UV/modifier-parameter/material-field comparison. Root/mount identity separately checked by actual inverse extraction signed schemas and native phase audit. No component builders imported.'},indent=2)+'\n')
# Independent selected saved-source rendering; all four directions, base/upgraded plus inbetween.
s,root,col=F['open_source']();renders=[]
for d in ['N','E','S','W']:
 for clip,frame in [('dock-ready',1),('upgraded-dock-ready',1),('upgraded-travel',3.5)]:
  F['apply'](clip,frame,d);p=OUT/(clip+'-'+d+'-'+str(frame)+'.png');s.render.filepath=str(p);bpy.ops.render.render(write_still=True);renders.append({'clip':clip,'direction':d,'frame':frame,'path':str(p.relative_to(H)),'sha256':sha(p)})
(OUT/'independent-renders.json').write_text(json.dumps({'selectedSourceSHA256':sha(S/'project.blend'),'directNativeFrame':[640,768],'renders':renders},indent=2)+'\n');print('INDEPENDENT_DIRECT',proof,flush=True)
