extends SceneTree
## Native issue #22 evidence from the real game: a current field, the shield
## pickup and active shield (with a rock bump), the portal, the whirlpool
## transition, the automatic passage ride (dimmed arrows) and the rejoin
## outflow. Run through tools/test_native.py --visible with an output folder.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
var app
var destination := ""
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message); printerr("FAIL: " + message)

func capture(name: String) -> void:
	await process_frame
	await process_frame
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name + ".png"))

func revealed_session(seed_value: int):
	var s = Session.new_session(seed_value, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	return s

func run_state() -> Dictionary: return Book.snapshot(app.session._state, app.session._store).run

## Advance the real presentation by `seconds` in 1/30 s frames.
func play(seconds: float, steer := 0.0) -> void:
	var ui = app.expedition_ui
	for i in range(int(round(seconds * 30))):
		if ui.mode != "travel": return
		if run_state().passage == null: app.session.command({"type": "expedition_steer", "input": steer})
		ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 1.0 / 30.0)

## Test-only cut: move the saved run onto a spot of its route.
func place(x: float, y: float) -> void:
	var r: Dictionary = app.session._state.expedition.run
	r.x = x; r.y = y; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	app.expedition_ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0)
	app.expedition_ui.view.snap_camera()

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = revealed_session(22); app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); ui.start()
	var path := Book.run_route(run_state())

	var crossing: Dictionary = path.spans.filter(func(span): return span.kind == "current")[0]
	place(Book._centre_of(path.rows[int(crossing.y1)]), float(crossing.y1) - 2.0)
	var x0 := float(run_state().x)
	play(1.2)
	check(absf(float(run_state().x) - x0) > 0.8, "the released ship drifts with the current")
	await capture("01-current-field")

	var shield: Vector2 = path.shields[0]
	place(shield.x, shield.y + 3.2)
	play(0.4)
	await capture("02-shield-pickup")
	play(1.4)
	check(float(run_state().shield) > 0.0, "the shield is active after pickup")
	await capture("03-shield-active")
	var hull := float(run_state().hull)
	play(1.2, -1.0)
	check(float(run_state().hull) == hull, "rock bumps the shield without damage")
	await capture("04-shield-bump")

	var portal: Dictionary = path.portals[0]
	place(float(portal.x) + 1.0, float(portal.y) + 3.5)
	play(0.3)
	await capture("05-portal-approach")
	place(float(portal.x), float(portal.y) + 0.6)
	play(0.4)
	check(run_state().passage != null and ui.view.transitioning(), "steering onto the portal starts the whirlpool transition")
	await capture("06-portal-transition")
	play(1.4)
	await capture("07-passage-ride")
	check(ui.view.controls_disabled and ui.ride_note.visible, "the passage ride dims the arrows and says the current steers")
	var guard := 0
	while run_state().passage != null and guard < 600: play(1.0 / 30.0); guard += 1
	play(0.45)
	await capture("08-passage-exit-iris")
	play(0.75)
	await capture("09-rejoin-outflow")
	check(run_state().passage == null and 0 in run_state().portals_used, "the ride rejoins the main route with the portal spent")
	place(float(portal.x) + 1.0, float(portal.y) + 2.5)
	play(0.2)
	await capture("10-portal-spent")
	ui.pause()
	await capture("11-paused-with-features")
	print("Expedition feature captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
