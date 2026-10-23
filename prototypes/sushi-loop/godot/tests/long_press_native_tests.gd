extends "res://tests/customer_rescue_native_tests.gd"
## Amendment: holds use actual sprite ownership; taps retain object actions.

func expect(value: bool, message: String) -> bool:
	if not value: printerr("CHECK FAILED: " + message)
	return super.expect(value, message)

func pickup_point(identity: String) -> Vector2:
	for hit in app.world.sprite_hits():
		if hit.owner_id != identity: continue
		for y in range(2, 9):
			for x in range(2, 9):
				var at: Vector2 = hit.rect.position + hit.rect.size * Vector2(x, y) * 0.1
				if app.world.object_at(at, true).get("id", "") == identity and app._floor_drop(at): return at
	return Vector2(-1, -1)

func hold(at: Vector2) -> void:
	await touch(at, true)
	app._advance_long_press(app.LONG_PRESS_SECONDS)
	await frames()

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		quit(1)
		return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size() == 2: root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	app = APP.instantiate()
	app.simulation_enabled = false
	app.show_editor_gallery = true
	root.add_child(app)
	app.set_process(false) # Deterministic threshold checks; real-frame timing below.
	app.audio.set_muted(true)
	await frames()
	app.store = Store.new("user://issue14-long-press")
	app.store.clear_session()
	app.show_editor_gallery = false
	await load_scenario()
	var id: String = saved_guest().id
	var point := pickup_point(id)
	if not expect(point.x >= 0, "The seated guest has a reachable opaque sprite hold target"):
		await finish()
		return
	var ui = app.editor_ui
	expect(app.world.object_at(point).get("id") == "seat", "Layout tap ownership still resolves the occupied stool")
	await tap(point)
	expect(app.session.snapshot().editor.selected_id == "seat" and ui.context_bubble.visible and ui.rotate.visible and ui.remove.visible, "A short tap opens the stool Rotate/Return menu")
	point = pickup_point(id)
	expect(point.x >= 0, "The selected stool menu leaves guest pixels exposed for a hold")
	var before: Dictionary = app.session.save_data()
	await touch(point, true)
	app._advance_long_press(0.399)
	expect(not app.gesture_lifted and app.world.editor_preview.is_empty(), "A subthreshold stationary press does not pick up the stool or guest")
	await capture("01-pending-guest-hold")
	app._advance_long_press(0.0011)
	await frames()
	expect(app.gesture_lifted and app.gesture_object == id and app.session.snapshot().editor.layer == "people", "A 400ms guest hold picks up the guest directly from Layout")
	expect(not ui.context_bubble.visible and not ui.rotate.visible and not ui.remove.visible, "Object actions hide during guest pickup")
	expect(same(before.state.customers, app.session.save_data().state.customers) and same(before.state.objects, app.session.save_data().state.objects) and before.random_state == app.session.save_data().random_state, "Pickup has no position, visit, plate, clock or RNG side effects")
	expect(not app.world.sprite_hits().any(func(hit): return hit.owner_id == id), "The original guest silhouette is hidden during pickup")
	expect(app.world.sprite_hits().any(func(hit): return hit.owner_id == "seat"), "Guest pickup leaves the stool in its original place")
	await capture("02-seated-guest-picked-up")
	var destination: Vector2 = point + Vector2(-app.world.cell * 0.73, app.world.cell * 0.27)
	await drag(point, destination)
	expect(absf(float(app.world.editor_preview.get("visual_x", -99)) - 1.27) < 0.001 and absf(float(app.world.editor_preview.get("visual_y", -99)) - 5.27) < 0.001, "The lifted sprite tracks fractional finger movement without snapping its root")
	expect(app.world.editor_preview.get("valid", false), "The floor footprint validates the actual seated-guest move")
	await capture("03-continuous-guest-drag")
	await touch(destination, false)
	expect(saved_guest().id == id and saved_guest().phase == "standing" and saved_guest().x == 1 and saved_guest().y == 5 and saved_guest().seat_id == "", "A seated guest can be dropped onto nearby floor without moving the stool")
	expect(saved_guest().meal_dish == before.state.customers[0].meal_dish and saved_guest().meal_elapsed == before.state.customers[0].meal_elapsed and saved_guest().preferred_recipe_id == before.state.customers[0].preferred_recipe_id, "The direct seated pickup preserves the unfinished meal and preference")
	expect(persisted() and app.world.editor_preview.is_empty(), "Only the accepted drop is persisted, with no lifted pose in the save")
	await capture("04-guest-dropped-standing")
	point = pickup_point(id)
	before = app.session.save_data()
	await hold(point)
	destination = point + app.world.cell_base(1,6) - app.world.cell_base(float(saved_guest().x),float(saved_guest().y))
	await drag(point,destination)
	expect(not app.world.editor_preview.get("valid", true), "A guest over an occupied belt gets an invalid footprint")
	await capture("05-invalid-guest-drop")
	await touch(destination,false)
	expect(same(before,app.session.save_data()), "An invalid held guest drop preserves the prior saved state")
	point = pickup_point(id)
	await hold(point)
	await drag(point,point+Vector2(0,app.world.cell))
	await touch(point+Vector2(0,app.world.cell),false,true)
	expect(same(before,app.session.save_data()) and app.world.editor_preview.is_empty() and not app.gesture_lifted, "A canceled guest hold restores the original visible guest and saved arrangement")
	await hold(point)
	app._notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	app._notification(Node.NOTIFICATION_APPLICATION_RESUMED)
	app.backgrounded = false
	app.skip_resume_frame = false
	await touch(point,false)
	expect(same(before,app.session.save_data()) and app.pointer == -1 and not app.gesture_lifted, "Backgrounding cancels pickup without moving or consuming the guest")
	# Directly reseat the same guest; this must preserve the exact meal.
	app._editor_command({"type":"editor_move","id":id,"x":2,"y":5})
	expect(saved_guest().phase == "eating" and saved_guest().meal_elapsed == before.state.customers[0].meal_elapsed, "The picked guest can return to their free stool with the same meal")
	app._editor_command({"type":"editor_select","id":null})
	app._editor_command({"type":"editor_layer","layer":"layout"})
	# Unselected furniture pickup; occupied stool pickup uses its own bare pixels.
	point = pickup_point("seat")
	expect(point.x >= 0, "An occupied stool also exposes its own opaque hold target")
	await hold(point)
	expect(app.gesture_object == "seat" and app.gesture_lifted, "Holding bare stool pixels picks up the unselected stool")
	expect(not app.world.sprite_hits().any(func(hit): return hit.owner_id in ["seat",id]), "An occupied stool hides both source silhouettes during its carried preview")
	await capture("06-occupied-stool-picked-up")
	destination = point + Vector2(app.world.cell,0)
	await drag(point,destination)
	await touch(destination,false)
	expect(saved_guest().x == 3 and saved_guest().y == 5 and saved_guest().meal_elapsed == before.state.customers[0].meal_elapsed, "The held stool still carries its seated guest and unfinished meal")
	expect(app.session.snapshot().editor.selected_id == "seat" and ui.context_bubble.visible and ui.rotate.visible and ui.remove.visible, "A dropped object stays selected with Rotate/Return immediately available")
	expect(persisted(), "The selected stool and carried guest survive save/reopen")
	await capture("07-dropped-stool-context-menu")
	# Long-press an unselected chef, then cancel; early movement must remain pan.
	app._editor_command({"type":"editor_select","id":null})
	point = pickup_point("chef")
	before = app.session.save_data()
	await touch(point,true)
	destination = point+Vector2(-15.0/maxf(0.001,app.get_viewport_transform().get_scale().x),0)
	await drag(point,destination)
	app._advance_long_press(1.0)
	expect(app.gesture_dragged and not app.gesture_lifted and app.long_press_candidate.is_empty(), "Movement before the hold threshold owns pan and cannot turn into a late pickup")
	await touch(destination,false)
	expect(same(before.state.objects,app.session.save_data().state.objects), "Early pan does not move the touched object")
	point = pickup_point("chef")
	await hold(point)
	expect(app.gesture_lifted and app.gesture_object == "chef", "An unselected chef supports the same long-press pickup")
	await capture("08-chef-picked-up")
	await touch(point,false,true)
	expect(ui.context_bubble.visible and app.session.snapshot().editor.selected_id == "chef", "Canceled object pickup restores its selection menu")
	point = pickup_point("chef")
	await touch(point,true)
	app._notification(Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	expect(app.pointer == -1 and app.world.state.objects.all(func(object): return not str(object.get("id", "")).is_empty()), "Canceling a pending object hold never clears the rendered object's dictionary")
	await touch(point,false)
	# Real foreground frames invoke the timer; Live never admits edit gestures.
	app._editor_command({"type":"editor_select","id":null})
	point = pickup_point("chef")
	app.set_process(true)
	await touch(point,true)
	await create_timer(0.45).timeout
	app.set_process(false)
	expect(app.gesture_lifted and app.gesture_object == "chef", "The production frame loop triggers stationary pickup without a drag event")
	await touch(point,false,true)
	app._editor_command({"type":"set_mode","mode":"live"})
	await touch(point,true)
	app._advance_long_press(1.0)
	expect(not app.gesture_lifted and app.long_press_candidate.is_empty(), "Live ignores long-press editing")
	await touch(point,false)
	# Loaded tiles retain their exact food and transfer clock during the lift.
	app.session = Session.new_session(1)
	app.session.command({"type":"set_entrance_open","open":false})
	app.session.advance(4.55)
	app.session.command({"type":"set_mode","mode":"edit"})
	app._refresh()
	app._layout()
	await frames()
	var loaded := {}
	for tile in app.session.save_data().state.objects:
		if tile.kind == "belt" and tile.dish != null and float(tile.travel_elapsed) > 0 and pickup_point(tile.id).x >= 0:
			loaded = tile.duplicate(true)
			break
	if expect(not loaded.is_empty(), "A partially traveled loaded belt has exposed hold pixels"):
		point = pickup_point(loaded.id)
		await hold(point)
		expect(app.gesture_lifted and app.gesture_object == loaded.id and app.world.editor_preview.source.dish == loaded.dish, "An unselected loaded belt picks up with its exact owned dish")
		expect(not ui.context_bubble.visible and not ui.path_targets.any(func(button): return button.visible), "Pickup hides conveyor controls and neighboring path targets")
		destination = point + app.world.cell_base(0,6) - app.world.cell_base(float(loaded.x),float(loaded.y))
		await drag(point,destination)
		await capture("11-loaded-belt-picked-up")
		await touch(destination,false)
		var dropped: Dictionary = app.session.save_data().state.objects.filter(func(tile): return tile.id == loaded.id)[0]
		expect(dropped.x == 0 and dropped.y == 6 and dropped.dish == loaded.dish and dropped.travel_elapsed == loaded.travel_elapsed, "The held belt drops with the same food and unfinished transfer clock")
		expect(app.session.snapshot().editor.selected_id == loaded.id and ui.context_bubble.visible and ui.rotate.visible and ui.remove.visible, "A dropped belt retains selection and its Rotate/Return menu")
		await capture("12-dropped-belt-context-menu")
	app._editor_command({"type":"editor_place","inventory_id":"plant-angular","x":0,"y":5})
	var plant: Dictionary = app._selected_object()
	app._editor_command({"type":"editor_select","id":null})
	point = pickup_point(plant.id)
	await hold(point)
	expect(app.gesture_lifted and app.gesture_object == plant.id, "An unselected decorative object supports stationary hold pickup")
	await capture("13-plant-picked-up")
	await touch(point,false,true)
	# A nontrapped walking guest can be picked up from Floor, with no prior selection.
	await load_scenario(true)
	id = saved_guest().id
	expect(saved_guest().phase == "walking" and saved_guest().navigation_mode == "goal", "The walking pickup fixture has a valid route and is not trapped")
	app._editor_command({"type":"editor_layer","layer":"floor"})
	point = pickup_point(id)
	await hold(point)
	expect(app.gesture_lifted and app.gesture_object == id, "A normal walking guest can be held from the Floor layer")
	await capture("09-ordinary-walking-guest-picked-up")
	await touch(point,false,true)
	# Reduced motion retains a static lift and exact pointer tracking.
	app.world.reduced_motion = true
	point = pickup_point(id)
	await hold(point)
	expect(app.gesture_lifted and float(app.world.editor_preview.get("lift_cells", 0)) > 0, "Reduced motion retains a clear static pickup pose")
	app.show_editor_gallery = true
	app._refresh()
	await capture("10-shared-reduced-motion-pickup")
	await touch(point,false,true)
	await finish()
