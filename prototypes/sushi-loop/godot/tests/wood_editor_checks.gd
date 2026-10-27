extends RefCounted
## Shared interaction regression suite for the real gameplay/editor scene.
const Session = preload("res://scripts/session.gd")
var tree: SceneTree
var checks := 0
var failures: Array[String] = []
var output := ""

func expect(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func frames() -> void:
	for i in range(3): await tree.process_frame

func touch(app, at: Vector2, down: bool, cancel := false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 21
	event.position = app.get_viewport_transform()*at
	event.pressed = down
	event.canceled = cancel
	Input.parse_input_event(event)
	await frames()

func drag(app, start: Vector2, end: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 21
	event.position = app.get_viewport_transform()*end
	event.relative = app.get_viewport_transform().basis_xform(end-start)
	Input.parse_input_event(event)
	await frames()

func tap(app, button: Control) -> void:
	var center := button.get_global_rect().get_center()
	await touch(app,center,true)
	await touch(app,center,false)

func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	tree.root.get_texture().get_image().save_png(output.path_join(name+".png"))

func gameplay(scene: Dictionary) -> String:
	var copy := scene.duplicate(true)
	copy.erase("editor")
	return JSON.stringify(copy)

func run(app, scene_tree: SceneTree, destination := "") -> void:
	tree = scene_tree
	output = destination
	app.session = Session.new_session(41)
	app._refresh()
	app._layout()
	await frames()
	await tap(app,app.edit)
	var ui = app.editor_ui
	expect(app.session.snapshot().mode == "edit" and ui.visible,"Edit opens the native continuous wood dock")
	expect(ui.cards.size()==5 and ui.rail.clip_contents and not ui.previous.visible and not ui.next.visible,"All five goods share a clipped horizontal strip without paging carets")
	expect(ui.wood.manifest.assets["shop-normal"].face_rect[3]==60 and ui.wood.manifest.assets["tab-normal"].face_rect[3]==60,"Shop and inactive tabs retain matching 60-unit faces")
	var targets := true
	for button: Button in [ui.layers.people,ui.layers.layout,ui.layers.floor,ui.shop]:
		var physical: Rect2 = app.get_viewport_transform()*button.get_global_rect()
		if physical.size.x<43.99 or physical.size.y<43.99 or not app.world.portrait.encloses(button.get_global_rect()):
			print("Wood target bounds: ",button.text," physical=",physical," logical=",button.get_global_rect()," portrait=",app.world.portrait)
		targets = targets and physical.size.x>=43.99 and physical.size.y>=43.99 and app.world.portrait.encloses(button.get_global_rect())
	expect(targets,"Compact category artwork keeps contained 44px physical touch targets")
	var clip: Rect2 = ui.rail.get_global_rect()
	expect(clip.encloses(ui.cards[3].get_global_rect()) and clip.intersects(ui.cards[4].get_global_rect()) and not clip.encloses(ui.cards[4].get_global_rect()),"Four complete goods and a clipped fifth provide the scrolling cue")
	expect(ui.cards[0].get_meta("stock").text==str(int(app.session.snapshot().inventory[0].count)) and ui.cards[1].get_meta("stock").text==str(int(app.session.snapshot().inventory[1].count)),"Quantities remain native live text in circular badges")
	expect(ui.cards[0].get_meta("preview").trim_goods,"Goods fit the same visible alpha bounds as the approved HTML, excluding authoring padding")
	var paused := gameplay(app.session.snapshot())
	app.advance_time(20)
	expect(gameplay(app.session.snapshot())==paused,"Editor pauses the entire simulation")
	await capture("01-layout")
	var start: Vector2 = ui.cards[1].get_global_rect().get_center()
	await touch(app,start,true)
	expect(app.gesture_kind=="inventory_pending" and app.armed_item.is_empty(),"Initial tray touch does not arm an item")
	await drag(app,start,start-Vector2(130,2)*ui.unit)
	expect(app.gesture_kind=="inventory_scroll" and app.armed_item.is_empty() and app.world.editor_preview.is_empty(),"Horizontal motion owns scrolling without arming or preview")
	await drag(app,start-Vector2(130,2)*ui.unit,start-Vector2(135,160)*ui.unit)
	expect(app.gesture_kind=="inventory_scroll" and app.world.editor_preview.is_empty(),"A sideways gesture cannot change into pickup when it later moves upward")
	await touch(app,start-Vector2(135,160)*ui.unit,false)
	expect(gameplay(app.session.snapshot())==paused and ui.scroll_offsets.layout>0,"Browsing leaves objects, inventory, camera, money and clocks untouched")
	var saved: Dictionary = app.session.save_data()
	var reopened = Session.new()
	expect(reopened.restore(saved) and reopened.snapshot().editor.scrolls.layout==ui.scroll_offsets.layout,"Per-category scroll offsets survive the public save/restore boundary")
	var malformed := saved.duplicate(true)
	malformed.state.editor.scrolls.layout = -1
	expect(not Session.new().restore(malformed),"A malformed negative saved scroll offset is rejected")
	expect(not app.session.command({"type":"editor_scroll","offset":NAN}).ok,"Nonfinite scroll commands are rejected without altering state")
	var scroll: float = ui.scroll_offsets.layout
	await tap(app,ui.shop)
	expect(ui.rejection.visible and ui.scroll_offsets.layout==scroll and gameplay(app.session.snapshot())==paused,"Separate Shop keeps its unavailable behavior without changing selection or scroll")
	await capture("02-scrolled")
	ui.rejection.hide()
	var floor_button: Button = ui.layers.floor
	var target_bounds := floor_button.get_global_rect()
	await touch(app,target_bounds.get_center(),true)
	expect(floor_button.get_meta("visual_pressed",false) and floor_button.get_global_rect()==target_bounds,"Pointer down changes only tab artwork, keeping its native target stable")
	app.propagate_notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	await touch(app,target_bounds.get_center(),false)
	expect(app.session.snapshot().editor.layer=="layout" and not floor_button.get_meta("visual_pressed",false),"Focus loss cancels a held tab and ignores its orphan release")
	ui.cards[0].grab_focus()
	await frames()
	expect(ui.scroll_offsets.layout==0,"Keyboard focus reveals an offscreen first item")
	var wheel := InputEventMouseButton.new()
	wheel.position = app.get_viewport_transform()*ui.rail.get_global_rect().get_center()
	wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
	wheel.pressed = true
	Input.parse_input_event(wheel)
	await frames()
	expect(ui.scroll_offsets.layout>0,"Mouse wheel browses the native inventory viewport")
	ui.cards[-1].grab_focus()
	await frames()
	expect(ui.rail.get_global_rect().encloses(ui.cards[-1].get_global_rect()),"Keyboard focus reveals the entire final item inside the clipping panel")
	ui.scroll_by(-1000*ui.unit)
	ui.commit_scroll()
	start = ui.cards[0].get_global_rect().get_center()
	var destination_cell := Vector2i(-1,-1)
	for y in range(4,9):
		for x in range(1,7):
			var probe = Session.new()
			probe.restore(app.session.save_data())
			if probe.command({"type":"editor_place","inventory_id":"belt-tile","x":x,"y":y}).get("ok",false):
				destination_cell = Vector2i(x,y)
				break
		if destination_cell.x>=0: break
	expect(destination_cell.x>=0,"The test locates a valid free floor cell through placement rules")
	await touch(app,start,true)
	await drag(app,start,start-Vector2(0,50)*ui.unit)
	expect(app.gesture_kind=="inventory" and not app.world.editor_preview.is_empty(),"Clearly upward motion starts the native validated placement preview")
	var target: Vector2 = app.world.cell_base(destination_cell.x,destination_cell.y)
	await drag(app,start-Vector2(0,50)*ui.unit,target)
	var count: int = app.session.snapshot().objects.size()
	await touch(app,target,false)
	expect(app.session.snapshot().objects.size()==count+1 and ui.cards[0].get_meta("stock").text=="5","Upward pickup places exactly one owned object and refreshes its live badge")
	var identity := str(app.session.snapshot().editor.selected_id)
	expect(not identity.is_empty(),"Successful placement selects the placed object")
	expect(app._editor_command({"type":"editor_rotate","id":identity}).get("ok",false),"Native contextual rotation still works")
	expect(app._editor_command({"type":"editor_remove","id":identity}).get("ok",false) and ui.cards[0].get_meta("stock").text=="6","Return stores the object and restores its stock")
	var before_invalid := gameplay(app.session.snapshot())
	start = ui.cards[0].get_global_rect().get_center()
	await touch(app,start,true)
	await drag(app,start,start-Vector2(0,55)*ui.unit)
	await touch(app,ui.shop.get_global_rect().get_center(),false)
	expect(gameplay(app.session.snapshot())==before_invalid,"An invalid release over the dock cannot place or move anything")
	await capture("03-invalid-release")
	ui.rejection.hide()
	app.armed_item.clear()
	ui.active_item = ""
	app._refresh()
	await tap(app,ui.layers.people)
	expect(ui.cards.size()==3,"People keeps the three native chef previews")
	await capture("03-people")
	await tap(app,ui.cards[0])
	expect(app.recipe_ui.visible and not app.staff_ui.modal.visible,"A chef tap opens Recipes directly")
	app.recipe_ui.dismiss()
	await tap(app,ui.layers.floor)
	expect(ui.cards.size()==1 and ui.cards[0].disabled,"Floor retains its single disabled current swatch")
	expect(ui.cards[0].get_meta("name_label").visible and ui.cards[0].get_meta("stock").visible,"The disabled Floor swatch retains its native caption and Current status")
	var floor_state := gameplay(app.session.snapshot())
	start = ui.cards[0].get_global_rect().get_center()
	await touch(app,start,true)
	await drag(app,start,start-Vector2(0,70)*ui.unit)
	await touch(app,start-Vector2(0,70)*ui.unit,false)
	expect(gameplay(app.session.snapshot())==floor_state and app.world.editor_preview.is_empty(),"Dragging a disabled swatch cannot pick it up or pan the room")
	await capture("04-floor")
	await tap(app,ui.layers.layout)
	await tap(app,ui.layers.layout)
	expect(not ui.tray.visible and ui.category_rail.visible,"Existing active-category collapse remains available")
	await capture("05-collapsed")
	await tap(app,ui.layers.layout)
	expect(ui.tray.visible,"Active category reopens the continuous board")
	await tap(app,ui.live)
	expect(app.session.snapshot().mode=="live" and not ui.visible,"Live returns to the existing simulation")
	app.advance_time(1)
	expect(app.session.snapshot().elapsed>0,"Live resumes the service clock")
	app._editor_command({"type":"set_mode","mode":"edit"})
	app._editor_command({"type":"editor_layer","layer":"layout"})
	await capture("06-layout-final")
