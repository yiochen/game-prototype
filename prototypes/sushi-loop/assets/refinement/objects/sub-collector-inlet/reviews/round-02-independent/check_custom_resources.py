import bpy,pathlib,json
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent

def val(v):
 if hasattr(v,'to_dict'):return val(v.to_dict())
 if isinstance(v,dict):return{k:val(x) for k,x in v.items()}
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return[val(x) for x in v]
 except:return str(v)
def get():
 return{o.name:{'object':{k:val(o[k]) for k in o.keys()},'data':{k:val(o.data[k]) for k in o.data.keys()} if o.data else None} for o in bpy.context.scene.objects}
bpy.ops.wm.open_mainfile(filepath=str(E/'inputs/frozen-main-v1/project.blend'));a=get();bpy.ops.wm.open_mainfile(filepath=str(E/'source/round-02-assembled.blend'));b=get();diff=[k for k in a if a[k]!=b.get(k)];r={'frozenOriginalCustomObjectDataPropertiesExact':not diff,'differences':diff,'frozenRootCustomProperties':a['submarine-yellow__root']['object'],'mountedRootCustomProperties':b['submarine-yellow__root']['object']};(O/'custom-resource-identity.json').write_text(json.dumps(r,indent=2)+'\n');print('CUSTOM_PROPERTIES',not diff,diff)
