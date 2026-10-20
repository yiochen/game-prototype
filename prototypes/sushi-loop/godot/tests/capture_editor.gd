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
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	app.session = Session.new_session(41)
	app.advance_time(1.0)
	app._layout()
	await capture("01-live-before-edit")
	await tap(app.edit.get_global_rect().get_center())
	await capture("02-edit-layout")
	await tap(app.world.cell_base(2, 5))
	verify(str(app.session.snapshot().editor.selected_id) == "seat-1", "The demonstrated stool must be selected")
	await capture("03-selected-stool")
	await touch(app.editor_ui.rotate.get_global_rect().get_center(), true)
	await capture("04-rotate-pressed")
	await touch(app.editor_ui.rotate.get_global_rect().get_center(), false)
	await capture("05-stool-rotated")
	var at: Vector2 = app.world.cell_base(2, 5)
	var target: Vector2 = app.world.cell_base(3, 5)
	await touch(at, true)
	await drag(at, target)
	await capture("06-valid-object-drag")
	await touch(target, false)
	verify(object_at("seat-1").x == 3 and object_at("seat-1").y == 5, "The demonstrated selected move must commit")
	await capture("07-object-moved")
	var blocked: Vector2 = app.world.cell_base(3, 6)
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
	await capture("13-inventory-next-page")
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
	await capture("21-shared-roster-boundary-disabled")
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

func touch(at: Vector2, down: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 22
	event.position = app.get_viewport_transform() * at
	event.pressed = down
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
	screens.append({"name": name, "pixels": [image.get_width(), image.get_height()], "canvas": [app.size.x, app.size.y], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "cell_pitch": app.world.cell, "editor": app.session.snapshot().editor, "session": app.session.snapshot()})

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

func object_at(identity: String) -> Dictionary:
	for object in app.session.snapshot().objects:
		if str(object.id) == identity: return object
	return {}

func verify(condition: bool, description: String) -> void:
	if not condition:
		push_error(description)
		quit(1)
