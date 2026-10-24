extends "res://tests/long_press_native_tests.gd"
## Leaving the stool changes food presentation, never meal ownership.
class SpriteProbe extends "res://scripts/restaurant_view.gd":
	var calls: Array[Dictionary] = []
	func sprite(identity: String, _base: Vector2, clip := "static", _direction := "S", _seconds := 0.0, _tile_pixels := -1.0, _tint := Color.WHITE) -> void:
		calls.append({"art_id":identity,"clip":clip})

func empty_hands(identity: String) -> bool:
	return not app.world.sprite_hits().any(func(hit): return hit.owner_id == identity and str(hit.art_id).begins_with("dish-"))

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
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
	app.set_process(false)
	app.audio.set_muted(true)
	await frames()
	app.store = Store.new("user://issue14-empty-hands")
	app.store.clear_session()
	app.show_editor_gallery = false
	await load_scenario()
	var before: Dictionary = saved_guest().duplicate(true)
	var id: String = before.id
	expect(before.phase == "eating" and app.world.customer_clip(before) == "eat-salmon", "The real seated guest initially shows the authored sushi-eating pose")
	await capture("01-seated-eating")
	# Every appearance/direction and food variant uses one empty-handed body
	# sprite off the stool. This exercises the production presentation method.
	var probe := SpriteProbe.new()
	for phase in ["standing","walking"]:
		for appearance in range(4):
			for direction in ["north","east","south","west"]:
				for recipe in ["salmon_nigiri","cucumber_maki","eel_nigiri"]:
					var customer := before.duplicate(true)
					customer.phase = phase
					customer.visual_phase = "stand" if phase == "standing" else "walk"
					customer.appearance = appearance
					customer.facing = direction
					customer.meal_dish.recipe_id = recipe
					probe.calls.clear()
					probe._customer_at(customer,Vector2.ZERO,76.0)
					expect(probe.calls.size() == 1 and not str(probe.calls[0].art_id).begins_with("dish-"), "%s %s guest %s with %s has no added sushi sprite" % [phase,direction,appearance,recipe])
	probe.free()
	app._editor_command({"type":"editor_remove","id":"seat"})
	expect(saved_guest().phase == "standing" and empty_hands(id), "Removing the stool immediately removes the held sushi and its picking silhouette")
	expect(saved_guest().meal_dish == before.meal_dish and saved_guest().meal_elapsed == before.meal_elapsed and persisted(), "Stool removal retains and saves the exact unfinished meal without showing it")
	await capture("02-stool-removed-empty-hands")
	app._editor_command({"type":"set_mode","mode":"live"})
	app.advance_time(0.1)
	expect(saved_guest().phase == "standing" and empty_hands(id) and saved_guest().meal_elapsed == before.meal_elapsed, "The standing guest stays empty-handed with paused eating after Live resumes")
	app._editor_command({"type":"set_mode","mode":"edit"})
	app._editor_command({"type":"editor_place","inventory_id":"stool-plain","x":2,"y":5,"facing":"south"})
	expect(saved_guest().phase == "eating" and app.world.customer_clip(saved_guest()) == "eat-salmon" and saved_guest().meal_dish == before.meal_dish, "Reseating restores the same visible sushi-eating pose")
	await capture("03-reseated-eating")
	var point := pickup_point(id)
	await hold(point)
	expect(app.gesture_lifted and app.world.editor_preview.source.id == id and app.world.editor_preview.source.meal_dish == before.meal_dish, "Direct pickup preserves meal state while presenting the guest as empty-handed standing")
	await capture("04-picked-up-empty-hands")
	await touch(point,false,true)
	expect(saved_guest().phase == "eating" and app.world.customer_clip(saved_guest()) == "eat-salmon" and saved_guest().meal_elapsed == before.meal_elapsed, "Canceling pickup restores the seated sushi pose without losing meal progress")
	point = pickup_point(id)
	await hold(point)
	var destination: Vector2 = point+Vector2(-app.world.cell,0)
	await drag(point,destination)
	await touch(destination,false)
	expect(saved_guest().phase == "standing" and saved_guest().x == 1 and empty_hands(id), "Dragging the guest off the stool drops an empty-handed standing guest")
	expect(saved_guest().meal_dish == before.meal_dish and saved_guest().meal_elapsed == before.meal_elapsed and persisted(), "Direct pickup/drop saves the same unfinished meal and frozen clock")
	await capture("05-dropped-empty-hands")
	app._editor_command({"type":"set_mode","mode":"live"})
	app.advance_time(0.05)
	expect(saved_guest().phase == "walking" and empty_hands(id) and saved_guest().meal_elapsed == before.meal_elapsed, "Walking back to replacement seating keeps sushi hidden and the meal paused")
	await capture("06-walking-empty-hands")
	var peer := Session.new()
	expect(peer.restore(app.session.save_data()), "An off-stool unfinished meal remains valid after reopening")
	app.session = peer
	app._refresh()
	expect(empty_hands(id), "Reopening the off-stool visit cannot restore a floating sushi attachment")
	await finish()
