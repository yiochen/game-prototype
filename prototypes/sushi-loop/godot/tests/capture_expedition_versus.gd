extends SceneTree
## Native evidence for the versus HUD: the travel row (hull + gold), the
## arrival transition (gold lifts away, the eel bar slides in and fills), the
## chase with the eel clear of the HUD, and the gold count's return after an
## escape. Run through tools/test_native.py --visible with an output folder.
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
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name + ".png"))

func live() -> Variant: return app.session._state.expedition.run
func play(seconds: float) -> void: await create_timer(seconds).timeout

func dive_to_arena() -> void:
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); ui.start()
	var r: Dictionary = live()
	r.y = float(Book.run_route(r).encounter_start) + 1.5; r.x = 5.5; r.vx = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state)}, 0.0); ui.view.snap_camera()

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	var s = Session.new_session(24, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	app.session = s; app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui

	await dive_to_arena()
	await play(0.2)
	check(ui.salvage_pill.visible and not ui.resistance_pill.visible, "travel shows hull and gold, no creature bar")
	await capture("01-travel-row")
	var guard := 0
	while live().encounter == null and guard < 300: await process_frame; guard += 1
	var at := Time.get_ticks_msec()
	for ms in [120, 300, 420, 600, 850, 1400]:
		await play(maxf(0.0, (ms - (Time.get_ticks_msec() - at)) / 1000.0))
		await capture("02-arrival-%04dms" % ms)
	check(not ui.salvage_pill.visible and ui.resistance_pill.visible and ui.resistance_pill.modulate.a == 1.0, "after the arrival the gold count is gone and the eel bar is in place")
	check(absf(ui.resistance_pill.position.y - ui.hull_pill.position.y) < 0.5, "hull and eel bars share the top row")
	# Hook and chase: the eel's head clears the single HUD row.
	live().x = Book.creature_centre(live()).x; live().vx = 0.0
	ui.fire()
	guard = 0
	while live().encounter.state != "hooked" and guard < 400: await process_frame; guard += 1
	await play(2.5)
	var head: Vector2 = ui.view.creature.to_view(ui.view.creature.bone_world("head"))
	var row_bottom: float = ui.hull_pill.position.y + ui.hull_pill.size.y - ui.view.position.y
	check(head.y > row_bottom, "the eel's head (%.0f) is below the HUD row (%.0f)" % [head.y, row_bottom])
	await capture("03-chase")

	# A second dive where the eel escapes: the gold count comes back.
	ui.pause(); ui.return_early(); ui.finish_results()
	app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
	await dive_to_arena()
	guard = 0
	while (live() == null or live().encounter == null) and guard < 300: await process_frame; guard += 1
	live().encounter.t = float(Book.definition().encounter.window_seconds) - 0.1
	guard = 0
	while live().encounter.state != "escaped" and guard < 300: await process_frame; guard += 1
	await play(0.5)
	check(ui.salvage_pill.visible and ui.salvage_pill.modulate.a > 0.99 and not ui.resistance_pill.visible, "after an escape the gold count returns")
	await capture("04-after-escape")
	print("Expedition versus captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
