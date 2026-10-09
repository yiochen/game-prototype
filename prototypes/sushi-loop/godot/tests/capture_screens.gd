extends SceneTree
## Native screenshots of actual simulation states. Always use the isolated runner.

var game: Control
var output_dir := "/tmp/sushi-loop-captures"
var captures: Array = []
var failures := 0
var requested_size := Vector2i(720, 1280)

func _init() -> void:
	call_deferred("capture")

func _fail(message: String) -> void:
	failures += 1
	push_error(message)

func _advance_service(seconds: float) -> void:
	var remaining := seconds
	while remaining > 0.0001:
		var step := minf(remaining, 0.05)
		game.backgrounded = false
		game._process(step)
		remaining -= step

func _capture(name: String, note: String = "") -> void:
	game.queue_redraw()
	if is_instance_valid(game.dive):
		game.dive.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var canvas := Rect2(Vector2.ZERO, game.size)
	for button in game.buttons:
		if not canvas.encloses(button.rect):
			_fail("Off-screen touch target in %s: %s" % [name, button.action])
	var picture := root.get_texture().get_image()
	var path := output_dir.path_join("sushi-" + name + ".png")
	if picture == null or picture.is_empty():
		_fail("Empty viewport image: " + name)
		return
	if picture.save_png(path) != OK:
		_fail("Could not write screenshot: " + path)
		return
	var entry := {
		"name": name, "path": path, "note": note,
		"width": picture.get_width(), "height": picture.get_height(),
		"canvas_width": game.size.x, "canvas_height": game.size.y,
		"screen": str(game.screen), "modal": str(game.modal),
		"restaurant_time": float(game.model.data.time),
		"customers": game.model.data.customers.size(),
		"sales": int(game.model.data.stats.sales),
	}
	if is_instance_valid(game.dive):
		entry["route"] = game.dive.route
		entry["phase"] = game.dive.phase
		entry["elapsed"] = game.dive.elapsed
		entry["resistance"] = game.dive.resistance
		entry["hull"] = game.dive.hull
		entry["objects"] = game.dive.objects.size()
	captures.append(entry)

func _first_chef() -> Dictionary:
	for object in game.model.data.objects:
		if object.kind == "chef":
			return object
	return {}

func capture() -> void:
	var arguments := OS.get_cmdline_user_args()
	if arguments.size() < 2 or not str(arguments[1]).begins_with("SushiLoopIntegrationTests-") or not OS.get_user_data_dir().ends_with(str(arguments[1])):
		push_error("Run screenshots through python3 tools/test_app.py --capture for save isolation.")
		quit(2)
		return
	var report := FileAccess.open(str(arguments[0]), FileAccess.WRITE)
	report.store_string(JSON.stringify({"user_directory": OS.get_user_data_dir()}))
	report.close()
	if arguments.size() > 2:
		output_dir = str(arguments[2])
	if arguments.size() > 4:
		requested_size = Vector2i(int(arguments[3]), int(arguments[4]))
	if DirAccess.make_dir_recursive_absolute(output_dir) != OK:
		_fail("Could not create screenshot directory: " + output_dir)
		quit(1)
		return
	root.size = requested_size
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_process(false)
	await process_frame
	await process_frame
	if not game.size.is_equal_approx(root.get_visible_rect().size):
		_fail("Root control must fill the actual viewport before capturing")
	game.backgrounded = false
	game.meta.music = false
	game.meta.sound = false
	game.audio.configure(false, false)
	_advance_service(6.0)
	if game.screen != "title":
		_fail("Loading did not reach the title screen")
		quit(1)
		return
	await _capture("title", "Fresh install after real asset loading")

	# This is the real starter layout and visitor population after twenty
	# seconds, rather than a still-life composed by relocating customers.
	game._finish_intro()
	_advance_service(20.0)
	if int(game.model.data.stats.sales) == 0 or game.model.data.customers.is_empty():
		_fail("Live restaurant capture must contain actual customers and sales")
	await _capture("restaurant", "Unmodified starter restaurant after 20 simulated seconds")
	_advance_service(2.0)
	await _capture("restaurant-activity", "Unmodified starter after 22 simulated seconds, separate from the 20-second baseline")
	var live_state: Dictionary = game.model.serialize()
	var chef := _first_chef()
	if chef.is_empty():
		_fail("Starter restaurant has no chef")
		quit(1)
		return
	game.selected = int(chef.id)
	game.modal = "chef"
	await _capture("chef", "Chef management over the live restaurant")
	game._action("recipes")
	await _capture("recipes", "Starter recipe picker: current recipe and undiscovered silhouettes")
	game.model.data.recipes = ["cucumber", "salmon", "shrimp", "eel"]
	game.meta.new_recipes = ["salmon", "shrimp", "eel"]
	chef.level = 3
	game.selected_recipe = "shrimp"
	await _capture("recipes-discovered", "Level 3 chef: current, selectable, NEW, and higher-tier discovered recipes")
	game._action("inspect_recipe", "eel")
	await _capture("recipes-locked", "Discovered Copper recipe inspected below required chef level")
	game.modal = ""
	game.model.restore(live_state)
	game.meta.new_recipes = []
	game.selected = -1
	game.editing = true
	for edit_layer in [0, 1, 2]:
		game.layer = edit_layer
		await _capture("edit-" + ["people", "layout", "floor"][edit_layer], "Paused restaurant edit layer")
	game.layer = 1
	for object in game.model.data.objects:
		if object.kind == "belt":
			game.selected = int(object.id)
			break
	await _capture("edit-selected", "Selected belt with its local edit controls")
	game.editing = false
	game.selected = -1

	for screen_name in ["shop", "workshop", "prep"]:
		game._change(screen_name)
		await _capture(screen_name)
	game._change("restaurant")
	for modal_name in ["help", "settings", "credits", "expand"]:
		game.modal = modal_name
		await _capture(modal_name)
	game.modal = ""

	# Each route is played forward through its real encounter schedule. The
	# fixture steers but does not replace scenery, props or creature artwork.
	for route_index in range(3):
		await _capture_route(route_index)

	game.result = {"species":"salmon", "outcome":"complete", "pickups":28, "completion_bonus":20, "repeat_bonus":0, "total":48, "caught":true}
	for screen_name in ["cutscene", "reveal"]:
		game._change(screen_name)
		game.scene_time = 1.5
		await _capture(screen_name)
	for outcome in ["complete", "early", "failed"]:
		game.result.outcome = outcome
		game.result.completion_bonus = 20 if outcome == "complete" else 0
		game.result.total = 48 if outcome == "complete" else 28
		game._change("results")
		await _capture("results" if outcome == "complete" else "results-" + outcome)

	var manifest := FileAccess.open(output_dir.path_join("manifest.json"), FileAccess.WRITE)
	manifest.store_string(JSON.stringify({"screenshots": captures, "failures": failures, "requested_width": requested_size.x, "requested_height": requested_size.y}, "\t"))
	manifest.close()
	print("Captured %d application screens; %d failures; %s" % [captures.size(), failures, output_dir])
	quit(1 if failures > 0 or captures.size() < 25 else 0)

func _capture_route(route_index: int) -> void:
	game.meta.charge = 1.0
	game.meta.dives = 1
	game.meta.upgrades = {"hull": 3, "harpoon": 1, "collector": 2}
	game.selected_route = route_index
	game._launch()
	if not is_instance_valid(game.dive):
		_fail("Could not launch route " + str(route_index + 1))
		return
	var voyage: Control = game.dive
	voyage.set_process(false)
	voyage.paused = false
	voyage.lesson = ""
	var travel_capture_time: float = float(voyage.route_data.get("portal_at", 18.0)) + 2.0
	var captured_travel := false
	var captured_aim := false
	var pursuit_time := 0.0
	for step_index in range(2600):
		if not is_instance_valid(voyage) or voyage.ended:
			break
		voyage.paused = false
		voyage.ui_clock += 0.05
		if voyage.phase == "travel":
			# A legal, steady steering line leaves the center available to view
			# the salvage trail, current and passage entrance.
			voyage.ship_x = 360.0
		elif voyage.phase in ["aim", "pursuit"]:
			voyage.ship_x = voyage.creature_x
			if voyage.phase == "aim":
				if not captured_aim:
					voyage.notice_left = 0.0
					await _capture("route-%d-aim" % (route_index + 1), "Real creature encounter and contextual harpoon control")
					captured_aim = true
				voyage._fire()
		voyage._tick(0.05)
		voyage._tick_particles(0.05)
		if not captured_travel and voyage.elapsed >= travel_capture_time:
			voyage.notice_left = 0.0
			await _capture("route-%d-travel" % (route_index + 1), "Mid-route live schedule including the bonus-passage entrance")
			captured_travel = true
		if voyage.phase == "pursuit":
			pursuit_time += 0.05
			if pursuit_time >= 4.0:
				voyage.notice_left = 0.0
				await _capture("route-%d-pursuit" % (route_index + 1), "Actual harpoon hit followed by four seconds of capture progress")
				break
	if not captured_travel or not captured_aim or pursuit_time < 4.0:
		_fail("Route %d did not reach all representative states" % (route_index + 1))
	if is_instance_valid(game.dive):
		game.dive.free()
		game.dive = null
	game._change("restaurant")
