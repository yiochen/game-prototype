import bpy,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03';a=json.loads((O/'native-audit.json').read_text());root=bpy.data.objects['rock-wall-middle__root'];side=bpy.data.objects['rock-wall-middle__continuous_carved_stone'];me=side.data
vwest=[v for v in me.vertices if abs(v.co.x+.5)<1e-7];veast=[v for v in me.vertices if abs(v.co.x-.5)<1e-7];west=sorted(vwest,key=lambda v:(round(v.co.y,7),round(v.co.z,7)));east=sorted(veast,key=lambda v:(round(v.co.y,7),round(v.co.z,7)))
colors=me.color_attributes['stone_albedo']
ports={'lockedProfileYThenZ':[[-.5,0],[.5,0],[.5,.67],[.45,1.04],[.31,1.15],[-.31,1.15],[-.45,1.04],[-.5,.67]],'endpointVertexCountEach':len(west),'exactXPlanes':[-.5,.5],'maxPairYZDelta':max((Vector((w.co.y,w.co.z))-Vector((e.co.y,e.co.z))).length for w,e in zip(west,east)),'maxPairColorDelta':max(abs(colors.data[w.index].color[k]-colors.data[e.index].color[k]) for w,e in zip(west,east) for k in range(4)),'maxPairNormalDelta':max((w.normal-e.normal).length for w,e in zip(west,east)),'endpointProfileVertexSHA256':hashlib.sha256(b''.join(struct.pack('ff',v.co.y,v.co.z) for v in west)).hexdigest()}
profile=[Vector(p) for p in ports['lockedProfileYThenZ']]
def segdist(p,a,b):
 ab=b-a;t=max(0,min(1,(p-a).dot(ab)/ab.length_squared));return (p-(a+t*ab)).length
ports['maxVertexDistanceFromLockedProfile']=max(min(segdist(Vector((v.co.y,v.co.z)),profile[i],profile[(i+1)%8]) for i in range(8)) for v in west+east)
a['connectorsMeasured']=ports
a['geometry']={'kind':'native full 3D carved crag with side surface and interior-relief terminal surfaces','materialCount':1,'imagesUsed':[],'allObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world]} for o in bpy.context.scene.objects],'nativeMeshResourceSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for o in [side]+[o for o in bpy.context.scene.objects if o.type=='MESH' and o!=side] for v in o.data.vertices)).hexdigest(),'cameras':1,'rigs':0,'shapekeys':0,'targetRasterPlanes':0}
a['resources']={'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'packed':bool(x.packed_file),'path':x.filepath} for x in bpy.data.images],'closure':'No used external resources: materials, vertex albedo, geometry, lighting and camera are stored inside the .blend.'}
a['contact']={'groundZ':0,'fullCellFootprint':[-.5,-.5,.5,.5],'mainContact':'Continuous full rectangular bottom profile edge across native X from -.5 to .5; no support strip removed','heightBudget':1.17,'sideReliefAllowance':.011}
a['futureGodotVerification']='Pending if rock-wall-middle is later added. Current SELECTION 34 and Godot catalog manifest exclude this asset/family; browser SpriteScene is the current applicable consumer.'
(O/'native-audit.json').write_text(json.dumps(a,indent=2))
print(json.dumps(ports,indent=2))
