extends SceneTree
## Regression: Live Staff must not leave Edit controls hidden or unresponsive.
const Session = preload("res://scripts/session.gd")
var app
var checks := 0
var failures: Array[String] = []
var output := ""
func _initialize() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message);printerr("FAIL: " + message)
func frames() -> void:
	for i in range(3): await process_frame
func touch(at: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 43
	event.position = app.get_viewport_transform() * at
	event.pressed = pressed
	Input.parse_input_event(event)
	await frames()
func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center()
	await touch(at, true)
	await touch(at, false)
func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		quit(1);return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size() == 2: root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = load("res://main.tscn").instantiate()
	app.show_editor_gallery = true # Skip all ordinary user-data reads and writes.
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	app.session = Session.new_session(81)
	app._refresh();app._layout()
	await frames()
	check(not app.get_property_list().any(func(property): return property.name == "staff"), "The main scene has no separate Staff action")
	for cycle in range(2):
		await tap(app.edit)
		var ui = app.editor_ui
		check(app.session.snapshot().mode == "edit", "The Edit button enters paused Edit")
		check(ui.live.is_visible_in_tree(), "Return to Live remains visible in Edit")
		check(ui.category_rail.is_visible_in_tree() and ui.shop.is_visible_in_tree(), "Edit keeps the category rail and Shop visible")
		await capture("%s-edit-layout" % cycle)
		if not ui.live.is_visible_in_tree() or not ui.category_rail.is_visible_in_tree():
			await finish();return
		var accessible := true
		for control in [ui.live,ui.layers.people,ui.layers.layout,ui.layers.floor]:
			var physical: Rect2 = app.get_viewport_transform() * control.get_global_rect()
			accessible = accessible and physical.size.x >= 43.99 and physical.size.y >= 43.99 and not control.accessibility_name.is_empty()
		check(accessible, "Edit navigation retains accessible names and 44px physical targets")
		for layer in ["people","floor","layout"]:
			await tap(ui.layers[layer])
			check(app.session.snapshot().editor.layer == layer and ui.tray.is_visible_in_tree(), "Touch opens the %s inventory tab" % layer)
			check(ui.cards.size() == {"people":3,"floor":1,"layout":5}[layer], "The %s tab shows its own inventory" % layer)
			await capture("%s-tab-%s" % [cycle,layer])
		await tap(ui.layers.layout)
		check(not ui.tray.visible, "The active tab can collapse its tray")
		await tap(ui.layers.layout)
		check(ui.tray.visible, "The active tab can reopen its tray")
		await tap(ui.layers.people)
		await tap(ui.applicants)
		await tap(app.staff_ui.close_button)
		await create_timer(.25).timeout
		check(not app.staff_ui.modal.visible and ui.live.is_visible_in_tree() and ui.category_rail.is_visible_in_tree(), "Closing applications preserves Edit navigation")
		await tap(ui.layers.floor)
		check(app.session.snapshot().editor.layer == "floor", "Inventory tabs still respond after closing applications")
		var elapsed: float = app.session.snapshot().elapsed
		await tap(ui.live)
		check(app.session.snapshot().mode == "live" and not ui.is_visible_in_tree() and app.edit.is_visible_in_tree(), "Return to Live exits Edit through the real native button")
		app.advance_time(.5)
		check(app.session.snapshot().elapsed > elapsed, "Returning to Live resumes the service clock")
		await capture("%s-returned-live" % cycle)
	# The People actions occupy the same continuous tray as the photos.
	await tap(app.edit);await tap(app.editor_ui.layers.people)
	check(app.editor_ui.applicants.get_parent() == app.editor_ui.tray and app.editor_ui.tray.get_global_rect().encloses(app.editor_ui.applicants.get_global_rect()), "Applicants belongs inside the People tray")
	check(app.editor_ui.rail.get_global_rect().position.y >= app.editor_ui.applicants.get_global_rect().end.y, "Applicants and the photo strip have separate non-overlapping hit areas")
	await capture("people-integrated-applicants")
	await finish()
func finish() -> void:
	app.queue_free();await frames()
	print("Edit navigation: %s checks, %s failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)
