"""Read-only native geometry and capture verification; run in Blender."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Sushi Loop Uniform Wood Backdrop35 Study'];bpy.context.window.scene=scene
camera=scene.camera;book=json.loads((ROOT/'camera.json').read_text())
for collection in scene.collection.children:
    if collection.name.startswith('S33_PROP_uniform35-'):collection.hide_viewport=False
bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get();records={}
for name,record in book['assets'].items():
    points=[]
    for obj in bpy.data.collections[record['collection']].all_objects:
        if obj.type not in {'MESH','CURVE'}:continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        points.extend([obj.matrix_world@v.co for v in mesh.vertices]);evaluated.to_mesh_clear()
    xs=[v.x for v in points]
    ys=[-math.sin(math.radians(35))*v.y-math.cos(math.radians(35))*v.z for v in points]
    image=bpy.data.images.load(str(ROOT/record['image']),check_existing=False)
    pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels)
    alpha=pixels.reshape(image.size[1],image.size[0],4)[:,:,3]
    assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())<.01,'Clipped frame: '+name
    occupied=np.argwhere(alpha>.01)
    source_pixels=list(image.size)
    bpy.data.images.remove(image)
    records[name]={'worldWidth':max(xs)-min(xs),'projectedHeight':max(ys)-min(ys),'projectedTop':min(ys),'projectedBottom':max(ys),'vertices':len(points),'sourcePixels':source_pixels,'alphaBoundsBottomUp':[int(occupied[:,1].min()),int(occupied[:,0].min()),int(occupied[:,1].max()+1),int(occupied[:,0].max()+1)],'transparentGutters':True}
collection=bpy.data.collections[book['assets']['gate']['collection']]
def edge(fragment,operation):
    obj=next(o for o in collection.all_objects if fragment in o.name)
    return operation((obj.matrix_world@Vector(c)).x for c in obj.bound_box)
opening=edge('inner_pillar_1',min)-edge('inner_pillar_-1',max)
look=camera.rotation_euler.to_matrix()@Vector((0,0,-1))
elevation=math.degrees(math.asin(abs(look.z)))
assert abs(opening-2)<.00001
assert abs(records['gate']['worldWidth']-4)<.00001
assert all(abs(r['projectedHeight']-3)<.01 for r in records.values()),records
assert abs(elevation-35)<.001
assert scene.render.pixel_aspect_x==scene.render.pixel_aspect_y==1
receipt={'cameraElevation':35,'measuredElevation':elevation,'cameraType':camera.data.type,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'clearInnerWidth':opening,'assets':records,'auditRecipeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'nativeSourceSha256':hashlib.sha256((ROOT/'source/restaurant-backdrop-35.blend').read_bytes()).hexdigest(),'renderRecipeSha256':hashlib.sha256((ROOT/'source/render_backdrop.py').read_bytes()).hexdigest(),'buildRecipeSha256':hashlib.sha256((ROOT/'source/build_backdrop.py').read_bytes()).hexdigest()}
wall=bpy.data.collections[book['assets']['wall-plain']['collection']]
features=[o.name for o in wall.all_objects if any(token in o.name for token in ['window','pillar','post_'])]
assert not features,features
roofs=[o for o in wall.all_objects if 'flat_roof_tile_' in o.name]
assert roofs and all(len(o.data.vertices)==8 and len(o.data.polygons)==6 for o in roofs)
wall_image=bpy.data.images.load(str(ROOT/'renders/wall-plain.png'),check_existing=False)
pixels=np.empty(len(wall_image.pixels),dtype=np.float32);wall_image.pixels.foreach_get(pixels)
rgba=pixels.reshape(wall_image.size[1],wall_image.size[0],4)
x=int(book['assets']['wall-plain']['anchor'][0]*3)
wall_samples=[]
for tile_y in [1.1,1.8,2.45]:
    y=int(wall_image.size[1]-(32+tile_y*128)*3)
    wall_samples.append([float(v) for v in rgba[y,x,:3]])
difference=max(max(values)-min(values) for values in zip(*wall_samples))
assert difference<.005,wall_samples
bpy.data.images.remove(wall_image)
receipt['woodWallAudit']={'decorationObjects':features,'roofTileVertexCounts':[len(o.data.vertices) for o in roofs],'wallRgbSamples':wall_samples,'maximumHeightColorDifference':difference,'lighting':'uniform ambient albedo; no height ramp or baked cast shadows','wallColor':'C6A267','baseboardObjects':[o.name for o in wall.all_objects if 'baseboard' in o.name]}
assert len(receipt['woodWallAudit']['baseboardObjects'])==2
assert not scene.render.use_compositing
(ROOT/'geometry-audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('BACKDROP35_AUDIT',json.dumps(receipt))
