extends SceneTree
## Actual viewport touch dispatch, native controls, persistence and captures.
const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
var checks := 0
var failures: Array[String] = []
var output := ""
var app

func _initialize() -> void:
	call_deferred("run")

func expect(value: bool, message: String) -> bool:
	checks += 1
	if not value: failures.append(message)
	return value

func frames(count := 3) -> void:
	for index in range(count): await process_frame

func touch(at: Vector2, down: bool, canceled := false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 13
	event.position = app.get_viewport_transform() * at
	event.pressed = down
	event.canceled = canceled
	Input.parse_input_event(event)
	await frames()

func drag(start: Vector2, end: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 13
	event.position = app.get_viewport_transform() * end
	event.relative = app.get_viewport_transform().basis_xform(end - start)
	Input.parse_input_event(event)
	await frames()

func tap(at: Vector2) -> void:
	await touch(at, true)
	await touch(at, false)

func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func same(a: Variant, b: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(a, "", true, true)) == JSON.parse_string(JSON.stringify(b, "", true, true))

func count_stock() -> int:
	return int(app.session.snapshot().inventory.filter(func(item): return item.id == "belt-tile")[0].count)

func sprite_point(identity: String) -> Vector2:
	for hit in app.world.sprite_hits():
		if hit.owner_id != identity: continue
		for y in range(2, 9):
			for x in range(2, 9):
				var point: Vector2 = hit.rect.position + hit.rect.size * Vector2(x, y) * 0.1
				if app.world.object_at(point).get("id", "") == identity and app._floor_drop(point): return point
	return Vector2(-1, -1)

func persisted() -> bool:
	var saved: Dictionary = app.store.load_session(app._valid_saved_session)
	var peer := Session.new()
	return peer.restore(saved) and same(peer.snapshot(), app.session.snapshot())

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Use tools/test_native.py for isolated save storage.")
		quit(1)
		return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size() == 2: root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = APP.instantiate()
	app.simulation_enabled = false
	# Start without reading/writing the shared test save, then exercise real
	# persistence in this suite's own directory so other suites stay independent.
	app.show_editor_gallery = true
	root.add_child(app)
	app.audio.set_muted(true)
	await frames()
	app.store = Store.new("user://issue13-conveyor")
	app.store.clear_session()
	app.show_editor_gallery = false
	app.session = Session.new_session(1313)
	app.session.command({"type":"set_entrance_open","open":false})
	app._refresh()
	app._layout()
	await tap(app.edit.get_global_rect().get_center())
	var ui = app.editor_ui
	var card: Button = ui.cards[0]
	var start: Vector2 = card.get_global_rect().get_center()
	var destination: Vector2 = app.world.cell_base(1,3)
	await touch(start,true)
	await drag(start,destination)
	await touch(destination,false)
	if not expect(count_stock() == 5 and app.session.snapshot().editor.belt_path.size() == 1, "An actual upward inventory drag spends one belt and enters path construction"):
		await finish()
		return
	expect(persisted(), "The accepted inventory drop is already durably saved before Live")
	expect(ui.path_exit.visible and ui.path_count.text == "Belt tiles\n5 left", "The native path capsule exposes live stock and Inventory exit")
	await capture("01-path-start")
	for control: Control in [ui.rotate, ui.remove, ui.path_exit]:
		var physical: Rect2 = app.get_viewport_transform() * control.get_global_rect()
		expect(physical.size.x >= 44 and physical.size.y >= 44 and app.world.portrait.encloses(control.get_global_rect()), "Every path action has a contained 44px target")
	var pressed_before: Dictionary = app.session.save_data()
	var press: Vector2 = ui.rotate.get_global_rect().get_center()
	await touch(press,true)
	expect(ui.rotate.get_meta("visual_pressed",false), "Native pointer down shows the approved pressed Rotate state")
	await capture("02-path-pressed")
	await touch(press,false,true)
	expect(same(pressed_before,app.session.save_data()), "A canceled press preserves the accepted construction state")
	for cell in [Vector2i(2,3),Vector2i(3,3),Vector2i(3,4),Vector2i(2,4),Vector2i(1,4)]:
		var before := count_stock()
		await tap(app.world.cell_base(cell.x,cell.y))
		expect(count_stock() == before-1, "A highlighted neighboring-cell touch spends exactly one tile")
		if cell == Vector2i(3,4): await capture("03-path-turn")
	if not expect(count_stock() == 0 and app.session.snapshot().editor.belt_path.size() == 6, "Real touches reach zero stock without exiting path construction"):
		await finish()
		return
	expect(not ui.rotate.disabled and not ui.remove.disabled and not ui.path_exit.disabled, "Rotate, Return and Inventory remain usable at zero stock")
	await capture("04-zero-stock")
	var unchanged: Dictionary = app.session.save_data()
	await tap(app.world.cell_base(0,4))
	expect(same(unchanged,app.session.save_data()) and ui.rejection.text == "No belt tiles left" and ui.rejection.visible, "An empty extension at zero stock rejects without mutation and shows the brief shortage toast")
	await capture("05-shortage-feedback")
	await tap(ui.cards[0].get_global_rect().get_center())
	expect(same(unchanged,app.session.save_data()) and ui.rejection.text == "No belt tiles left" and ui.rejection.visible, "Tapping the exhausted ordinary inventory item gives the same nonmodal shortage feedback")
	await create_timer(1.4).timeout
	var saved: Dictionary = app.store.load_session(app._valid_saved_session)
	var reopened := Session.new()
	expect(reopened.restore(saved), "The actual persisted path reopens through the public validator")
	app.session = reopened
	app._refresh()
	await frames()
	expect(app.session.snapshot().editor.belt_path.size() == 6 and count_stock() == 0 and ui.path_exit.visible, "Reopening retains the zero-stock path cursor and usable controls")
	await capture("06-reopened-path")
	var first: String = app.session.snapshot().editor.belt_path[0]
	var first_point := sprite_point(first)
	expect(first_point.x >= 0, "The starting tile exposes selectable rendered pixels")
	await tap(first_point)
	expect(count_stock() == 0 and app.session.snapshot().editor.belt_path.is_empty() and persisted(), "Tapping the starting tile's actual raised sprite closes the loop for free and saves it")
	await capture("07-loop-closed-selected")
	# Resume from a rendered existing tile at zero stock, then exercise keyboard
	# target focus, Return, interrupted object movement and Android Back policy.
	await tap(ui.layers.layout.get_global_rect().get_center())
	app._editor_command({"type":"editor_select","id":first})
	await frames()
	var target: Button = ui.path_targets.filter(func(button): return button.visible and button.get_meta("target").kind == "reuse" and button.get_meta("target").valid)[0]
	var stock_before := count_stock()
	target.grab_focus()
	var key := InputEventKey.new()
	key.keycode = KEY_ENTER
	key.pressed = true
	Input.parse_input_event(key)
	await frames()
	key = InputEventKey.new()
	key.keycode = KEY_ENTER
	key.pressed = false
	Input.parse_input_event(key)
	await frames()
	expect(app.session.snapshot().editor.belt_path.size() == 2 and count_stock() == stock_before, "A focused native neighbor target supports keyboard reuse at zero stock")
	var selected: String = app.session.snapshot().editor.selected_id
	var selected_point := sprite_point(selected)
	var move_before: Dictionary = app.session.save_data()
	await touch(selected_point,true)
	await drag(selected_point,selected_point+Vector2(0,app.world.cell*2))
	await touch(selected_point+Vector2(0,app.world.cell*2),false,true)
	expect(same(move_before,app.session.save_data()), "A canceled selected-sprite drag preserves graph, stock, food and saved path")
	await tap(ui.remove.get_global_rect().get_center())
	expect(count_stock() == 1 and app.session.snapshot().editor.belt_path.size() == 1 and persisted(), "Return stores the latest tile and restores its prior path cursor")
	await tap(app.world.cell_base(5,4))
	expect(app.session.snapshot().editor.belt_path.is_empty() and app.session.snapshot().mode == "edit", "An outside highlighted-cell tap ends construction and returns to inventory")
	app._editor_command({"type":"editor_select","id":first})
	app._notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	expect(app.session.snapshot().mode == "edit" and app.session.snapshot().editor.belt_path.is_empty(), "System Back exits path mode before leaving the restaurant")
	app._editor_command({"type":"editor_select","id":first})
	await frames()
	await tap(ui.path_exit.get_global_rect().get_center())
	expect(app.session.snapshot().editor.belt_path.is_empty() and app.session.snapshot().editor.tray_open and persisted(), "The visible X Inventory action exits construction with all edits already saved")
	# Capture the shared native presentation at zero stock from the exact same
	# gameplay state and components, without introducing a separate UI fixture.
	app.session.restore(saved)
	app.show_editor_gallery = true
	app._refresh()
	await frames()
	expect(app.editor_ui.get_script().resource_path == "res://scripts/wood_editor_presentation.gd", "Shared review uses the exact gameplay presentation")
	await capture("08-shared-construction-gallery")
	# Filled-loop fixture for visible live plate motion and corner alignment.
	app.session.restore(saved)
	app.session.command({"type":"editor_belt_extend","x":1,"y":3})
	var food: Dictionary = app.session.save_data()
	var dish_index := 1
	for tile in food.state.objects:
		if tile.kind == "belt" and tile.id.begins_with("editor-object-"):
			tile.dish = {"id":"dish-%s" % dish_index,"recipe_id":"salmon_nigiri"}
			dish_index += 1
	food.state.next_dish_id = dish_index
	expect(app.session.restore(food), "The visible full-loop food fixture passes normal save validation")
	app.session.command({"type":"set_mode","mode":"live"})
	app.advance_time(0.45)
	app._refresh()
	await frames()
	await capture("09-live-full-loop")
	await finish()

func finish() -> void:
	for failure in failures: printerr("FAIL: " + failure)
	print("Conveyor native: %s checks, %s failures" % [checks,failures.size()])
	if not output.is_empty():
		var report := {"checks":checks,"failures":failures,"window":[root.size.x,root.size.y],"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"ui":app.editor_ui.get_script().resource_path}
		var file := FileAccess.open(output.path_join("capture-report.json"),FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"\t")+"\n")
	var status := 0 if failures.is_empty() else 1
	app.store.clear_session()
	app.queue_free()
	app = null
	await frames()
	quit(status)
