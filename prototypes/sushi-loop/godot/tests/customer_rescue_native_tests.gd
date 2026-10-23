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
	if app.editor_ui.rejection.visible:
		await create_timer(maxf(0.0, app.editor_ui.rejection_seconds) + 0.05).timeout
	# Capture the completed selection transition, or the actual held press /
	# drag, rather than a near-transparent first frame of the UI tween.
	await create_timer(0.18).timeout
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

func configuration(trap := false) -> Dictionary:
	var objects: Array = [
		{"id":"chef","kind":"chef","name":"Lena","art_id":"chef-lena","recipe_id":"salmon_nigiri","x":1,"y":7,"facing":"north"},
		{"id":"belt1","kind":"belt","x":1,"y":6,"facing":"east"},
		{"id":"belt2","kind":"belt","x":2,"y":6,"facing":"east"},
		{"id":"seat","kind":"seat","x":2,"y":5,"facing":"south"}]
	if trap:
		objects = [{"id":"chef","kind":"chef","name":"Lena","art_id":"chef-lena","recipe_id":"salmon_nigiri","x":2,"y":8,"facing":"east"},{"id":"belt1","kind":"belt","x":3,"y":8,"facing":"south"},{"id":"seat","kind":"seat","x":3,"y":7,"facing":"south"}]
		for row in [4,6]:
			for x in range(7):
				if x != 3: objects.append({"id":"wall-%s-%s" % [row,x],"kind":"belt","x":x,"y":row,"facing":"east"})
	return {"objects":objects,"service":{"first_arrival_seconds":0.1,"arrival_seconds":1000.0,"arrival_jitter_seconds":0.0,"eating_seconds":8.0},"customers":{"fullness_min":1.0,"fullness_max":1.0,"dish_fullness_min":1.0,"dish_fullness_max":1.0,"eating_jitter_seconds":0.0}}

func saved_guest() -> Dictionary:
	return app.session.save_data().state.customers[0] if not app.session.snapshot().customers.is_empty() else {}

func load_scenario(trap := false) -> void:
	app._cancel_gesture()
	app.session = Session.new_session(1414,configuration(trap))
	for index in range(600):
		app.session.advance(0.05)
		if not saved_guest().is_empty() and ((trap and saved_guest().phase == "walking" and float(saved_guest().y) >= 5.0) or (not trap and saved_guest().phase == "eating")): break
	app.session.command({"type":"set_mode","mode":"edit"})
	app._refresh()
	app._layout()
	await frames()

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Use tools/test_native.py for isolated save storage.")
		quit(1)
		return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size() == 2: root.size = Vector2i(int(dimensions[0]),int(dimensions[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = APP.instantiate()
	app.simulation_enabled = false
	app.show_editor_gallery = true
	root.add_child(app)
	app.audio.set_muted(true)
	await frames()
	app.store = Store.new("user://issue14-rescue")
	app.store.clear_session()
	app.show_editor_gallery = false
	await load_scenario()
	if not expect(saved_guest().get("phase") == "eating", "The native scenario begins with a real eating customer"):
		await finish()
		return
	var ui = app.editor_ui
	var guest_id: String = saved_guest().id
	var meal: Dictionary = saved_guest().meal_dish.duplicate(true)
	var point := sprite_point("seat")
	if not expect(point.x>=0,"The occupied seat is selectable through its customer's rendered body"):
		await finish()
		return
	await tap(point)
	expect(app.session.snapshot().editor.selected_id == "seat" and ui.context_bubble.visible,"Layout selects the occupied stool and shows its shared object controls")
	await capture("01-occupied-seat-selected")
	var before: Dictionary = app.session.save_data()
	var press: Vector2 = ui.rotate.get_global_rect().get_center()
	await touch(press,true)
	expect(ui.rotate.get_meta("visual_pressed",false),"The occupied-seat Rotate control has actual pointer-down feedback")
	await capture("02-occupied-seat-pressed")
	await touch(press,false,true)
	expect(same(before,app.session.save_data()),"Canceling an occupied-seat action preserves the complete prior state")
	point = sprite_point("seat")
	var destination: Vector2 = point+Vector2(-app.world.cell,0)
	await touch(point,true)
	await drag(point,destination)
	expect(app.world.editor_preview.get("valid",false),"The carried-person preview validates the same public command as the real drop")
	await capture("03-carried-customer-preview")
	await touch(destination,false)
	expect(saved_guest().x == 1 and saved_guest().y == 5 and saved_guest().meal_dish == meal and same(saved_guest().meal_elapsed,before.state.customers[0].meal_elapsed),"An actual stool drag carries its recognizable customer and exact unfinished plate")
	expect(persisted(),"The occupied-seat move is durably saved before Live")
	await capture("04-carried-customer-dropped")
	await tap(ui.remove.get_global_rect().get_center())
	expect(saved_guest().phase == "standing" and saved_guest().seat_id == "" and saved_guest().meal_dish == meal,"Returning the seat leaves the same guest standing with their meal")
	expect(app.world.customer_feedback(app.session.snapshot().customers[0]).is_empty(),"New standing reactions are deferred while paused")
	await capture("05-seat-removed-paused")
	await tap(ui.live.get_global_rect().get_center())
	app.advance_time(1.2)
	expect(app.world.customer_feedback(app.session.snapshot().customers[0]).get("object") == "bubble-puzzled","The standing guest visibly looks puzzled after Live resumes")
	expect(saved_guest().meal_elapsed == before.state.customers[0].meal_elapsed,"A standing guest does not consume or sell their unfinished meal")
	await capture("06-puzzled-standing-guest")
	await tap(app.edit.get_global_rect().get_center())
	var stool: Button = ui.cards.filter(func(card): return card.get_meta("entry").id == "stool-plain")[0]
	var start: Vector2 = stool.get_global_rect().get_center()
	var at: Vector2 = app.world.cell_base(1,5)
	await touch(start,true)
	await drag(start,at)
	await touch(at,false)
	expect(saved_guest().phase == "eating" and saved_guest().meal_dish == meal and persisted(),"Dragging suitable seating onto the guest immediately reseats and saves the same meal")
	await capture("07-immediate-reseating")
	await tap(ui.remove.get_global_rect().get_center())
	app._editor_command({"type":"editor_place","inventory_id":"crate-wood","x":1,"y":5})
	expect(saved_guest().phase == "standing" and Vector2(saved_guest().x,saved_guest().y).distance_to(Vector2(1,5)) == 1.0,"Another object visibly displaces the guest to a nearest valid floor cell")
	await capture("08-visible-displacement")
	await tap(ui.layers.people.get_global_rect().get_center())
	point = sprite_point(guest_id)
	expect(point.x>=0,"People exposes the standing guest's actual raised sprite pixels")
	await tap(point)
	expect(app.session.snapshot().editor.selected_id == guest_id and not ui.context_bubble.visible,"People selection keeps the floor marker and hides object-only Rotate/Return")
	await capture("09-people-selected")
	for target: Button in ui.customer_targets:
		if not target.visible: continue
		var physical: Rect2 = app.get_viewport_transform()*target.get_global_rect()
		expect(not target.accessibility_name.is_empty() and physical.size.x>=44 and physical.size.y>=44,"Guest selection also has a named 44px keyboard/accessibility target")
	app._notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	expect(app.session.snapshot().editor.selected_id == "" and app.session.snapshot().mode == "edit", "System Back clears customer selection and keeps Edit paused")
	var guest_target: Button = ui.customer_targets.filter(func(target): return target.visible and target.get_meta("customer_id") == guest_id)[0]
	guest_target.grab_focus()
	for down in [true,false]:
		var key := InputEventKey.new()
		key.keycode = KEY_SPACE
		key.pressed = down
		Input.parse_input_event(key)
		await frames()
	expect(app.session.snapshot().editor.selected_id == guest_id, "Keyboard activation selects the same rescuable customer")
	before = app.session.save_data()
	point = sprite_point(guest_id)
	destination = point+app.world.cell_base(1,6)-app.world.cell_base(float(saved_guest().x),float(saved_guest().y))
	await touch(point,true)
	await drag(point,destination)
	await touch(destination,false)
	expect(same(before,app.session.save_data()), "An invalid native customer drop onto an occupied belt preserves the prior state")
	point = sprite_point(guest_id)
	destination = point+Vector2(0,app.world.cell)
	await touch(point,true)
	await drag(point,destination)
	await touch(destination,false,true)
	expect(same(before,app.session.save_data()) and app.world.editor_preview.is_empty(),"An interrupted native guest drop keeps the valid prior visit and position")
	point = sprite_point(guest_id)
	await touch(point,true)
	await drag(point,destination)
	app._notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	app._notification(Node.NOTIFICATION_APPLICATION_RESUMED)
	expect(app.pointer == -1 and same(before,app.session.save_data()),"Backgrounding during rescue cancels touch ownership and saves the prior state")
	await touch(destination,false)
	var working_store = app.store
	var obstacle_path := "user://issue14-write-obstacle-%s" % Time.get_ticks_usec()
	var obstacle := FileAccess.open(obstacle_path, FileAccess.WRITE)
	obstacle.store_string("A file blocks this directory")
	obstacle.close()
	obstacle = null
	app.store = Store.new(obstacle_path)
	app._editor_command({"type":"editor_move","id":guest_id,"x":0,"y":5})
	var pending: Dictionary = app.session.save_data()
	expect(app.save_blocked and app.pending_edit_save and saved_guest().x == 0 and saved_guest().y == 5 and saved_guest().meal_dish == meal, "A failed rescue save retains the valid accepted guest and unfinished meal behind Retry")
	expect(not app._editor_command({"type":"editor_move","id":guest_id,"x":0,"y":6}).ok and same(pending,app.session.save_data()), "Pending rescue persistence blocks further edits without duplicating a visit or sale")
	await capture("15-rescue-save-retry")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(obstacle_path))
	await tap(app.recovery_retry.get_global_rect().get_center())
	expect(not app.save_blocked and same(pending,app.store.load_session()), "Native Retry writes the exact pending rescue once storage recovers")
	app.audio.set_muted(true)
	app.store = working_store
	working_store = null
	app.save_now()
	# Directly create a free, disconnected seat; the subsequent drop is actual
	# viewport input and deliberately does not require a walking route.
	app._editor_command({"type":"editor_place","inventory_id":"stool-plain","x":0,"y":6})
	app._editor_command({"type":"editor_layer","layer":"people"})
	app._editor_command({"type":"editor_select","id":guest_id})
	point = sprite_point(guest_id)
	destination = point + app.world.cell_base(0,6)-app.world.cell_base(float(saved_guest().x),float(saved_guest().y))
	await touch(point,true)
	await drag(point,destination)
	await capture("10-rescue-to-free-seat-preview")
	await touch(destination,false)
	expect(saved_guest().phase == "eating" and saved_guest().x == 0 and saved_guest().y == 6 and saved_guest().meal_dish == meal,"An actual People drag reseats onto a disconnected free stool with the same meal")
	expect(persisted(),"The direct customer rescue is immediately persistent")
	await capture("11-rescued-and-reseated")
	var reopened := Session.new()
	expect(reopened.restore(app.store.load_session(app._valid_saved_session)) and same(reopened.snapshot(),app.session.snapshot()),"Save/reopen retains the rescued visit and meal without paying a sale")
	reopened = null
	await load_scenario(true)
	app._editor_command({"type":"editor_place","inventory_id":"crate-wood","x":3,"y":4})
	app._editor_command({"type":"editor_place","inventory_id":"crate-wood","x":3,"y":6})
	app._editor_command({"type":"set_mode","mode":"live"})
	app.advance_time(1.2)
	expect(saved_guest().navigation_mode == "wander" and app.world.customer_feedback(app.session.snapshot().customers[0]).get("object") == "bubble-panic","An inaccessible guest visibly panics and wanders")
	await capture("12-trapped-panic")
	app._editor_command({"type":"set_mode","mode":"edit"})
	app._editor_command({"type":"editor_layer","layer":"people"})
	guest_id = saved_guest().id
	app._editor_command({"type":"editor_select","id":guest_id})
	point = sprite_point(guest_id)
	destination = point+app.world.cell_base(3,7)-app.world.cell_base(float(saved_guest().x),float(saved_guest().y))
	before = app.session.save_data()
	await touch(point,true)
	await drag(point,destination)
	await touch(destination,false)
	expect(saved_guest().phase == "waiting" and saved_guest().seat_id == "seat" and saved_guest().id == guest_id,"A trapped guest can be dragged across an impassable barrier directly onto a free seat")
	expect(saved_guest().preferred_recipe_id == before.state.customers[0].preferred_recipe_id and saved_guest().preference_elapsed == before.state.customers[0].preference_elapsed,"Rescue retains the existing visit's preference")
	await capture("13-rescued-across-barrier")
	app._editor_command({"type":"editor_remove","id":"seat"})
	app._editor_command({"type":"editor_layer","layer":"people"})
	app._editor_command({"type":"editor_select","id":guest_id})
	app.show_editor_gallery = true
	app._refresh()
	await capture("14-shared-rescue-gallery")
	await finish()

func finish() -> void:
	if not output.is_empty():
		var file := FileAccess.open(output.path_join("verification.json"),FileAccess.WRITE)
		file.store_string(JSON.stringify({"checks":checks,"failures":failures,"display":DisplayServer.get_name(),"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"viewport":[root.size.x,root.size.y]},"\t"))
	# Retry restores normal production audio. Release any test playback before
	# quitting a fast headless loop, so the audio thread holds no WAV resources.
	app.audio.set_muted(true)
	for player in app.audio.get_children():
		if player is AudioStreamPlayer:
			player.stop()
			player.stream = null
	await create_timer(0.1).timeout
	app.queue_free()
	await frames(6)
	if failures.is_empty():
		print("PASS: %s native customer rescue touch checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: "+failure)
		quit(1)
