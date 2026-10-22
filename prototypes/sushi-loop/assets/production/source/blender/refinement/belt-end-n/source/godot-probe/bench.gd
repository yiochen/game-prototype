extends SceneTree
const Composer=preload("res://runtime/native_pixel_compositor.gd")
class Drawing:
	extends Node2D
	var commands:Array=[]
	func _draw()->void:
		for c in commands:draw_texture_rect_region(c.texture,c.destination,c.region)
class Background:
	extends Node2D
	var dimensions:Vector2
	var color:Color
	func _draw()->void:draw_rect(Rect2(Vector2.ZERO,dimensions),color)
var config:Dictionary
var pipelines:Dictionary={}
var drawings:Dictionary={}
var outputs:Array=[]
var textures:Dictionary={}
func _initialize()->void:call_deferred("run")
func texture(path:String)->Texture2D:
	if not textures.has(path):textures[path]=ImageTexture.create_from_image(Image.load_from_file(path))
	return textures[path]
func set_case(direction:String,index:int,shift:Vector2)->void:
	for mode in pipelines:
		var commands:Array=[];var pipeline=pipelines[mode];pipeline.set_grid_origin(shift)
		if mode=="independent":
			for c in config.modules[direction]:
				var tex=texture(config.nativeBase.path_join("atlases/%s-%s.png"%[c.kind,c.direction]))
				commands.append({"texture":pipeline.native_sprite_texture("belt-"+str(c.kind),tex),"destination":Rect2(Vector2(c.offset[0],c.offset[1])+shift,Vector2(384,704)),"region":Rect2((index%6)*384,int(index/6)*704,384,704)})
		else:
			var tex=texture(config.nativeBase.path_join("%s/running-%s-%02d.png"%[mode,direction,index]));commands.append({"texture":tex,"destination":Rect2(shift,Vector2(896,1216)),"region":Rect2(0,0,896,1216)})
		drawings[mode].commands=commands;drawings[mode].queue_redraw()
func settle()->void:
	await process_frame
	RenderingServer.force_draw()
	await process_frame
	RenderingServer.force_draw()
func run()->void:
	OS.low_processor_usage_mode=false
	config=JSON.parse_string(FileAccess.get_file_as_string("res://config.json"))
	config.nativeBase=ProjectSettings.globalize_path("res://").path_join("../../candidates/round-01").simplify_path();config.output=config.nativeBase.path_join("godot-consumer");DirAccess.make_dir_recursive_absolute(config.output)
	var cases:Array=[]
	for direction in ["N","E","S","W"]:cases.append({"direction":direction,"pitch":55,"index":0,"background":"transparent","shift":[.25,.75]})
	cases.append({"direction":"S","pitch":128,"index":23,"background":"light","shift":[0,0]});cases.append({"direction":"S","pitch":32,"index":7,"background":"dark","shift":[.75,.25]});cases.append({"direction":"S","pitch":47.3,"index":23,"background":"transparent","shift":[.25,.75]})
	for mode in ["independent","connected","unbroken"]:
		var drawing=Drawing.new();drawing.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST;var pipeline=Composer.new();root.add_child(pipeline);pipeline.initialize(drawing,Vector2(896,1216));drawings[mode]=drawing;pipelines[mode]=pipeline
		for i in range(cases.size()):
			var c=cases[i];var factor=float(c.pitch)/256.;var dimensions=Vector2i(ceili(896*factor),ceili(1216*factor));var view=SubViewport.new();view.size=dimensions;view.transparent_bg=true;view.disable_3d=true;view.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(view);var bg=Background.new();bg.dimensions=dimensions;bg.color={"transparent":Color.TRANSPARENT,"light":Color("f5f2e9"),"dark":Color("182231")}[c.background];view.add_child(bg);pipeline.make_surface(view,Rect2(Vector2.ZERO,dimensions),factor);outputs.append({"case":i,"view":view,"mode":mode})
	var records:Array=[]
	for i in range(cases.size()):
		var c=cases[i];set_case(c.direction,c.index,Vector2(c.shift[0],c.shift[1]));await settle()
		for o in outputs:
			if o.case!=i:continue
			var filename="case-%02d-%s.png"%[i,o.mode];o.view.get_texture().get_image().save_png(config.output.path_join(filename));records.append({"case":str(i),"direction":c.direction,"pitch":c.pitch,"index":c.index,"mode":o.mode,"background":c.background,"shift":c.shift,"path":filename})
	var f=FileAccess.open(config.output.path_join("render-record.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"godot":Engine.get_version_info(),"captures":records,"method":"Actual unchanged production native compositor,registered atlas-region independent/nativeconnected/weldedreference comparison. Proportionate distinct terminal-class fixture; broadtiming/filter matrix explicitly reused."},"  "));f.close();quit()
