extends SceneTree
const Editor = preload("res://scripts/editor_presentation.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
class Drawing:
	extends Control
	var texture: Texture2D
	var color := Color.TRANSPARENT
	var frame_size := Vector2.ZERO
	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, frame_size), color)
		draw_texture_rect_region(texture, UISkin.fit_rect(texture.get_size(), Rect2(Vector2.ZERO, frame_size)), Rect2(Vector2.ZERO, texture.get_size()))
var outputs: Array[Dictionary] = []
var contexts: Array[Dictionary] = []
var outdir: String
const BG := {"cream": Color("fff3db"), "light": Color("e6e9e4"), "gray": Color("787d80"), "dark": Color("181e24")}
func _initialize() -> void: call_deferred("run")
func viewport(dimensions: Vector2i) -> SubViewport:
	var v := SubViewport.new()
	v.size = dimensions
	v.transparent_bg = true
	v.disable_3d = true
	v.gui_disable_input = true
	v.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	v.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(v)
	return v
func draw_state() -> Dictionary:
	return {"mode":"edit", "editor":{"layer":"layout", "page":0, "tray_open":true, "selected_id":""}, "inventory":[{"id":"belt-tile","name":"Conveyor","art_id":"belt-straight-e","kind":"belt","count":6}, {"id":"stool-plain","name":"Wood stool","art_id":"stool-wood","kind":"seat","count":4}, {"id":"plant-angular","name":"Plant","art_id":"plant-angular","kind":"decor","count":2}, {"id":"barrel-wood","name":"Barrel","art_id":"barrel-wood","kind":"decor","count":1}, {"id":"crate-wood","name":"Crate","art_id":"crate-wood","kind":"decor","count":3}, {"id":"floor-cream","name":"Cream floor","art_id":"floor-cream","kind":"floor","count":1}]}
func run() -> void:
	outdir = OS.get_environment("GOODS_OUTPUT")
	assert(not outdir.is_empty())
	DirAccess.make_dir_recursive_absolute(outdir)
	for mode in ["original", "candidate"]:
		for pixels in [384, 96, 66]:
			for bg in BG:
				var v := viewport(Vector2i(pixels,pixels))
				var drawing := Drawing.new()
				drawing.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
				drawing.texture = load("res://%s.png" % mode)
				drawing.frame_size = Vector2(pixels,pixels)
				drawing.size = drawing.frame_size
				drawing.color = BG[bg]
				v.add_child(drawing)
				outputs.append({"mode":mode,"pixels":pixels,"background":bg,"viewport":v})
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
	var records: Array[Dictionary] = []
	for output in outputs:
		var path := outdir.path_join("background-%s-%d-%s.png" % [output.mode,output.pixels,output.background])
		assert(output.viewport.get_texture().get_image().save_png(path)==OK)
		records.append({"mode":output.mode,"pixels":output.pixels,"background":output.background,"path":path,"filter":"current LINEAR; full384canvas UISkin.fit_rect; no alpha crop"})
	for mode in ["candidate", "original"]:
		Editor.ItemPreview.goods_loaded = true
		Editor.ItemPreview.goods = JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/editor-goods/manifest.json")).sprites
		Editor.ItemPreview.goods_texture = load("res://assets/ui/editor-goods/atlas.png" if mode=="candidate" else "res://baseline-atlas.png")
		var active: Array[Dictionary] = []
		for dimensions in [Vector2i(540,960),Vector2i(786,1398),Vector2i(1280,720)]:
			var v := viewport(dimensions)
			var background := ColorRect.new()
			background.color=Color("28413e")
			background.size=Vector2(dimensions)
			v.add_child(background)
			var editor := Editor.new()
			editor.reduced_motion=true
			editor.size=Vector2(dimensions)
			v.add_child(editor)
			var width := minf(dimensions.x, dimensions.y*9.0/16.0)
			var unit := width/720.0
			var sky_height := 80.0*unit
			var area := Rect2((dimensions.x-width)*0.5,sky_height,width,dimensions.y-sky_height)
			editor.set_state(draw_state(),area)
			active.append({"viewport":v,"editor":editor,"size":dimensions,"area":area})
		await process_frame
		await RenderingServer.frame_post_draw
		await process_frame
		await RenderingServer.frame_post_draw
		for entry in active:
			var editor: Control = entry.editor
			var dimensions: Vector2i=entry.size
			var path:=outdir.path_join("context-%s-%dx%d.png" % [mode,dimensions.x,dimensions.y])
			assert(entry.viewport.get_texture().get_image().save_png(path)==OK)
			var card:Button=editor.cards[0]
			var preview:Control=card.get_meta("preview")
			var fit:=UISkin.fit_rect(Vector2(384,384),Rect2(Vector2.ZERO,preview.size))
			contexts.append({"mode":mode,"path":path,"viewportSize":[dimensions.x,dimensions.y],"hudArea":[entry.area.position.x,entry.area.position.y,entry.area.size.x,entry.area.size.y],"unit":editor.unit,"cardRect":[card.global_position.x,card.global_position.y,card.size.x,card.size.y],"previewRect":[preview.global_position.x,preview.global_position.y,preview.size.x,preview.size.y],"fullCanvasDestination":[preview.global_position.x+fit.position.x,preview.global_position.y+fit.position.y,fit.size.x,fit.size.y],"label":card.get_meta("name_label").text,"stock":card.get_meta("stock").text,"badgeVisible":card.get_meta("stock_badge").visible,"inventoryCount":editor.state.inventory.size(),"goodsManifestCount":Editor.ItemPreview.goods.size(),"actualCurrentCode":true})
		for entry in active: entry.viewport.queue_free()
		await process_frame
	var record:={"godot":Engine.get_version_info(),"renderer":ProjectSettings.get_setting("rendering/renderer/rendering_method"),"backgrounds":records,"contexts":contexts,"qualification":"Actual current unmodified EditorPresentation in disposableproject; plain solid roomplaceholder only, no simulatedcard. Sixitem fixture. Static goods texture is bound to either original exactatlas or copiedatlas with only E384rect substituted. All card layout/labels/stock/badge/fit/filter code unchanged. CameraHudarea formula follows current RestaurantView9:16/80unit rules."}
	var file:=FileAccess.open(outdir.path_join("render-record.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(record,"  "))
	quit()
