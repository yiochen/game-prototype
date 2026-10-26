extends SceneTree
const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var manifest: Array = []
func configuration() -> Dictionary:
	return {"objects": [
		{"id": "chef", "kind": "chef", "x": 4, "y": 7, "facing": "east", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"},
		{"id": "belt", "kind": "belt", "x": 5, "y": 7, "facing": "south"},
		{"id": "seat", "kind": "seat", "x": 5, "y": 6, "facing": "south"}],
		"recipes": {"salmon_nigiri": {"preparation_seconds": 0.2}},
		"service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "eating_seconds": 0.5, "sitting_seconds": 0.1, "standing_seconds": 0.1, "loading_seconds": 0.1},
		"customers": {"fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0}}
func guest() -> Dictionary:
	var guests: Array = app.session.save_data().state.customers
	return guests[0] if not guests.is_empty() else {}
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty(): quit(1); return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	# Select representative real visits through the public saved simulation.
	var selected := {}
	for seed_value in range(1, 40):
		var probe = Session.new_session(seed_value, configuration())
		probe.advance(0.1)
		var lane := int(probe.save_data().state.customers[0].door_lane)
		if not selected.has(lane): selected[lane] = seed_value
		if selected.size() == 2: break
	for lane in [4, 5]:
		app.session = Session.new_session(selected[lane], configuration())
		app.advance_time(0.8)
		if not is_equal_approx(float(guest().x), float(lane)) or float(guest().y) <= 3.0: push_error("Expected a real guest on its selected front approach.")
		await capture("entry-front-%s" % lane)
		for step in range(500):
			app.advance_time(0.05)
			if not guest().is_empty() and guest().phase == "leaving" and not guest().has("door_motion") and float(guest().y) > 3.1 and float(guest().y) < 3.9: break
		await capture("exit-front-entry-%s-goal-%s" % [lane, guest().get("door_lane", -1)])
	app.session = Session.new_session(7, configuration())
	app.session.command({"type": "set_mode", "mode": "edit"})
	var left: Dictionary = app.session.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 4, "y": 3})
	var right: Dictionary = app.session.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 5, "y": 3})
	if not left.ok or not right.ok: push_error("Both front tiles must accept furniture.")
	app.session.command({"type": "set_mode", "mode": "live"})
	app.advance_time(5.0)
	if not app.session.snapshot().customers.is_empty(): push_error("A blocked entrance must not spawn guests in furniture.")
	await capture("both-front-tiles-blocked")
	app.session.command({"type": "set_mode", "mode": "edit"})
	app.session.command({"type": "editor_remove", "id": right.id})
	app.session.command({"type": "set_mode", "mode": "live"})
	app.advance_time(0.8)
	if guest().is_empty() or guest().x != 5: push_error("Reopening the right side must admit through the right front tile.")
	await capture("left-blocked-right-front-open")
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest,"\t"))
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)
func capture(label: String) -> void:
	app._refresh()
	for frame in range(4): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(label + ".png"))
	manifest.append({"name": label, "snapshot": app.session.snapshot()})
