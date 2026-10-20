extends SceneTree
## Review the actual native editor using production controls and screen gestures.
const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
var app
var destination := ""
var screens: Array = []

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("An isolated capture output directory is required.")
		quit(1)
		return
	# macOS may clamp the initial --resolution to its desktop work area. Match
	# the isolated native test's explicit window size before laying out the app.
	var requested_size := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if requested_size.size() == 2 and requested_size[0].is_valid_int() and requested_size[1].is_valid_int():
		root.size = Vector2i(int(requested_size[0]), int(requested_size[1]))
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	app.session = Session.new_session(41)
	# This isolated review camera lifts the existing two counters above the
	# open drawer; it does not change runtime camera defaults or user saves.
	app.session.command({"type": "set_camera", "x": 0.0, "y": 1.25})
	app.advance_time(1.0)
	app._layout()
	await capture("01-live-before-edit")
	await tap(app.edit.get_global_rect().get_center())
	verify(app.editor_ui.cards.size() == 4 and app.editor_ui.cards[3].get_meta("entry").id == "crate-wood", "Layout must open with the first four goods")
	await capture("02-edit-layout")
	var curtain: Button = app.editor_ui.layers.people
	var curtain_target := curtain.get_global_rect()
	var rod_target: Rect2 = app.editor_ui.category_rod.get_global_rect()
	var before_press: Dictionary = app.session.save_data()
	await touch(curtain_target.get_center(), true)
	await capture("02a-curtain-pressed")
	verify(curtain.get_meta("visual").scale.x < 1.0 and curtain.get_global_rect() == curtain_target and app.editor_ui.category_rod.get_global_rect() == rod_target and same(before_press, app.session.save_data()), "Holding a curtain must press only its artwork before category activation")
	verify(curtain.get_meta("visual_surface").get_theme_stylebox("panel").region == app.editor_ui.skin.style("tab-idle", app.editor_ui.unit).region, "Holding an inactive curtain must preserve the current selection underline until release")
	verify(curtain.get_meta("visual_focus").get_theme_stylebox("panel").bg_color.a == 0, "The curtain focus cue must stay transparent and keep the current selection underline")
	await touch(curtain_target.get_center(), false, true)
	await capture("02a2-curtain-cancelled")
	verify(curtain.get_meta("visual").scale.is_equal_approx(Vector2.ONE) and same(before_press, app.session.save_data()), "Canceling a curtain must restore its artwork without changing the editor")
	await touch(curtain_target.get_center(), true)
	app.propagate_notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	verify(not bool(curtain.get_meta("visual_pressed", false)) and curtain.get_meta("visual").scale.is_equal_approx(Vector2.ONE), "Pausing while a curtain is held must immediately cancel its native and visual press")
	app.propagate_notification(Node.NOTIFICATION_APPLICATION_RESUMED)
	await touch(curtain_target.get_center(), false)
	verify(same(before_press, app.session.save_data()), "An orphan release after pausing must preserve the current category and paused restaurant")
	var before_shop: Dictionary = app.session.save_data()
	await tap(app.editor_ui.shop.get_global_rect().get_center())
	verify(same(before_shop, app.session.save_data()) and app.editor_ui.rejection.visible, "Editor Shop must show unavailable feedback without changing the paused restaurant")
	await capture("02b-editor-shop-unavailable")
	await create_timer(1.35).timeout
	await tap(sprite_point("seat-1"))
	verify(str(app.session.snapshot().editor.selected_id) == "seat-1", "The demonstrated stool must be selected")
	await capture("03-selected-stool")
	await touch(app.editor_ui.rotate.get_global_rect().get_center(), true)
	await capture("04-rotate-pressed")
	await touch(app.editor_ui.rotate.get_global_rect().get_center(), false)
	await capture("05-stool-rotated")
	var at: Vector2 = sprite_point("seat-1")
	var target: Vector2 = app.world.cell_base(3, 5) + at - app.world.cell_base(2, 5)
	await touch(at, true)
	await drag(at, target)
	await capture("06-valid-object-drag")
	await touch(target, false)
	verify(object_at("seat-1").x == 3 and object_at("seat-1").y == 5, "The demonstrated selected move must commit")
	await capture("07-object-moved")
	target = sprite_point("seat-1")
	var blocked: Vector2 = app.world.cell_base(3, 6) + target - app.world.cell_base(3, 5)
	await touch(target, true)
	await drag(target, blocked)
	await capture("08-invalid-object-drag")
	await touch(blocked, false)
	verify(object_at("seat-1").x == 3 and object_at("seat-1").y == 5 and app.editor_ui.rejection.visible, "The occupied drop must reject and keep the valid arrangement")
	await capture("09-rejected-drop")
	await tap(app.editor_ui.remove.get_global_rect().get_center())
	verify(object_at("seat-1").is_empty(), "The demonstrated return must actually remove the selected stool")
	await capture("10-returned-to-inventory")
	var inventory_start: Vector2 = app.editor_ui.cards[1].get_global_rect().get_center()
	var place: Vector2 = app.world.cell_base(3, 4)
	await touch(inventory_start, true)
	await drag(inventory_start, place)
	await capture("11-inventory-placement-preview")
	await touch(place, false)
	verify(not object_at(str(app.session.snapshot().editor.selected_id)).is_empty() and object_at(str(app.session.snapshot().editor.selected_id)).x == 3 and object_at(str(app.session.snapshot().editor.selected_id)).y == 4, "The inventory drop must place a new selected object")
	await capture("12-inventory-placed")
	await tap(app.editor_ui.next.get_global_rect().get_center())
	verify(app.editor_ui.cards.size() == 1 and app.editor_ui.cards[0].get_meta("entry").id == "barrel-wood" and app.editor_ui.next.disabled and not app.editor_ui.previous.disabled, "The final Layout page must contain the fifth good with the correct paging boundaries")
	await capture("13-inventory-next-page")
	await tap(app.editor_ui.previous.get_global_rect().get_center())
	verify(app.editor_ui.cards.size() == 4 and app.editor_ui.cards[3].get_meta("entry").id == "crate-wood" and app.editor_ui.previous.disabled, "Paging back must restore the first four goods")
	await capture("13b-inventory-previous-page")
	await tap(app.editor_ui.layers.people.get_global_rect().get_center())
	await capture("14-people-profiles")
	await tap(app.editor_ui.cards[0].get_global_rect().get_center())
	await capture("14b-profile-inspection")
	await tap(app.editor_ui.inspection_close.get_global_rect().get_center())
	await tap(app.editor_ui.layers.people.get_global_rect().get_center())
	await capture("15-collapsed-tray")
	await tap(app.editor_ui.layers.floor.get_global_rect().get_center())
	await capture("16-floor-current-disabled")
	app.save_now()
	var expected: Dictionary = app.session.snapshot()
	app.queue_free()
	await frames()
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	if not same(expected, app.session.snapshot()):
		push_error("Editor capture reopened a different state.")
		quit(1)
		return
	await capture("17-reopened-editor")
	var working_store = app.store
	var obstacle := FileAccess.open("user://editor-capture-write-obstacle", FileAccess.WRITE)
	obstacle.store_string("Blocks the test save directory")
	obstacle.close()
	app.store = Store.new("user://editor-capture-write-obstacle")
	app._editor_command({"type": "editor_rotate", "id": app.session.snapshot().editor.selected_id})
	verify(app.pending_edit_save, "The save-retry capture must show a genuine failed immediate write")
	await capture("17b-pending-save-retry")
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://editor-capture-write-obstacle"))
	await tap(app.recovery_retry.get_global_rect().get_center())
	verify(not app.save_blocked, "Retry must save the same in-memory arrangement")
	app.store = working_store
	app.save_now()
	await tap(app.editor_ui.live.get_global_rect().get_center())
	app.advance_time(1.0)
	await capture("18-live-resumed")
	app.queue_free()
	await frames()
	app = APP.instantiate()
	app.show_editor_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	await capture("19-shared-editor-normal")
	await touch(app.editor_ui.layers.people.get_global_rect().get_center(), true)
	await capture("20-shared-layer-pressed")
	await touch(app.editor_ui.layers.people.get_global_rect().get_center(), false)
	verify(app.editor_ui.cards.size() == 3 and app.editor_ui.previous.disabled and app.editor_ui.next.disabled, "The People page must retain three profiles and quiet boundary carets")
	await capture("21-shared-roster-boundary-disabled")
	await tap(app.editor_ui.layers.floor.get_global_rect().get_center())
	verify(app.editor_ui.cards.size() == 1 and app.editor_ui.cards[0].disabled and app.editor_ui.cards[0].get_meta("preview").goods.has("floor-cream"), "The shared Floor preview must use the separate Blender slab render")
	await capture("22-shared-floor-current")
	app.world.reduced_motion = true
	app._refresh()
	var reduced_target: Rect2 = app.editor_ui.layers.people.get_global_rect()
	await touch(reduced_target.get_center(), true)
	verify(app.editor_ui.layers.people.get_meta("visual").scale.is_equal_approx(Vector2.ONE * 0.975) and app.editor_ui.layers.people.get_global_rect() == reduced_target, "Reduced motion must show the pressed curtain immediately without moving its target")
	await capture("23-shared-reduced-motion-pressed")
	await touch(reduced_target.get_center(), false)
	verify(app.editor_ui.layers.people.get_meta("visual").scale.is_equal_approx(Vector2.ONE) and app.session.snapshot().editor.layer == "people", "Reduced-motion release must restore the artwork and activate People")
	await capture("24-shared-reduced-motion-released")
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": screens, "input": "Actual InputEventScreenTouch and InputEventScreenDrag through the production viewport", "shared_presentation": "res://scripts/editor_presentation.gd"}, "\t"))
	file.close()
	print("Captured %s actual native editor states" % screens.size())
	app.queue_free()
	await frames()
	await create_timer(0.1).timeout
	quit(0)

func frames(count := 3) -> void:
	for index in range(count): await process_frame

func touch(at: Vector2, down: bool, cancelled := false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 22
	event.position = app.get_viewport_transform() * at
	event.pressed = down
	event.canceled = cancelled
	Input.parse_input_event(event)
	await frames(2)

func drag(from: Vector2, to: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 22
	event.position = app.get_viewport_transform() * to
	event.relative = app.get_viewport_transform().basis_xform(to - from)
	Input.parse_input_event(event)
	await frames(2)

func tap(at: Vector2) -> void:
	await touch(at, true)
	await touch(at, false)
	await create_timer(0.23).timeout

func capture(name: String) -> void:
	await frames()
	await create_timer(0.23).timeout
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image.save_png(destination.path_join(name + ".png")) != OK:
		push_error("Could not save " + name)
	screens.append({"name": name, "pixels": [image.get_width(), image.get_height()], "canvas": [app.size.x, app.size.y], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "cell_pitch": app.world.cell, "editor": app.session.snapshot().editor, "presentation": presentation_state(), "session": app.session.snapshot()})

func rect_values(control: Control) -> Array:
	return rect_array(control.get_global_rect())

func rect_array(bounds: Rect2) -> Array:
	return [bounds.position.x, bounds.position.y, bounds.size.x, bounds.size.y]

func presentation_state() -> Dictionary:
	var editor = app.editor_ui
	var result := {"backing_visible": editor.inventory_backing.is_visible_in_tree(), "backing_mouse_filter": editor.inventory_backing.mouse_filter, "backing_color": editor.inventory_backing.color.to_html(true), "rod_face": rect_array(editor.skin.face_rect("noren-rod", editor.category_rod.get_global_rect(), editor.unit)), "category_panel_drawn": not (editor.category_rail.get_theme_stylebox("panel") is StyleBoxEmpty), "backing": rect_values(editor.inventory_backing), "rod": rect_values(editor.category_rod), "dock": rect_values(editor.bottom_dock), "tray": rect_values(editor.tray), "coin_capsule": rect_values(app.coin_panel), "editing_capsule": rect_values(app.editing_panel), "coin_face": rect_array(editor.skin.face_rect("coin-panel", app.coin_panel.get_global_rect(), editor.unit)), "editing_face": rect_array(editor.skin.face_rect("control-wood", app.editing_panel.get_global_rect(), editor.unit)), "coin_icon": rect_values(app.coin), "coin_text": rect_values(app.money), "editing_icon": rect_values(app.editing_icon), "editing_text": rect_values(app.editing_cue), "reduced_motion": editor.reduced_motion, "buttons": {}, "goods": []}
	for key in ["people", "layout", "floor", "shop", "live", "previous", "next", "rotate", "remove"]:
		var button: Button = editor.layers[key] if editor.layers.has(key) else editor.get(key)
		var visual: Control = button.get_meta("visual")
		var physical: Rect2 = app.get_viewport_transform() * button.get_global_rect()
		var stacked: bool = button.get_meta("visual_stacked", false)
		var face: Rect2 = editor.skin.face_rect(str(button.get_meta("skin_role")), visual.get_global_rect(), editor.unit)
		if stacked:
			var bubble_face: Rect2 = editor.skin.face_rect("context-bubble", editor.context_bubble.get_global_rect(), editor.unit)
			face.position.y = bubble_face.position.y
			face.size.y = bubble_face.size.y
		result.buttons[key] = {"target": rect_values(button), "artwork": rect_values(visual), "face": rect_array(face), "stacked": stacked, "visible": button.is_visible_in_tree(), "surface_visible": button.get_meta("visual_surface").is_visible_in_tree(), "surface_drawn": button.get_meta("visual_surface").is_visible_in_tree() and not (button.get_meta("visual_surface").get_theme_stylebox("panel") is StyleBoxEmpty), "icon": rect_values(button.get_meta("visual_icon")), "caption": rect_values(button.get_meta("visual_label")), "scale": [visual.scale.x, visual.scale.y], "physical_target": [physical.size.x, physical.size.y], "disabled": button.disabled, "pressed": bool(button.get_meta("visual_pressed", false))}
	for card in editor.cards:
		var preview: Control = card.get_meta("preview")
		result.goods.append({"id": card.get_meta("entry").id, "target": rect_values(card), "preview": rect_values(preview), "caption": card.get_meta("name_label").text, "caption_bounds": rect_values(card.get_meta("name_label")), "stock": card.get_meta("stock").text, "stock_bounds": rect_values(card.get_meta("stock")), "blender_preview": preview.goods.has(str(card.get_meta("entry").art_id))})
	return result

func same(a: Variant, b: Variant) -> bool:
	if (a is int or a is float) and (b is int or b is float): return absf(float(a) - float(b)) < 0.000000001
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size(): return false
		for key in a:
			if not b.has(key) or not same(a[key], b[key]): return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size(): return false
		for index in range(a.size()):
			if not same(a[index], b[index]): return false
		return true
	return a == b

func sprite_point(identity: String) -> Vector2:
	var object := object_at(identity)
	var ground: Vector2 = app.world.cell_base(float(object.x), float(object.y))
	var best := Vector2(INF, INF)
	var distance := INF
	for record in app.world.sprite_hits():
		if str(record.owner_id) != identity: continue
		var pixels: Image = record.texture.get_image()
		if pixels.is_compressed(): pixels.decompress()
		var region: Rect2 = record.region
		var bounds: Rect2 = record.rect
		for y in range(3, int(region.size.y), 8):
			for x in range(3, int(region.size.x), 8):
				if pixels.get_pixelv(Vector2i(region.position) + Vector2i(x, y)).a < 0.9: continue
				var point := bounds.position + (Vector2(x, y) + Vector2(0.5, 0.5)) / region.size * bounds.size
				if point.distance_squared_to(ground) >= distance or not app._floor_drop(point): continue
				if app.world.object_at(point).get("id") != identity: continue
				best = point
				distance = point.distance_squared_to(ground)
	verify(best.is_finite(), "The %s gesture starts on a visible opaque owned sprite pixel outside protected UI" % identity)
	return best

func object_at(identity: String) -> Dictionary:
	for object in app.session.snapshot().objects:
		if str(object.id) == identity: return object
	return {}

func verify(condition: bool, description: String) -> void:
	if not condition:
		push_error(description)
		quit(1)
