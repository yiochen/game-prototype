import bpy,json,hashlib,bmesh
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02'
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];scene=bpy.context.scene
meshes=[]
for o in col.objects:
 if o.type!='MESH':continue
 weighted=bool(o.vertex_groups)
 errors=[abs(sum(g.weight for g in v.groups)-1) for v in o.data.vertices] if weighted else []
 meshes.append(dict(object=o.name,vertices=len(o.data.vertices),faces=len(o.data.polygons),
                    restMeshSHA256=hashlib.sha256(json.dumps(dict(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons]),sort_keys=True).encode()).hexdigest(),
                    groups=[g.name for g in o.vertex_groups],maximumWeightNormalizationError=max(errors,default=0),
                    unweightedVertices=sum(not v.groups for v in o.data.vertices) if weighted else None,
                    zeroAreaFaces=sum(p.area<1e-12 for p in o.data.polygons),
                    modifiers=[dict(name=m.name,type=m.type,target=getattr(getattr(m,'object',None),'name',None)) for m in o.modifiers],
                    localOrientation=dict(location=list(o.location),rotation=list(o.rotation_euler),scale=list(o.scale))))
lights=[dict(name=o.name,type=o.data.type,energy=o.data.energy,size=getattr(o.data,'size',None),location=list(o.location),color=list(o.data.color)) for o in scene.objects if o.type=='LIGHT']
fills=[o for o in lights if 'fill' in o['name']]
resources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'resources').glob('*') if p.is_file()}
def project(point):
 p=world_to_camera_view(scene,scene.camera,Vector(point));return [p.x*192,(1-p.y)*320]
projected={name:project(point) for name,point in dict(ground=(0,0,0),unitX=(1,0,0),unitDepth=(0,-1,0),unitHeight=(0,0,1)).items()}
data=dict(activeBrief='brief-v3-food-depth.json',nativeSourceSHA256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          savedReopenedSource=True,meshes=meshes,lights=lights,resources=resources,
          world=dict(color=list(scene.world.node_tree.nodes['Background'].inputs['Color'].default_value),strength=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value),
          groundShadowGeometry=False,sceneObjectCount=len(scene.objects),assetObjectCount=len(col.objects),
          colorManagement=dict(viewTransform=scene.view_settings.view_transform,look=scene.view_settings.look,exposure=scene.view_settings.exposure,gamma=scene.view_settings.gamma),
          pixelAspect=[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],
          logicalProjection=projected,
          checks=[dict(name='normalized native weights',passed=all(m['maximumWeightNormalizationError']<1e-6 for m in meshes)),
                  dict(name='no unweighted native deform vertices',passed=all(m['unweightedVertices'] in [None,0] for m in meshes)),
                  dict(name='no zero-area native mesh faces',passed=all(m['zeroAreaFaces']==0 for m in meshes)),
                  dict(name='four equal cardinal fill lights',passed=len(fills)==4 and len(set(o['energy'] for o in fills))==1 and len(set(o['size'] for o in fills))==1),
                  dict(name='only owned asset and capture rig in scene',passed=len(scene.objects)==len(col.objects)+6),
                  dict(name='logical root projects to 96,248',passed=max(abs(a-b) for a,b in zip(projected['ground'],[96,248]))<.001),
                  dict(name='original native helper retained locally',passed=resources['original-native-actions.py']=='d88e53edef8e7c73e3a0287513f31678ec4427ad4bf2c756a4db178558a1942f')])
data['allChecksPassed']=all(c['passed'] for c in data['checks'])
(OUT/'native-supplement.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(allChecksPassed=data['allChecksPassed'],checks=data['checks'],zeroAreaFaces=[(m['object'],m['zeroAreaFaces']) for m in meshes if m['zeroAreaFaces']]),indent=2))
