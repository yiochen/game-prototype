"""Only canonical packed held-food dependency/fullUV/aspect change; no body/placement edits."""
import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-03';canonical=C/'resources/dish-salmon.png';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'round-02.blend')=='4f81f6e29a8b587ea03bf4a22e6ac4762585aea643bad7569c5a4506ea7a0073'
assert sha(canonical)=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;plane=bpy.data.objects['chef_lena__ground_root.002__held_dish-salmon__image_plane'];root=plane.parent.parent;tex=next(n for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');old=tex.image
before={'image':{'name':old.name,'size':list(old.size),'sha256':hashlib.sha256(old.packed_file.data).hexdigest(),'alphaMode':old.alpha_mode,'colorspace':old.colorspace_settings.name},'vertices':[list(v.co) for v in plane.data.vertices],'uv':[list(x.uv) for x in plane.data.uv_layers.active.data],'planeLocation':list(plane.location),'planeRotation':list(plane.rotation_euler)}
im=bpy.data.images.load(str(canonical),check_existing=False);im.name='Lena canonical salmon round03';im.alpha_mode=old.alpha_mode;im.colorspace_settings.name=old.colorspace_settings.name;im.filepath='//../candidates/round-03/resources/dish-salmon.png';im.pack();assert list(im.size)==[731,505];assert hashlib.sha256(im.packed_file.data).hexdigest()==sha(canonical);tex.image=im
if old.users==0:bpy.data.images.remove(old)
width=max(v.co.x for v in plane.data.vertices)-min(v.co.x for v in plane.data.vertices);height=width*505/731
for vertex in plane.data.vertices:
 if vertex.co.y>0:vertex.co.y=height
coords=[(0,0),(1,0),(1,1),(0,1)]
for poly in plane.data.polygons:
 for li in poly.loop_indices:plane.data.uv_layers.active.data[li].uv=coords[plane.data.loops[li].vertex_index]
plane['source_image']='../candidates/round-03/resources/dish-salmon.png';plane['source_sha256']=sha(canonical);plane['fixed_alpha_rectangle']=json.dumps([0,0,731,505]);plane['representation']='Approved canonical2D salmon, exact fullRGBA/fullUV/aspect; not modeled3D food'
food=json.loads(root['held_food_source']);food.update(path='../candidates/round-03/resources/dish-salmon.png',sha256=sha(canonical),alphaRectangleBottomOrigin=[0,0,731,505],canonicalSize=[731,505]);root['held_food_source']=json.dumps(food)
after={'image':{'name':im.name,'size':list(im.size),'sha256':sha(canonical),'alphaMode':im.alpha_mode,'colorspace':im.colorspace_settings.name},'vertices':[list(v.co) for v in plane.data.vertices],'uv':[list(x.uv) for x in plane.data.uv_layers.active.data],'planeLocation':list(plane.location),'planeRotation':list(plane.rotation_euler),'localWidth':width,'localHeight':height,'worldWidth':width*root.scale.x,'worldHeight':height*root.scale.y}
assert before['vertices'][:2]==after['vertices'][:2];assert before['planeLocation']==after['planeLocation'] and before['planeRotation']==after['planeRotation'];assert abs(after['worldWidth']-.35)<1e-7
r=json.loads((P/'recipe-round02.json').read_text());r.update(round=3,scene=sc.name,approvedBody={'path':'source/round-02.blend','sha256':sha(P/'round-02.blend')},frozenBrief={'path':'brief-v2-held-food.json','sha256':sha(O/'brief-v2-held-food.json')},revisionScope={'onlyChange':'Canonical held-food image/fullUV/aspect and provenance','before':before,'after':after,'bodyKnifeRigActionsMaterialsWorldLightCameraRenderFrozen':True,'foodRootPlacementVisibilityDriversFrozen':True});r['commands']={'build':'blender -b source/round-02.blend --python source/build_round03.py','renderAll192':'blender -b source/round-03.blend --python source/render_round03.py','auditAll192':'blender -b --python source/semantic_audit_round03.py','package':'Python with Pillow: source/package_round03.py'}
(P/'recipe-round03.json').write_text(json.dumps(r,indent=2)+'\n');dest=P/'round-03.blend';assert not dest.exists();bpy.ops.wm.save_as_mainfile(filepath=str(dest));(C/'food-delta-build.json').write_text(json.dumps({'before':before,'after':after,'sourceSHA256':sha(dest),'approvedBodySHA256':sha(P/'round-02.blend'),'packedResourceClosure':'Exact PNG embedded; same bytes externally in resources/dish-salmon.png','onlyNativeDelta':'Food textureimage binding, fullUV and two top Y coordinates; food provenance metadata'},indent=2))

# Finalize portable round metadata without any further .blend save.
exec(compile((P/'complete_recipe_round03.py').read_text(),str(P/'complete_recipe_round03.py'),'exec'))
