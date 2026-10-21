"""Correct only facing phase from approved round 02 using original publisher convention."""
import bpy,json,hashlib,math,re
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
publisher=(BASE/'../../../production/source/blender/native_actions.py').resolve();lines=publisher.read_text().splitlines()
line_index=next(i for i,line in enumerate(lines) if "asset['root'].rotation_euler.z={" in line)
source_line=lines[line_index].strip();mapping=eval(source_line.split('=',1)[1].rsplit('[direction]',1)[0],{'math':math})
assert mapping=={'S':0.,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
convention={'source':str(publisher),'projectRelativeSource':'../../../production/source/blender/native_actions.py','line':line_index+1,'sourceSha256':sha(publisher),'code':source_line,'rotationByDirectionRadians':mapping,'rotationByDirectionDegrees':{d:math.degrees(a) for d,a in mapping.items()},'previousRoundCorrespondence':{'N':'S','E':'W','S':'N','W':'E'}}

def identity():
 meshes=[{'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons],'materials':[m.name for m in o.data.materials],'modifiers':[{'type':m.type,'segments':getattr(m,'segments',None),'width':getattr(m,'width',None),'weight':getattr(m,'weight',None)} for m in o.modifiers]} for o in sorted(bpy.context.scene.objects,key=lambda o:o.name) if o.type=='MESH']
 materials=[]
 for m in sorted(bpy.data.materials,key=lambda m:m.name):
  nodes=[]
  for n in m.node_tree.nodes:
   inputs=[]
   for socket in n.inputs:
    if hasattr(socket,'default_value'):
     v=socket.default_value
     try:v=list(v)
     except TypeError:pass
     inputs.append([socket.identifier,v])
   nodes.append({'type':n.bl_idname,'name':n.name,'inputs':inputs,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'ramp':[(e.position,list(e.color)) for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None})
  materials.append({'name':m.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]})
 lights=[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in bpy.context.scene.objects if o.type=='LIGHT']
 data={'meshes':meshes,'materials':materials,'lights':lights,'worldBackground':[(n.type,[list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value')]) for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND']}
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def bounds():
 points=[]
 for o in bpy.context.scene.objects:
  if o.type=='MESH':
   e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();points.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
 return {'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]}
if __name__=='__main__':
 previous=BASE/'source/round-02.blend';previous_hash=sha(previous);bpy.ops.wm.open_mainfile(filepath=str(previous));scene=bpy.context.scene;root=bpy.data.objects['stool_blue__root.001'];bpy.context.view_layer.update();before=identity()
 root.rotation_euler.z=mapping['S'];scene['native_facings']='S=0,E=90,N=180,W=-90';scene['rotationByDirectionDegrees']=json.dumps(convention['rotationByDirectionDegrees']);scene['rotationByDirectionRadians']=json.dumps(mapping);scene['facingConventionSource']=f'native_actions.py:{line_index+1}';scene['savedFacing']='S';bpy.context.view_layer.update()
 path=BASE/'source/round-03.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
 (OUT/'direction-convention.json').write_text(json.dumps(convention,indent=2)+'\n')
 validation=json.loads((BASE/'candidates/round-02/validation.json').read_text());validation['round']=3;validation['sourceEdited']={'path':'source/round-03.blend','sha256':sha(path),'reproductionScript':'source/round-03.py','reproductionScriptSha256':sha(Path(__file__)),'scene':scene.name,'root':root.name};validation['directionConvention']=convention;validation['previousApprovedRound']={'project':'source/round-02.blend','sha256':previous_hash,'renderIdentitySignature':before};validation['checks']['approvedGeometryMaterialsLightsPreserved']=identity()==before;validation.pop('reopenedSource',None);validation.pop('alpha',None);validation.pop('previews',None)
 records=[]
 for d in ['N','E','S','W']:
  root.rotation_euler.z=mapping[d];bpy.context.view_layer.update();scene.frame_set(1);scene.render.filepath=str(OUT/f'static-{d}.png');bpy.ops.render.render(write_still=True)
  records.append({'direction':d,'clip':'static','sourceClip':'idle','frameIndex':0,'nativeFrame':1,'path':f'candidates/round-03/static-{d}.png','sha256':sha(scene.render.filepath),'rootRotationDegrees':math.degrees(mapping[d]),'rootRotationRadians':mapping[d],'actualEvaluatedRootRotationRadians':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'worldBounds':bounds(),'correspondingRound02Facing':convention['previousRoundCorrespondence'][d]})
 root.rotation_euler.z=mapping['S'];bpy.context.view_layer.update();validation['renders']=records;validation['status']='orientation-corrected-native-candidate-awaiting-independent-review';validation['checks']['facingConventionMatchesOriginalPublisher']=True
 (OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
 for name in ['camera','assetRecord','rig']:
  record=json.loads((BASE/f'source/round-02-{name}.json').read_text());record['rotationByDirectionDegrees']=convention['rotationByDirectionDegrees'];record['rotationByDirectionRadians']=mapping;record['directionConventionSource']={'path':convention['projectRelativeSource'],'line':convention['line'],'sha256':convention['sourceSha256']};record['nativeScene']=scene.name;record['savedFacing']='S'
  if name=='rig':record['project']='round-03.blend'
  (BASE/f'source/round-03-{name}.json').write_text(json.dumps(record,indent=2)+'\n')
 print('Completed corrected four native facings',convention)
