extends SceneTree
const Editor = preload("res://scripts/editor_presentation.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const BG := {"cream":Color("fff3db"),"light":Color("e6e9e4"),"gray":Color("787d80"),"dark":Color("181e24")}
class Drawing:
	extends Control
	var texture: Texture2D
	var color := Color.TRANSPARENT
	var frame_size := Vector2.ZERO
	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO,frame_size),color)
		draw_texture_rect_region(texture,UISkin.fit_rect(texture.get_size(),Rect2(Vector2.ZERO,frame_size)),Rect2(Vector2.ZERO,texture.get_size()))
var outputs:Array[Dictionary]=[]
var contexts:Array[Dictionary]=[]
var outdir:String
func _initialize() -> void: call_deferred("run")
func viewport(dimensions:Vector2i) -> SubViewport:
	var v:=SubViewport.new()
	v.size=dimensions
	v.transparent_bg=true
	v.disable_3d=true
	v.gui_disable_input=true
	v.render_target_clear_mode=SubViewport.CLEAR_MODE_ALWAYS
	v.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	root.add_child(v)
	return v
func draw_state(layer:String,page:int,empty_stock:bool=false) -> Dictionary:
	var inventory:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://content/editor.json"))
	var entries:Array=inventory.inventory.duplicate(true)
	if empty_stock:
		for entry in entries:
			if entry.id=="barrel-wood": entry.count=0
	return {"mode":"edit","editor":{"layer":layer,"page":page,"tray_open":true,"selected_id":""},"inventory":entries}
func frames() -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
func rect(r:Rect2) -> Array:return [r.position.x,r.position.y,r.size.x,r.size.y]
func button_properties(b:Button) -> Dictionary:
	return {"text":b.text,"disabled":b.disabled,"selected":b.button_pressed,"visible":b.visible,"rect":rect(b.get_global_rect()),"toggleMode":b.toggle_mode,"mouseFilter":b.mouse_filter,"textureFilter":b.texture_filter,"tooltip":b.tooltip_text,"accessibilityName":b.accessibility_name}
func control_properties(editor:Control) -> Dictionary:
	var tabs:Dictionary={}
	for key in editor.layers: tabs[key]=button_properties(editor.layers[key])
	return {"previous":button_properties(editor.previous),"next":button_properties(editor.next),"shop":button_properties(editor.shop),"live":button_properties(editor.live),"rotate":button_properties(editor.rotate),"return":button_properties(editor.remove),"tabs":tabs,"pageAnnouncement":editor.page_announcement.text,"trayRect":rect(editor.tray.get_global_rect()),"railRect":rect(editor.rail.get_global_rect()),"categoryRect":rect(editor.category_rail.get_global_rect()),"selectedVisible":editor.selected_visible,"filter":editor.texture_filter}
func run() -> void:
	outdir=OS.get_environment("GOODS_OUTPUT")
	assert(not outdir.is_empty())
	DirAccess.make_dir_recursive_absolute(outdir)
	for mode in ["original","candidate"]:
		for pixels in [384,96,66]:
			for bg in BG:
				var v:=viewport(Vector2i(pixels,pixels))
				var drawing:=Drawing.new()
				drawing.texture_filter=CanvasItem.TEXTURE_FILTER_LINEAR
				drawing.texture=load("res://%s.png"%mode)
				drawing.frame_size=Vector2(pixels,pixels)
				drawing.size=drawing.frame_size
				drawing.color=BG[bg]
				v.add_child(drawing)
				outputs.append({"mode":mode,"pixels":pixels,"background":bg,"viewport":v})
	await frames()
	var backgrounds:Array[Dictionary]=[]
	for output in outputs:
		var path:=outdir.path_join("background-%s-%d-%s.png"%[output.mode,output.pixels,output.background])
		assert(output.viewport.get_texture().get_image().save_png(path)==OK)
		backgrounds.append({"mode":output.mode,"pixels":output.pixels,"background":output.background,"path":path.get_file(),"filter":"Current LINEAR full384square UISkin.fit_rect; no alpha crop"})
	for mode in ["candidate","original"]:
		Editor.ItemPreview.goods_loaded=true
		Editor.ItemPreview.goods=JSON.parse_string(FileAccess.get_file_as_string("res://assets/ui/editor-goods/manifest.json")).sprites
		Editor.ItemPreview.goods_texture=load("res://assets/ui/editor-goods/atlas.png" if mode=="candidate" else "res://baseline-atlas.png")
		var active:Array[Dictionary]=[]
		for state in [{"name":"layout-page0","layer":"layout","page":0},{"name":"layout-page1","layer":"layout","page":1},{"name":"floor","layer":"floor","page":0},{"name":"barrel-selected","layer":"layout","page":1},{"name":"barrel-empty","layer":"layout","page":1}]:
			for dimensions in [Vector2i(540,960),Vector2i(786,1398),Vector2i(1280,720)]:
				var v:=viewport(dimensions)
				var background:=ColorRect.new()
				background.color=Color("28413e")
				background.size=Vector2(dimensions)
				v.add_child(background)
				var editor:=Editor.new()
				editor.reduced_motion=true
				editor.size=Vector2(dimensions)
				v.add_child(editor)
				var width:=minf(dimensions.x,dimensions.y*9.0/16.0)
				var unit:=width/720.0
				var sky_height:=80.0*unit
				var area:=Rect2((dimensions.x-width)*0.5,sky_height,width,dimensions.y-sky_height)
				editor.active_item="barrel-wood" if state.name=="barrel-selected" else ""
				editor.set_state(draw_state(state.layer,state.page,state.name=="barrel-empty"),area)
				active.append({"viewport":v,"editor":editor,"size":dimensions,"area":area,"state":state.name})
		await frames()
		for entry in active:
			var editor:Control=entry.editor
			var dimensions:Vector2i=entry.size
			var path:=outdir.path_join("context-%s-%s-%dx%d.png"%[mode,entry.state,dimensions.x,dimensions.y])
			assert(entry.viewport.get_texture().get_image().save_png(path)==OK)
			var cards:Array[Dictionary]=[]
			for card:Button in editor.cards:
				var preview:Control=card.get_meta("preview")
				var fit:=UISkin.fit_rect(Vector2(384,384),Rect2(Vector2.ZERO,preview.size))
				cards.append({"id":card.get_meta("entry").id,"artID":card.get_meta("entry").art_id,"cardRect":rect(card.get_global_rect()),"previewRect":rect(preview.get_global_rect()),"fullCanvasDestination":[preview.global_position.x+fit.position.x,preview.global_position.y+fit.position.y,fit.size.x,fit.size.y],"label":card.get_meta("name_label").text,"labelVisible":card.get_meta("name_label").visible,"stock":card.get_meta("stock").text,"stockVisible":card.get_meta("stock").visible,"badgeVisible":card.get_meta("stock_badge").visible,"disabled":card.disabled,"selected":card.button_pressed})
			contexts.append({"mode":mode,"state":entry.state,"path":path.get_file(),"viewportSize":[dimensions.x,dimensions.y],"hudArea":rect(entry.area),"unit":editor.unit,"cards":cards,"inventoryCount":editor.state.inventory.size(),"goodsManifestCount":Editor.ItemPreview.goods.size(),"actualCurrentCode":true,"stateSnapshot":editor.state.duplicate(true),"activeItem":editor.active_item,"controls":control_properties(editor),"fixture":{"name":entry.state,"barrelZeroDisabled":entry.state=="barrel-empty","originalBarrelCount":1,"productionInventoryModified":false}})
		for entry in active:entry.viewport.queue_free()
		await process_frame
	var record:={"godot":Engine.get_version_info(),"renderer":ProjectSettings.get_setting("rendering/renderer/rendering_method"),"backgrounds":backgrounds,"contexts":contexts,"qualification":"Actual unchanged current EditorPresentation/UISkin in isolated project. Solid room placeholder only; no world/room rendering claim. Exact copied content/editor.json six-goods fixture; layout0, layout1, floor, selectedbarrel1 and emptybarrel0 states; only empty fixture count changes from baseline. Existing names/counts/badges/layout/filter/fit remain current. Candidate copied atlas replaces barrel384rect only, all other cells including accepted floor exact. HUD area follows current9:16/80unit rule."}
	var file:=FileAccess.open(outdir.path_join("render-record.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(record,"  "))
	quit()
