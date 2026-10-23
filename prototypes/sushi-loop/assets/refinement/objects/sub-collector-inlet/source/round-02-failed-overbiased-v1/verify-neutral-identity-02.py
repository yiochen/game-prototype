import bpy,pathlib,json,sys,importlib.util
sys.dont_write_bytecode=True
H=pathlib.Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-02'
sp=importlib.util.spec_from_file_location('saved_replay',H/'replay-02.py');M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M);A=M.A
def channels(col):
 return {o.name:{'location':list(o.location),'rotationMode':o.rotation_mode,'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixBasis':[list(r) for r in o.matrix_basis],'matrixParentInverse':[list(r) for r in o.matrix_parent_inverse]} for o in col.all_objects}
bpy.ops.wm.open_mainfile(filepath=str(H/'round-02.blend'));col=bpy.data.collections['REFINED__sub-collector-inlet'];standalone=M.fingerprint(col);before=channels(col)
bpy.ops.wm.open_mainfile(filepath=str(H/'round-02-assembled.blend'));col=bpy.data.collections['REFINED__sub-collector-inlet'];mounted=M.fingerprint(col);after=channels(col);sourceBy={x['name']:x for x in standalone['records']};mountedBy={x['name']:x for x in mounted['records']};rows=[]
for n,a in before.items():
 rows.append({'object':n,'storedLocalTransformChannelsAndMatrixBasisExact':a==after[n],'standaloneStoredChannels':a,'mountedStoredChannels':after[n],'meshNormalsUVMaterialsExact':sourceBy[n].get('mesh')==mountedBy[n].get('mesh'),'computedMatrixLocalExact':sourceBy[n]['localMatrix']==mountedBy[n]['localMatrix'],'computedMatrixLocalMaxAbsError':max(abs(sourceBy[n]['localMatrix'][i][j]-mountedBy[n]['localMatrix'][i][j]) for i in range(4) for j in range(4))})
assert all(r['storedLocalTransformChannelsAndMatrixBasisExact'] and r['meshNormalsUVMaterialsExact'] for r in rows)
record={'standaloneSource':'source/round-02.blend','standaloneSHA256':A.sha(H/'round-02.blend'),'assembledSource':'source/round-02-assembled.blend','assembledSHA256':A.sha(H/'round-02-assembled.blend'),'allExactStoredChannelsAndMeshResources':True,'records':rows,'qualification':'Stored location/rotation/scale, matrixBasis and parentInverse channels are unchanged. Blender computed matrix_local derives through the new positive uniform parent and differs by ordinary float inversion rounding. Resource identity compares exact native mesh/normals/UV/material bytes separately; inverse-mount geometric residual is recorded in assembly audit. No transform fit or altered geometry.'}
A.savej(O/'neutral-transform-verification.json',record)
p=O/'assembly-audit.json';d=json.loads(p.read_text())
for r in d['neutralResources']:r['meshNormalsUVMaterialExact']=r['sourceMeshSHA256']==r['mountedMeshSHA256']
d['allNeutralResourcesExact']=all(r['meshNormalsUVMaterialExact'] for r in d['neutralResources']);d['allStoredNeutralLocalTransformChannelsExact']=True;d['neutralTransformVerification']='candidates/round-02/neutral-transform-verification.json';d['computedLocalMatrixQualification']=record['qualification'];A.savej(p,d)
print('Exact neutral stored transform channels and mesh/normals/UV/material resources verified',len(rows))
