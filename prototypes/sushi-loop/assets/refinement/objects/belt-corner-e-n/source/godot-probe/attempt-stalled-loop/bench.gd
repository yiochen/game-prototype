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
var captures:Array=[]
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
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
func run()->void:
	config=JSON.parse_string(FileAccess.get_file_as_string("res://config.json"))
	config.nativeBase=ProjectSettings.globalize_path("res://").path_join("../../candidates/round-01").simplify_path()
	config.output=config.nativeBase.path_join("godot-consumer")
	DirAccess.make_dir_recursive_absolute(config.output)
	for mode in ["independent","connected","unbroken"]:
		var drawing=Drawing.new();drawing.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
		var pipeline=Composer.new();root.add_child(pipeline);pipeline.initialize(drawing,Vector2(896,1216));drawings[mode]=drawing;pipelines[mode]=pipeline
		for pitch in [128,55,32,47.3]:
			var factor=float(pitch)/256.;var dimensions=Vector2i(ceili(896*factor),ceili(1216*factor))
			for bg in ["transparent","light","gray","dark"]:
				var view=SubViewport.new();view.size=dimensions;view.transparent_bg=true;view.disable_3d=true;view.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(view)
				var background=Background.new();background.dimensions=dimensions;background.color={"transparent":Color.TRANSPARENT,"light":Color("f5f2e9"),"gray":Color("808080"),"dark":Color("182231")}[bg];view.add_child(background)
				pipeline.make_surface(view,Rect2(Vector2.ZERO,dimensions),factor);outputs.append({"view":view,"mode":mode,"pitch":pitch,"background":bg})
	for direction in ["N","E","S","W"]:
		for index in [0,7,23]:
			for origin in ["integer","subpixel"]:
				var shift=Vector2.ZERO if origin=="integer" else Vector2(.25,.75)
				set_case(direction,index,shift);await settle()
				for c in outputs:
					var filename="%s-%s-%02d-%s-%s-%s.png"%[c.mode,direction,index,c.pitch,c.background,origin]
					c.view.get_texture().get_image().save_png(config.output.path_join(filename));captures.append({"mode":c.mode,"direction":direction,"index":index,"pitch":c.pitch,"background":c.background,"origin":origin,"nativeShift":[shift.x,shift.y],"path":filename})
			print("CORNER_GPU ",direction," ",index)
	var playback:Array=[]
	for direction in ["N","E","S","W"]:
		var start=Time.get_ticks_msec()
		for step in range(48):
			var target=start+roundi(step*1000./12.);var delay=(target-Time.get_ticks_msec())/1000.
			if delay>0:await create_timer(delay).timeout
			set_case(direction,step%24,Vector2(.25,.75));await settle()
			for c in outputs:
				if c.pitch!=55 or c.background!="transparent":continue
				var filename="loop-%s-%s-%02d.png"%[c.mode,direction,step]
				c.view.get_texture().get_image().save_png(config.output.path_join(filename));playback.append({"mode":c.mode,"direction":direction,"index":step%24,"step":step,"elapsedMS":Time.get_ticks_msec()-start,"pitch":55,"background":"transparent","origin":"subpixel","path":filename})
	var f=FileAccess.open(config.output.path_join("render-record.json"),FileAccess.WRITE);f.store_string(JSON.stringify({"godot":Engine.get_version_info(),"renderer":ProjectSettings.get_setting("rendering/renderer/rendering_method"),"captures":captures,"playback":playback,"method":"Actual unchanged production native compositor/reducer/presenter. Registered atlas regions, integer/subpixel origins, exact128/55/32/fractional47.3 pitches; four backgrounds. Two loops scheduled at12fps with actual elapsed times retained."},"  "));f.close();quit()
