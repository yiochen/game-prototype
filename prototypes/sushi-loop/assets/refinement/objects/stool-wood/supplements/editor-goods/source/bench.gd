extends SceneTree
## Isolated fixture; uses unchanged current production presentation and assets.
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
			if entry.id=="stool-plain": entry.count=0
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
func apply_fixture_command(command:Dictionary,editor:Control,area:Rect2,history:Array) -> void:
	history.append(command.duplicate(true))
	if command.type=="editor_page":
		var next_state:Dictionary=editor.state.duplicate(true)
		next_state.editor.page=command.page
		editor.set_state(next_state,area)
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
		for fixture in [{"name":"layout-page0","layer":"layout"},{"name":"layout-page1","layer":"layout"},{"name":"layout-back","layer":"layout"},{"name":"floor","layer":"floor"},{"name":"stool-selected","layer":"layout"},{"name":"stool-empty","layer":"layout"}]:
			for dimensions in [Vector2i(540,960),Vector2i(900,1200),Vector2i(1280,720)]:
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
				editor.active_item="stool-plain" if fixture.name=="stool-selected" else ""
				editor.set_state(draw_state(fixture.layer,0,fixture.name=="stool-empty"),area)
				var history:Array=[]
				editor.command_requested.connect(apply_fixture_command.bind(editor,area,history))
				if fixture.name in ["layout-page1","layout-back"]:
					assert(not editor.next.disabled)
					editor.next.pressed.emit()
					assert(editor.state.editor.page==1 and editor.cards.size()==1 and editor.next.disabled and not editor.previous.disabled)
				if fixture.name=="layout-back":
					editor.previous.pressed.emit()
					assert(editor.state.editor.page==0 and editor.cards.size()==4 and editor.previous.disabled and not editor.next.disabled)
				active.append({"viewport":v,"editor":editor,"size":dimensions,"area":area,"state":fixture.name,"history":history})
		await frames()
		for entry in active:
			var editor:Control=entry.editor
			var dimensions:Vector2i=entry.size
			var path:=outdir.path_join("context-%s-%s-%dx%d.png"%[mode,entry.state,dimensions.x,dimensions.y])
			assert(entry.viewport.get_texture().get_image().save_png(path)==OK)
			var cards:Array[Dictionary]=[]
			var disabled_probe:Dictionary={"exercised":false}
			for card:Button in editor.cards:
				var preview:Control=card.get_meta("preview")
				var fit:=UISkin.fit_rect(Vector2(384,384),Rect2(Vector2.ZERO,preview.size))
				cards.append({"id":card.get_meta("entry").id,"artID":card.get_meta("entry").art_id,"cardRect":rect(card.get_global_rect()),"previewRect":rect(preview.get_global_rect()),"fullCanvasDestination":[preview.global_position.x+fit.position.x,preview.global_position.y+fit.position.y,fit.size.x,fit.size.y],"label":card.get_meta("name_label").text,"labelVisible":card.get_meta("name_label").visible,"stock":card.get_meta("stock").text,"stockVisible":card.get_meta("stock").visible,"badgeVisible":card.get_meta("stock_badge").visible,"disabled":card.disabled,"selected":card.button_pressed})
				if entry.state=="stool-empty" and card.get_meta("entry").id=="stool-plain":
					var probe:Dictionary={"pointerSignals":0,"armedSignals":0}
					editor.item_pointer.connect(func(_item:Dictionary,_event:InputEvent):probe.pointerSignals+=1)
					editor.item_armed.connect(func(_item:Dictionary):probe.armedSignals+=1)
					var click:=InputEventMouseButton.new()
					click.button_index=MOUSE_BUTTON_LEFT
					click.pressed=true
					card.gui_input.emit(click)
					assert(card.disabled and probe.pointerSignals==0 and probe.armedSignals==0)
					disabled_probe={"exercised":true,"nativeDisabledProperty":card.disabled,"productionGuiInputGuardExercised":true,"pointerSignals":probe.pointerSignals,"armedSignals":probe.armedSignals,"note":"Direct gui_input signal exercises unchanged production pointer guard; native Button.disabled remains true. No native pressed signal forced."}
			contexts.append({"mode":mode,"state":entry.state,"path":path.get_file(),"viewportSize":[dimensions.x,dimensions.y],"hudArea":rect(entry.area),"unit":editor.unit,"cards":cards,"inventoryCount":editor.state.inventory.size(),"goodsManifestCount":Editor.ItemPreview.goods.size(),"actualCurrentCode":true,"stateSnapshot":editor.state.duplicate(true),"activeItem":editor.active_item,"controls":control_properties(editor),"navigationCommands":entry.history,"disabledInputProbe":disabled_probe,"fixture":{"name":entry.state,"stoolZeroDisabled":entry.state=="stool-empty","originalStoolCount":4,"productionInventoryModified":false,"userSaveReadOrWritten":false}})
		for entry in active:entry.viewport.queue_free()
		await process_frame
	var record:={"godot":Engine.get_version_info(),"renderer":ProjectSettings.get_setting("rendering/renderer/rendering_method"),"backgrounds":backgrounds,"contexts":contexts,"qualification":"Actual unchanged current EditorPresentation/UISkin in isolated project. Solid room placeholder only; no world/room rendering claim. Exact copied content/editor.json six-goods fixture; layout0, connected next/page1 and previous/back, floor, selectedstool4 and emptystool0 states. Only declared empty fixture count changes from baseline in memory. Names/counts/badges/layout/filter/fit remain current. Candidate copied atlas replaces stool384rect only, all five other cells and padding including accepted floor exact. HUD area follows current9:16/80unit rule. No user saves accessed. Navigation exercises actual native buttons connected pressed signals and isolated caller state application."}
	var file:=FileAccess.open(outdir.path_join("render-record.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(record,"  "))
	quit()
