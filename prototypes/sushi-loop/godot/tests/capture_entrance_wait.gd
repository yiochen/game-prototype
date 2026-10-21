extends SceneTree
## Native evidence uses the actual mobile scene/approved sprite renderer. Public
## Session configuration, command and advance APIs are the only fixture seam.
const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var screens: Array = []
var timeline: Array = []
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("run")

func configuration() -> Dictionary:
	return {
		"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}},
		"service": {"step_seconds": 0.05, "first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 2.0},
		"objects": [
			{"id": "chef", "kind": "chef", "art_id": "chef-lena", "x": 2, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri"},
			{"id": "seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"},
		],
	}

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
	var config := configuration()
	app.session = Session.new_session(41, config)
	app.advance_time(1.3)
	app._layout()
	var first: Dictionary = app.session.snapshot().customers[0]
	if first.phase != "entrance_wait" or app.world.customer_feedback(first).get("object") != "bubble-puzzled": failures.append("Expected the production puzzled wait.")
	await capture("01-puzzled-entrance", {"reason": "The only seat has no connected belt."})
	app.advance_time(2.5)
	await capture("02-still-at-entrance", {"same_guest": first.id, "standing_seconds": 3.7})
	var departure: Array = app.advance_time(0.3)
	if not app.session.snapshot().customers.is_empty() or not departure.any(func(event): return event.type == "departed" and event.reason == "no_seat"): failures.append("Expected one no-seat departure at four seconds.")
	await capture("03-no-seat-guest-left", {"events": departure})
	app.session = Session.new_session(41, config)
	app.advance_time(0.7)
	app.session.command({"type": "set_mode", "mode": "edit"})
	var addition: Dictionary = app.session.command({"type": "editor_place", "inventory_id": "belt-tile", "x": 3, "y": 6})
	app.session.command({"type": "set_mode", "mode": "live"})
	app.advance_time(0.75)
	var admitted: Dictionary = app.session.snapshot().customers[0]
	if not addition.ok or admitted.phase != "walking" or admitted.seat_id != "seat" or app.world.customer_feedback(admitted).get("object") == "bubble-puzzled": failures.append("Expected the same visitor to walk toward the newly usable seat.")
	await capture("04-seat-opens-same-guest-enters", {"command": {"type": "editor_place", "inventory_id": "belt-tile", "x": 3, "y": 6}, "result": addition})
	var trapped := configuration()
	trapped.objects.append({"id": "belt", "kind": "belt", "x": 3, "y": 6, "facing": "south"})
	for x in range(7):
		if x != 3: trapped.objects.append({"id": "wall-%s" % x, "kind": "decor", "art_id": "crate-wood", "x": x, "y": 3, "facing": "south"})
	app.session = Session.new_session(41, trapped)
	app.advance_time(0.6)
	app.session.command({"type": "set_mode", "mode": "edit"})
	var blockage: Dictionary = app.session.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3})
	app.session.command({"type": "set_mode", "mode": "live"})
	app.advance_time(1.3)
	var scared: Dictionary = app.session.snapshot().customers[0]
	if not blockage.ok or scared.navigation_mode != "wander" or app.world.customer_feedback(scared).get("object") != "bubble-panic": failures.append("Expected a genuine trapped guest with the production scared reaction.")
	await capture("05-trapped-guest-scared", {"command": {"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3}, "result": blockage})
	app.advance_time(3.0)
	await capture("06-trapped-guest-still-wandering", {"same_guest": scared.id})
	app.queue_free()
	await frames()
	app = APP.instantiate()
	app.show_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await frames()
	app.advance_time(1.5)
	await capture("07-shared-reactions-gallery", {"purpose": "All seven customer reactions, inactive furniture and service samples in the real native mobile gallery."})
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": screens, "fixture": config, "source": "Actual production main.tscn and RestaurantView; public Session APIs only", "failures": failures}, "  ") + "\n")
	for failure in failures: printerr("FAIL: " + failure)
	print("Captured %s native entrance and scared-guest states" % screens.size())
	app.queue_free()
	await frames()
	await create_timer(0.1).timeout
	quit(0 if screens.size() == 7 and failures.is_empty() else 1)

func frames() -> void:
	for index in range(3): await process_frame

func capture(name: String, trigger: Dictionary) -> void:
	app._refresh()
	await frames()
	await RenderingServer.frame_post_draw
	var pixels := root.get_texture().get_image()
	if pixels.save_png(destination.path_join(name + ".png")) != OK: failures.append("Cannot save " + name)
	var feedback: Array = []
	for guest in app.session.snapshot().customers:
		feedback.append({"id": guest.id, "body_clip": app.world.customer_clip(guest), "bubble": app.world.customer_feedback(guest)})
	screens.append({"name": name, "pixels": [pixels.get_width(), pixels.get_height()], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "trigger": trigger, "snapshot": app.session.snapshot(), "feedback": feedback})
