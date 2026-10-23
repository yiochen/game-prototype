import bpy,json,pathlib,importlib.util,sys,math
B=pathlib.Path(__file__).resolve().parents[2];bpy.ops.wm.open_mainfile(filepath=str((B/'source/round-01.blend').resolve()));recipe=json.loads((B/'source/recipe-round01.json').read_text());s=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0];coll=bpy.data.collections[recipe['collection']];plane=next(o for o in coll.all_objects if '__image_plane' in o.name)
r=[]
for f in plane.animation_data.drivers:
 r.append({'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'extrapolation':f.extrapolation,'modifiers':[{'type':m.type,'poly_order':getattr(m,'poly_order',None),'coefficients':list(m.coefficients) if hasattr(m,'coefficients') else None} for m in f.modifiers],'keyframes':[{'co':list(k.co),'interpolation':k.interpolation,'left':list(k.handle_left),'right':list(k.handle_right)} for k in f.keyframe_points],'evaluateNearZero':[[x,f.evaluate(x)] for x in [-.001,-.0002,-.0001,-.00007,-.00001,0,.00001,.00007,.0001,.0002,.001]]})
(B/'reviews/held-food-v3/source-driver-mapping.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
