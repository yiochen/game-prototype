import bpy,pathlib,json,math,hashlib
from mathutils import Matrix
repo=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');base=repo/'prototypes/sushi-loop/assets/refinement/objects/belt-straight-e';rounddir=base/'candidates/round-01';out=base/'reviews/round-01-inspection';scene=bpy.context.scene
family=json.loads((base/'inputs/family-settings.json').read_text());validation=json.loads((rounddir/'validation.json').read_text())
# Compare actual material nodes, socket defaults, properties, ramps and links with frozen family data.
def norm(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [norm(x) for x in v]
 except:return str(v)
def near(a,b):
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(near(x,y) for x,y in zip(a,b))
 if isinstance(a,(float,int)) and isinstance(b,(float,int)):return abs(a-b)<1e-6
 return a==b
scene.frame_set(1);bpy.context.view_layer.update();audits=[]
for name,spec in family['materials'].items():
 actual=bpy.data.materials['S33_belt-straight-e_moving_deck_native' if 'moving_deck' in name else name];diff=[];nodes=actual.node_tree.nodes
 for specnode in spec['nodeTree']['nodes']:
  node=nodes.get(specnode['name'])
  if node is None:diff.append(['missingNode',specnode['name']]);continue
  if node.bl_idname!=specnode['type']:diff.append(['type',node.name])
  for prop,expected in specnode['properties'].items():
   if not near(norm(getattr(node,prop)),expected):diff.append(['property',node.name,prop])
  for kind in ['inputs','outputs']:
   for sock in specnode[kind]:
    if 'defaultValue' not in sock:continue
    actualsock=getattr(node,kind)[sock['index']]
    if not near(norm(actualsock.default_value),sock['defaultValue']):diff.append(['socket',node.name,kind,sock['index'],norm(actualsock.default_value),sock['defaultValue']])
  for key,value in specnode.items():
   if key=='colorRamp':
    ramp=node.color_ramp
    if not near(value['interpolation'],ramp.interpolation):diff.append(['colorRampInterpolation',node.name])
    if not near(value['elements'],[{'position':e.position,'color':list(e.color)} for e in ramp.elements]):diff.append(['colorRampElements',node.name])
 linkset={(l.from_node.name,list(l.from_node.outputs).index(l.from_socket),l.to_node.name,list(l.to_node.inputs).index(l.to_socket)) for l in actual.node_tree.links}
 expected={(l['fromNode'],l['fromSocketIndex'],l['toNode'],l['toSocketIndex']) for l in spec['nodeTree']['links']}
 if linkset!=expected:diff.append(['links'])
 if len(nodes)!=len(spec['nodeTree']['nodes']):diff.append(['nodeCount'])
 audits.append({'material':actual.name,'reference':name,'differences':diff})
ecoll=bpy.data.collections['S33_FB_belt-straight-e.001']
npath=repo/'prototypes/sushi-loop/assets/refinement/objects/belt-straight-n/source/round-09.blend'
with bpy.data.libraries.load(str(npath),link=False) as (src,dst):dst.collections=['S33_FB_belt-straight-n.001']
ncoll=dst.collections[0];ecoll.hide_render=True
def clone(coll,label):
 c=bpy.data.collections.new(label);scene.collection.children.link(c);mapping={o:o.copy() for o in coll.all_objects}
 for original,copy in mapping.items():
  c.objects.link(copy);copy.hide_render=False;copy.hide_viewport=False;copy.parent=mapping.get(original.parent)
 return c,next(o for o in c.all_objects if '__root.' in o.name)
cam=scene.camera;data=validation['nativeRunCamera'];cam.matrix_world=Matrix(data['worldMatrix']);cam.data.ortho_scale=data['orthoScale'];cam.data.shift_x,cam.data.shift_y=data['shift'];scene.render.resolution_x,scene.render.resolution_y=data['frame']
report={'projectSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'familyProjectSHA256':hashlib.sha256(npath.read_bytes()).hexdigest(),'actualFamilyGraphAudit':audits,'captures':[]}
mapping={'N':'E','E':'S','S':'W','W':'N'};rot={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
for pattern,d,index in [('ENE','S',12),('NEN','E',23),('EEE','W',0)]:
 roots=[];created=[]
 for j,identity in enumerate(pattern):
  c,root=clone(ecoll if identity=='E' else ncoll,f'Judge_{pattern}_{d}_{j}');created.append(c);facing=d if identity=='E' else mapping[d];root.rotation_euler.z=rot[facing];root.location=(j-1,0,0) if d in 'NS' else (0,1-j,0);roots.append(root)
 scene.frame_set(index+1);bpy.context.view_layer.update();scene.render.filepath=str(out/f'judge-native-{pattern}-{d}-{index:02}.png');bpy.ops.render.render(write_still=True)
 report['captures'].append({'pattern':pattern,'direction':d,'index':index,'path':scene.render.filepath,'rootMatrices':[[list(v) for v in r.matrix_world] for r in roots]})
 for c in created:
  for obj in list(c.objects):bpy.data.objects.remove(obj,do_unlink=True)
  bpy.data.collections.remove(c)
(out/'independent-mixed-native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
