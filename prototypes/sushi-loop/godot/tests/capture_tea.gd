extends SceneTree
## #62 native review captures: the tea-green request bubble beside another
## guest's happy bubble, the pour sheet over the live restaurant, a real touch
## drag on the tilt arc, the graded result and the guest's sip, and an overflow.
##   python3 godot/tools/test_native.py --script tests/capture_tea.gd --visible --resolution 390x844 --output review/62/native/phone

const Session = preload("res://scripts/session.gd")
const Tea = preload("res://scripts/features/tea.gd")
const APP = preload("res://main.tscn")
var app
var destination := ""
var manifest: Array = []
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message);printerr("FAIL: " + message)

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41, {"starting_coins": 2000})
	app._refresh()
	for step in range(900): app.advance_time(0.05, false)
	# Freeze the existing requests so the captures are deterministic, then ask.
	var seated: Array = app.session._customers().filter(func(c): return c.phase == "waiting" and c.first_dish_received)
	for customer in app.session._customers():
		if customer.tea_phase in ["requested", "pouring"]: customer.tea_phase = "skipped"
	check(seated.size() >= 2, "two seated guests for the captures")
	var asking: Dictionary = seated[0]
	asking.preference_phase = "complete"
	asking.tea_phase = "requested"; asking.tea_cup = "flask"; asking.tea_elapsed = 2.5
	var happy: Dictionary = seated[1]
	happy.preference_phase = "satisfied"; happy.preference_phase_elapsed = 1.2; happy.happy_elapsed = 1.2
	app._layout()
	app._refresh()
	await settle(0.5)
	await capture("01-tea-request-and-happy")
	# A real tap on the guest opens the sheet; the bubble is dismissed.
	app._tip_tap({"kind": "tea", "customer_id": asking.id})
	await settle(0.5)
	check(app.tea_ui.visible and app.session._customer_by_id(asking.id).tea_phase == "pouring", "tapping opens the pour and dismisses the bubble")
	await capture("02-pour-sheet")
	# Drag the handle down the arc with real touch events.
	var ui = app.tea_ui
	var stage: Vector2 = ui.sheet.position + Vector2(0, ui.HEADER * ui.unit)
	var start: Vector2 = stage + ui._arc_point(0.0) * ui.unit
	touch(start, true)
	for step in range(1, 13):
		drag(stage + ui._arc_point(62.0 * step / 12.0) * ui.unit)
		await process_frame
	await settle(1.1)
	check(ui.pour.poured and ui.held, "a drag on the arc tilts the pot and pours")
	await capture("03-pouring")
	touch(stage + ui._arc_point(62.0) * ui.unit, false)
	await settle(0.55)
	check(not ui.result.is_empty(), "letting go serves the pour")
	await capture("04-result")
	var grade: String = str(ui.result.get("id", ""))
	await settle(1.4)
	check(not ui.visible and app.session._customer_by_id(asking.id).tea_phase == "served", "the sheet closes and the tea is served (%s)" % grade)
	await capture("05-sip")
	# Overflow on a tea bowl, held at full tilt.
	var second: Dictionary = seated[1]
	second.preference_phase = "complete"
	second.tea_phase = "requested"; second.tea_cup = "bowl"; second.tea_elapsed = 0.0
	app._tip_tap({"kind": "tea", "customer_id": second.id})
	await settle(0.4)
	ui.held = true; ui.tilt = 1.0
	await settle(4.6)
	check(float(ui.pour.spilled) > 0.0, "holding full tilt overflows the bowl")
	await capture("06-overflow-pouring")
	ui.held = false; ui.tilt = 0.0
	await settle(0.55)
	await capture("07-overflow-result")
	await settle(1.6)
	await capture("08-surprised")
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": manifest, "first_grade": grade, "failures": failures}, "\t"))
	file.close()
	print("Captured %d #62 screens, %d failures" % [manifest.size(), failures.size()])
	app.queue_free()
	await process_frame
	quit(1 if not failures.is_empty() else 0)

func touch(at: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new()
	event.index = 0; event.pressed = pressed; event.position = app.get_viewport_transform() * at
	Input.parse_input_event(event)

func drag(at: Vector2) -> void:
	var event := InputEventScreenDrag.new()
	event.index = 0; event.position = app.get_viewport_transform() * at
	Input.parse_input_event(event)

func settle(seconds: float) -> void:
	await create_timer(seconds).timeout

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(destination.path_join(name + ".png"))
	manifest.append({"name": name, "pixels": [image.get_width(), image.get_height()]})
