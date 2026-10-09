extends SceneTree

const Main = preload("res://scripts/main.gd")
const Save = preload("res://scripts/save_store.gd")
var checks := 0
var failures := 0
var requested_size := Vector2i(720, 1280)

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(message)

func fresh_app() -> Control:
	var app = Main.new()
	root.add_child(app)
	app.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	app.set_process(false)
	app.meta.music = false
	app.meta.sound = false
	app.audio.configure(false, false)
	return app

func run() -> void:
	var arguments := OS.get_cmdline_user_args()
	# Never run destructive save fixtures against a user's real game identity.
	if arguments.size() < 2 or not str(arguments[1]).begins_with("SushiLoopIntegrationTests-") or not OS.get_user_data_dir().ends_with(str(arguments[1])):
		push_error("Run app tests through python3 tools/test_app.py for save isolation.")
		quit(2)
		return
	var report := FileAccess.open(str(arguments[0]), FileAccess.WRITE)
	report.store_string(JSON.stringify({"user_directory": OS.get_user_data_dir()}))
	report.close()
	if arguments.size() > 4:
		requested_size = Vector2i(int(arguments[3]), int(arguments[4]))
	root.size = requested_size
	await process_frame
	check(Save.read_save().is_empty(), "Isolated project must begin without saved progress")
	var app = fresh_app()
	await process_frame
	check(app.screen == "loading", "App starts on loading screen")
	for i in range(60):
		app._process(0.1)
	check(app.screen == "title" and app.textures.size() >= 15, "Loading completes after assets are ready")
	app._action("play")
	check(app.screen == "intro", "First play opens the opening cutscene")
	app._finish_intro()
	check(app.screen == "restaurant" and app.meta.intro_seen, "Intro finishes in the persistent restaurant")
	_test_restaurant_input_and_modals(app)
	await _test_responsive_touch_targets(app)
	var charge: float = app.meta.charge
	app._action("dock")
	check(app.screen == "prep" and float(app.meta.charge) == charge, "Opening the dock does not consume charge")
	app._action("restaurant")
	check(float(app.meta.charge) == charge, "Leaving preparation preserves readiness")
	app._action("workshop")
	check(app.screen == "workshop", "Workshop is reachable from restaurant")
	app.meta.salvage = 200
	app._action("equipment", "hull")
	check(int(app.meta.upgrades.hull) == 1 and int(app.meta.salvage) == 160, "Equipment buys exactly one level at displayed cost")
	app._action("restaurant")
	check(app.screen == "restaurant" and app.pan == Vector2.ZERO, "Workshop returns centered to restaurant")
	app.meta.charge = 0.3
	app._process(1.0)
	check(float(app.meta.charge) > 0.3, "Service replenishes the battery")
	app.meta.charge = 1.0
	app._action("dock")
	app._launch()
	var dive = app.dive
	dive.set_process(false)
	check(app.screen == "dive" and is_instance_valid(dive) and float(app.meta.charge) == 0.0, "Start consumes charge and opens expedition")
	app._process(5.0)
	check(float(app.meta.charge) == 0.0, "The ship does not charge during a dive")
	dive.suspend()
	var time_before: float = dive.elapsed
	var money_before: float = app.model.data.coins
	for i in range(1500):
		app._process(0.1)
	check(float(app.meta.charge) == 0.0 and dive.elapsed == time_before, "Pause freezes dive and battery while restaurant continues")
	check(float(app.meta.pending_coins) > 0.0 and float(app.model.data.coins) == money_before, "Restaurant income is pending during expedition")
	var income_before: float = app.meta.pending_coins
	app._offline(180.0)
	check(float(app.meta.pending_coins) > income_before and float(app.model.data.coins) == money_before, "Offline dive income stays pending without double credit")
	check(float(app.meta.charge) == 0.0, "Offline dive never recharges readiness")
	app._save()
	var suspended: Dictionary = Save.read_save()
	check(not suspended.get("dive", {}).is_empty() and suspended.dive.hull == dive.hull, "Suspended dive is saved with hull and encounter state")
	var bank_before: int = int(app.meta.salvage)
	var pending_before: float = float(app.meta.pending_coins)
	dive.caught = true
	dive.pickups = 17
	dive._finish("complete")
	check(app.screen == "cutscene" and "salmon" in app.model.data.recipes, "Recipe is earned before the catch cutscene starts")
	check(int(app.meta.salvage) == bank_before + 37, "Catch receipt credits pickup plus completion bonus")
	check(float(app.meta.pending_coins) == 0.0 and is_equal_approx(float(app.model.data.coins), money_before + pending_before), "Return credits all pending service income exactly once")
	var bank_after: int = int(app.meta.salvage)
	dive._finish("complete")
	check(int(app.meta.salvage) == bank_after, "Repeated finished call cannot duplicate rewards")
	var persisted: Dictionary = Save.read_save()
	check("salmon" in persisted.restaurant.recipes and int(persisted.meta.salvage) == bank_after and persisted.dive.is_empty(), "Award persists atomically before celebration")
	app.free()
	var reopened = fresh_app()
	check(int(reopened.meta.salvage) == bank_after and not reopened.result.is_empty(), "Reopen restores pending result without re-awarding")
	reopened._action("play")
	check(reopened.screen == "results" and int(reopened.meta.salvage) == bank_after, "Reopen result continuation retains exact reward balance")
	reopened._action("results_home")
	check(reopened.result.is_empty() and reopened.screen == "restaurant", "Receipt continuation clears the pending result")
	var coins_before: float = reopened.model.data.coins
	var probe = reopened.Restaurant.new()
	probe.restore(reopened.model.serialize())
	var expected: int = probe.offline_income(180.0)
	reopened._offline(180.0)
	check(is_equal_approx(float(reopened.model.data.coins), coins_before + expected), "Ordinary offline income is credited once")
	reopened.free()

	# Write twice to exercise atomic replacement and last-good backup recovery.
	var a := {"version": 1, "restaurant": {"marker": 1}}
	var b := {"version": 1, "restaurant": {"marker": 2}}
	check(Save.write_save(a) and Save.write_save(b), "Atomic save writes must succeed")
	check(Save.read_save().restaurant.marker == 2, "Most recent valid save wins")
	var corrupt := FileAccess.open(Save.PATH, FileAccess.WRITE)
	corrupt.store_string("{\"incomplete\":true}")
	corrupt.close()
	check(Save.read_save().restaurant.marker == 1, "Corrupt primary recovers the previous complete save")
	print("App integration: %d checks, %d failures; window %dx%d" % [checks, failures, requested_size.x, requested_size.y])
	quit(1 if failures or checks < 50 else 0)


func _test_restaurant_input_and_modals(app: Control) -> void:
	var saved_layout: Dictionary = app.model.serialize()
	var saved_meta: Dictionary = app.meta.duplicate(true)
	var chef: Dictionary = {}
	for object in app.model.data.objects:
		if object.kind == "chef":
			chef = object
			break
	check(not chef.is_empty(), "Starter kitchen exposes a chef for touch selection")
	if chef.is_empty():
		return
	app.pan = Vector2(12, -8)
	var point: Vector2 = app._cell_rect(int(chef.x), int(chef.y)).get_center()
	check(app._cell(point) == Vector2i(int(chef.x), int(chef.y)), "Rendered grid coordinates map back to the correct cell after panning")
	app.buttons.clear()
	app._pointer_down(point)
	app._pointer_up(point)
	check(app.modal == "chef" and int(app.selected) == int(chef.id), "Tapping the chef cell opens that chef's management popup")
	var recipe_before := str(chef.recipe)
	var time_before := float(app.model.data.time)
	app._action("recipes")
	check(app.modal == "recipes" and app.selected_recipe == recipe_before, "Recipe picker starts with current assignment selected")
	app._process(0.1)
	check(float(app.model.data.time) > time_before and str(chef.recipe) == recipe_before, "Browsing recipes leaves service running and assignment intact")
	app.model.data.recipes.append("eel")
	app.meta.new_recipes = ["eel"]
	var progress_before := float(chef.progress)
	var held_before := str(chef.dish)
	app._action("inspect_recipe", "eel")
	check(app.selected_recipe == "eel" and not app.meta.new_recipes.has("eel"), "Inspecting a higher-tier recipe clears its NEW marker")
	check(str(chef.recipe) == recipe_before and float(chef.progress) == progress_before and str(chef.dish) == held_before, "Inspection preserves current preparation and held dish")
	app._action("prepare")
	check(app.modal == "recipes" and str(chef.recipe) == recipe_before, "Ineligible recipe cannot be assigned through the action handler")
	app._back()
	check(app.modal.is_empty() and str(chef.recipe) == recipe_before, "Back closes recipe picker without changing the kitchen")
	app._action("edit")
	var paused_time := float(app.model.data.time)
	app._process(0.1)
	check(float(app.model.data.time) == paused_time, "Editing pauses customers, chefs, and conveyor simulation")
	app._action("live")
	app._process(0.1)
	check(float(app.model.data.time) > paused_time, "Live control resumes the same kitchen simulation")
	app.buttons.clear()
	app.modal = ""
	app._pointer_down(point)
	var canceled := InputEventScreenTouch.new()
	canceled.index = 0
	canceled.position = point
	canceled.canceled = true
	app._input(canceled)
	app._pointer_up(point)
	check(app.modal.is_empty() and not app.moving, "Canceled touch cannot open a popup on release")
	app.model.restore(saved_layout)
	app.meta = saved_meta
	app.pan = Vector2.ZERO
	app.selected = -1
	app.modal = ""
	app.editing = false


func _paint(app: Control) -> void:
	app.queue_redraw()
	await process_frame
	await process_frame


func _button_rect(app: Control, action: String, data: Variant = null) -> Rect2:
	for button in app.buttons:
		if str(button.action) == action and (data == null or button.data == data):
			return button.rect
	return Rect2()


func _targets_fit(app: Control) -> bool:
	var canvas := Rect2(Vector2.ZERO, app.size)
	for button in app.buttons:
		if not canvas.encloses(button.rect):
			return false
	return true


func _screen_tap(app: Control, at: Vector2, redraw_while_held: bool = true) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 0
	# Inject physical window pixels into Godot's input dispatcher.
	event.position = app.get_viewport_transform() * at
	event.pressed = true
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	if redraw_while_held:
		await _paint(app)
	event = InputEventScreenTouch.new()
	event.index = 0
	event.position = app.get_viewport_transform() * at
	event.pressed = false
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await _paint(app)


func _test_responsive_touch_targets(app: Control) -> void:
	var saved_meta: Dictionary = app.meta.duplicate(true)
	app._change("restaurant")
	app.backgrounded = false
	app.editing = false
	await _paint(app)
	check(app.size.is_equal_approx(root.get_visible_rect().size), "Game control fills the actual viewport")
	check(is_equal_approx(app.size.x / app.size.y, float(requested_size.x) / requested_size.y), "Game canvas preserves the requested phone aspect ratio without letterboxing")
	check(_targets_fit(app), "Restaurant controls fit inside the actual phone canvas")
	var settings := _button_rect(app, "settings")
	check(settings.has_area(), "Restaurant exposes a reachable settings target")
	await _screen_tap(app, settings.get_center())
	check(app.modal == "settings", "Settings opens through a touch held across redraws")
	check(_targets_fit(app), "Settings controls fit inside the actual phone canvas")
	var music := _button_rect(app, "setting", "music")
	var music_before: bool = bool(app.meta.music)
	await _screen_tap(app, Vector2(music.position.x + 2, music.get_center().y))
	check(bool(app.meta.music) != music_before, "A touch near the left edge of a settings control activates it")
	var close := _button_rect(app, "close")
	await _screen_tap(app, close.end - Vector2(2, 2))
	check(app.modal.is_empty(), "A touch near the far corner closes the settings panel")
	var edit := _button_rect(app, "edit")
	await _screen_tap(app, edit.get_center())
	check(app.editing and _targets_fit(app), "Bottom arrangement control opens an on-screen edit tray")
	var live := _button_rect(app, "live")
	await _screen_tap(app, live.end - Vector2(2, 2))
	check(not app.editing, "The edit tray's far edge returns to live service")
	var dock := _button_rect(app, "dock")
	check(dock.has_area() and dock.get_center().y > app.size.y * 0.75, "The submarine remains reachable in the bottom region of the phone")
	app.meta.charge = 1.0
	await _screen_tap(app, dock.get_center())
	check(app.screen == "prep" and _targets_fit(app), "Dock touch opens preparation with every target on-screen")
	var launch := _button_rect(app, "launch")
	check(launch.has_area() and launch.get_center().y > app.size.y * 0.7, "Preparation exposes its start control below the route choices")
	var back := _button_rect(app, "restaurant")
	await _screen_tap(app, back.get_center())
	check(app.screen == "restaurant", "Preparation's bottom navigation returns to the restaurant")
	settings = _button_rect(app, "settings")
	await _screen_tap(app, settings.get_center(), false)
	check(app.modal == "settings", "A press and release in the same frame still opens settings")
	app.modal = ""
	app.meta = saved_meta
	app.audio.configure(bool(app.meta.sound), bool(app.meta.music))
	await _paint(app)
