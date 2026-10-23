import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');E=P/'reviews/held-food-v2-evidence';sys.path.insert(0,str(P.parents[2]/'production/source/blender'))
import native_actions as NA
br=json.loads((P/'brief-v2-held-food.json').read_text());rig=json.loads((P/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.all_objects));sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False
coll.hide_render=False;coll.hide_viewport=False;plane=next(o for o in coll.all_objects if '__image_plane' in o.name);oldimage=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE');newimage=bpy.data.images.load(str((P/br['foodDependency']['artwork']).resolve()),check_existing=False)
def alpha(im):return np.asarray(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)[:,:,3]
oldA=alpha(oldimage);newA=alpha(newimage)
def sample(a,u,v):
 h,w=a.shape;x=u*w-.5;y=v*h-.5;x0=math.floor(x);y0=math.floor(y);fx=x-x0;fy=y-y0
 def px(ix,iy):return float(a[iy,ix]) if 0<=ix<w and 0<=iy<h else 0.
 return px(x0,y0)*(1-fx)*(1-fy)+px(x0+1,y0)*fx*(1-fy)+px(x0,y0+1)*(1-fx)*fy+px(x0+1,y0+1)*fx*fy
uvs=[tuple(l.uv) for l in plane.data.uv_layers.active.data];umin=min(u[0] for u in uvs);umax=max(u[0] for u in uvs);vmin=min(u[1] for u in uvs);vmax=max(u[1] for u in uvs);xmin=min(v.co.x for v in plane.data.vertices);xmax=max(v.co.x for v in plane.data.vertices);ymin=min(v.co.y for v in plane.data.vertices);ymax=max(v.co.y for v in plane.data.vertices);semantic=json.loads((E/'semantic-support-reference.json').read_text())['references'][1];newHeight=semantic['canonicalRecommendedHeight'];newXMin=semantic['canonicalRecommendedXMin'];newXMax=semantic['canonicalRecommendedXMax'];newYMin=semantic['canonicalRecommendedYMin'];newYMax=semantic['canonicalRecommendedYMax']
cam=sc.camera;right=cam.matrix_world.col[0].xyz.normalized();up=cam.matrix_world.col[1].xyz.normalized();forward=-cam.matrix_world.col[2].xyz.normalized()
def px(v):
 q=world_to_camera_view(sc,cam,v);return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
rootpx=px(Vector((0,0,0)));ppu=(px(right)-rootpx).length;records=[]
for clip in ['hold','load']:
 for d in ['N','E','S','W']:
  for index in [0,5,11]:
   NA.apply_clip({'root':root,'collection':coll},rig,clip,index+1,d,sc);dg=bpy.context.evaluated_depsgraph_get();points=[];faces=[]
   for o in coll.all_objects:
    if o.type!='MESH' or o==plane or o.hide_render or not o.visible_camera:continue
    ev=o.evaluated_get(dg);offset=len(points);points.extend(ev.matrix_world@v.co for v in ev.data.vertices);faces.extend(tuple(offset+i for i in p.vertices) for p in ev.data.polygons)
   bvh=BVHTree.FromPolygons(points,faces,all_triangles=False);ev=plane.evaluated_get(dg);bottom=ev.matrix_world@Vector((xmin,ymin,0));top=ev.matrix_world@Vector((xmax,ymax,0));newbottom=ev.matrix_world@Vector((newXMin,newYMin,0));newtop=ev.matrix_world@Vector((newXMax,newYMax,0));p0=px(bottom);p1=px(top);pn0=px(newbottom);pn=px(newtop);w=p1.x-p0.x;h=p0.y-p1.y;nw=pn.x-pn0.x;nh=pn0.y-pn.y;oldvisible=[];newvisible=[];oldall=0;newall=0
   for py in range(max(0,math.floor(min(p1.y,pn.y))),min(640,math.ceil(max(p0.y,pn0.y)))):
    for xx in range(max(0,math.floor(min(p0.x,pn0.x))),min(384,math.ceil(max(p1.x,pn.x)))):
     u=(xx+.5-p0.x)/w;v=(p0.y-py-.5)/h;nu=(xx+.5-pn0.x)/nw;nv=(pn0.y-py-.5)/nh
     oa=sample(oldA,umin+u*(umax-umin),vmin+v*(vmax-vmin)) if 0<=u<=1 and 0<=v<=1 else 0;na=sample(newA,nu,nv) if 0<=nu<=1 and 0<=nv<=1 else 0
     if oa<=.5 and na<=.5:continue
     if oa>.5:oldall+=1
     if na>.5:newall+=1
     screenpoint=right*((xx+.5-rootpx.x)/ppu)+up*((rootpx.y-py-.5)/ppu);origin=screenpoint-forward*10;foodDistance=(bottom-origin).dot(forward);hit=bvh.ray_cast(origin,forward,100);visible=(hit[0] is None or hit[3]>=foodDistance-1e-5)
     if visible and oa>.5:oldvisible.append([xx,py])
     if visible and na>.5:newvisible.append([xx,py])
   def info(v):return {'opaqueVisiblePixels':len(v),'bbox':[min(a[0] for a in v),min(a[1] for a in v),max(a[0] for a in v)+1,max(a[1] for a in v)+1] if v else None}
   records.append({'clip':clip,'direction':d,'index':index,'old':{**info(oldvisible),'totalOpaqueQuadPixels':oldall},'canonicalAtSemanticSupportProjection':{**info(newvisible),'totalOpaqueQuadPixels':newall},'method':'Read-only geometric camera-ray visibility against evaluated opaque chef/knife meshes, source food plane depth unchanged; image alpha bilinear sampled at native pixel centers. Canonical fullUV quad width and position mathematically derived from source opaque rim/support alpha128 reference only, never added/saved/rendered as candidate.'})
(E/'occlusion-semantic-support-analysis.json').write_text(json.dumps({'scope':'Analytic placement diagnostic only, no candidate verdict or native canonical render. Ignores multisample coverage, denoising, lighting/secondary radiance and transparent body materials; body is opaque in inspected source.','semanticReference':semantic,'records':records},indent=2)+'\n')
print(json.dumps(records,indent=2))
