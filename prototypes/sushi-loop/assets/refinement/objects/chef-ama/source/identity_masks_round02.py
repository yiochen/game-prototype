"""Native evaluated primary-ray identity masks, diagnostic only; no scene/save/render edits."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02';sys.path.insert(0,str(P));import native_actions_round02 as NA
role='source' if '--source' in sys.argv else 'candidate';sc=bpy.data.scenes['Ama warm soft round01'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_ama.002'];root=bpy.data.objects['chef_ama__ground_root.002'];plane=next(o for o in coll.all_objects if '__image_plane' in o.name);rig=json.loads((P/'rig-round02.json').read_text());asset={'collection':coll,'root':root};im=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');alpha=np.asarray(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)[:,:,3];uv=np.array([v.uv[:] for v in plane.data.uv_layers.active.data]);controls=[('idle','S',0),('work','S',0),('hold','S',0),('hold','N',0),('hold','N',5),('hold','N',11),('hold','E',5),('hold','W',5),('load','N',5),('load','E',5),('load','W',5),('load','S',11)]
def xy(v):q=world_to_camera_view(sc,sc.camera,v);return np.array([q.x*384,(1-q.y)*640])
def sample(u,v):
 h,w=alpha.shape;x=u*w-.5;y=v*h-.5;ix=int(math.floor(x));iy=int(math.floor(y));fx=x-ix;fy=y-iy
 def px(xx,yy):return float(alpha[yy,xx]) if 0<=xx<w and 0<=yy<h else 0.
 return px(ix,iy)*(1-fx)*(1-fy)+px(ix+1,iy)*fx*(1-fy)+px(ix,iy+1)*(1-fx)*fy+px(ix+1,iy+1)*fx*fy
out=C/'identity-masks'/role;out.mkdir(parents=True,exist_ok=True);rows=[]
for clip,d,i in controls:
 NA.apply_clip(asset,rig,clip,i+1,d,sc);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();points=[];faces=[]
 for o in coll.all_objects:
  if o.type!='MESH' or o==plane or o.hide_render or not o.visible_camera:continue
  e=o.evaluated_get(dg);me=e.to_mesh();n=len(points);points.extend(e.matrix_world@v.co for v in me.vertices);faces.extend(tuple(n+x for x in p.vertices) for p in me.polygons);e.to_mesh_clear()
 tree=BVHTree.FromPolygons(points,faces,all_triangles=False);right=sc.camera.matrix_world.col[0].xyz.normalized();up=sc.camera.matrix_world.col[1].xyz.normalized();forward=-sc.camera.matrix_world.col[2].xyz.normalized();originpx=xy(Vector((0,0,0)));ppu=float(np.linalg.norm(xy(right)-originpx));pe=plane.evaluated_get(dg);corners=[pe.matrix_world@v.co for v in pe.data.vertices];p0=xy(corners[0]);basis=np.stack([xy(corners[1])-p0,xy(corners[3])-p0],axis=1);inverse=np.linalg.inv(basis);body=np.zeros((640,384),np.uint8);food=np.zeros_like(body);foodalpha=np.zeros((640,384),np.float32);active=not plane.hide_render and not plane.parent.hide_render
 for y in range(640):
  for x in range(384):
   # Identity is sampled at native pixel centres, without claiming antialias/denoiser coverage.
   sp=right*((x+.5-originpx[0])/ppu)+up*((originpx[1]-y-.5)/ppu);origin=sp-forward*10;hit=tree.ray_cast(origin,forward,100)
   if hit[0] is not None:body[y,x]=255
   if not active:continue
   u,v=inverse@(np.array([x+.5,y+.5])-p0)
   if not (0<=u<=1 and 0<=v<=1):continue
   q=uv[0]+u*(uv[1]-uv[0])+v*(uv[3]-uv[0]);a=sample(*q)
   if a<=1/255:continue
   distance=(corners[0]-origin).dot(forward)
   if hit[0] is None or hit[3]>=distance-1e-5:food[y,x]=255;foodalpha[y,x]=a
 path=out/(f'{clip}-{d}-{i:03d}.npz');np.savez_compressed(path,body=body,food=food,foodAlpha=foodalpha)
 rows.append({'clip':clip,'direction':d,'index':i,'path':str(path.relative_to(B)),'bodyPrimaryRayPixels':int(np.count_nonzero(body)),'visibleFoodAlpha1Pixels':int(np.count_nonzero(food)),'visibleFoodAlpha128Pixels':int(np.count_nonzero(foodalpha>=128/255)),'active':active});print('MASK',role,clip,d,i,flush=True)
(C/(role+'-identity-mask-manifest.json')).write_text(json.dumps({'method':'Read-only BVH native evaluated physical body primary camera-ray identities and original source/all-ray food depth, with bilinear exact image alpha at native pixel centres. No ray-visibility/material edits. Diagnostic masks omit multisample filtering and denoising; comparisons dilate union food coverage2px and report alpha/edge regions separately.','records':rows},indent=2))
