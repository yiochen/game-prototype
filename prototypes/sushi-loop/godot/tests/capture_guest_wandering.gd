extends SceneTree
## Small native proof of accepted route blockage and continuous guest movement.
## Only public Session configuration, command, time, snapshot and save APIs set
## up this isolated gallery-sized restaurant; all sprites/UI are production.
const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var screens: Array = []
var timeline: Array = []

func _initialize() -> void:
	call_deferred("run")

func configuration() -> Dictionary:
	var objects: Array = [
		{"id": "chef", "kind": "chef", "art_id": "chef-lena", "x": 2, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri"},
		{"id": "belt", "kind": "belt", "x": 3, "y": 6, "facing": "south"},
		{"id": "seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"},
	]
	for x in range(7):
		if x != 3: objects.append({"id": "wall-%s" % x, "kind": "decor", "art_id": "crate-wood", "x": x, "y": 3, "facing": "south"})
	return {"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}}, "service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 2.0}, "objects": objects}

func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		push_error("Capture through tools/test_native.py with isolated data.")
		quit(1)
		return
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("An output directory is required.")
		quit(1)
		return
	var requested := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if requested.size() == 2: root.size = Vector2i(int(requested[0]), int(requested[1]))
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	app.session = Session.new_session(41, configuration())
	app.advance_time(0.6)
	app._layout() # Refit the seven-row public fixture at the fixed cell scale.
	app.session.command({"type": "set_mode", "mode": "edit"})
	var result: Dictionary = app.session.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3})
	if not result.ok:
		push_error("The genuine route-closing drop was rejected: " + JSON.stringify(result))
		quit(1)
		return
	app.session.command({"type": "editor_toggle_tray"})
	app._refresh()
	await capture("01-blocking-edit-accepted", {"command": {"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3}, "result": result})
	app.session.command({"type": "set_mode", "mode": "live"})
	for step in range(80):
		app.advance_time(0.05)
		timeline.append({"elapsed": app.session.snapshot().elapsed, "guests": app.session.snapshot().customers})
		if step == 19: await capture("02-guest-wandering", {})
		if step == 69: await capture("03-guest-still-wandering", {})
	app.session.command({"type": "set_mode", "mode": "edit"})
	var reopened: Dictionary = app.session.command({"type": "editor_remove", "id": result.id})
	if not reopened.ok:
		push_error("The genuine route-opening return was rejected.")
		quit(1)
		return
	app.session.command({"type": "set_mode", "mode": "live"})
	for step in range(160):
		app.advance_time(0.05)
		var guests: Array = app.session.snapshot().customers
		if not guests.is_empty() and float(guests[0].y) > 3.0:
			await capture("04-seat-route-restored", {"command": {"type": "editor_remove", "id": result.id}, "result": reopened})
			break
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": screens, "wander_timeline": timeline, "fixture": configuration(), "source": "Actual production main.tscn and RestaurantView; public Session APIs only"}, "  ") + "\n")
	print("Captured %s native guest-wandering states" % screens.size())
	app.queue_free()
	await frames()
	await create_timer(0.1).timeout
	quit(0 if screens.size() == 4 else 1)

func frames() -> void:
	for index in range(3): await process_frame

func capture(name: String, trigger: Dictionary) -> void:
	await frames()
	await RenderingServer.frame_post_draw
	var pixels := root.get_texture().get_image()
	if pixels.save_png(destination.path_join(name + ".png")) != OK: push_error("Cannot save " + name)
	screens.append({"name": name, "pixels": [pixels.get_width(), pixels.get_height()], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "trigger": trigger, "snapshot": app.session.snapshot()})
