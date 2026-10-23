import pathlib
P=pathlib.Path(__file__).resolve().parent
exec((P/'audit_identity_contact.py').read_text().split('# Independent persistent canonical resources')[0])
def differences(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):return [r for k in set(a)|set(b) for r in differences(a.get(k),b.get(k),path+'/'+str(k))]
 if isinstance(a,list):
  if len(a)!=len(b):return [(path+'/length',len(a),len(b))]
  return [r for i,(x,y) in enumerate(zip(a,b)) for r in differences(x,y,path+'/'+str(i))]
 if a!=b:return [(path,a,b)]
 return []
bpy.ops.wm.open_mainfile(filepath=str(R/'round-01.blend'));set_idle(bpy.context.scene);ca=obj(bpy.data.objects['collector__protective_shoe'],True)
bpy.ops.wm.open_mainfile(filepath=str(E/'inputs/frozen-main-v1/project.blend'));set_main(bpy.context.scene);bc=obj(bpy.data.objects['Registered 65 degree camera']);bh=obj(bpy.data.objects['body__hull'])
bpy.ops.wm.open_mainfile(filepath=str(R/'round-01-assembled.blend'));set_main(bpy.context.scene);dg=bpy.context.evaluated_depsgraph_get();tg=geometry(bpy.data.objects['collector__rear_seat_tongue'],dg);maxes=sorted([{'max':max((v-Vector(f['vertices'][0])).dot(Vector(f['normal'])) for v in tg['v']),'normal':f['normal'],'n':len(f['vertices'])} for f in tg['faces']],key=lambda x:x['max'],reverse=True)
r={'collectorDifferences':differences(ca,obj(bpy.data.objects['collector__protective_shoe'],True)),'cameraDifferences':differences(bc,obj(bpy.data.objects['Registered 65 degree camera'])),'hullDifferences':differences(bh,obj(bpy.data.objects['body__hull'])),'tongueConvexPlaneDiagnostics':maxes[:8]};(O/'identity-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2)[:9000])
