extends SceneTree
## Native issue #21 evidence: the real game flow from the dock through travel,
## Pause, early return, results and the charging dock message. Run through
## tools/test_native.py --visible with an output folder; headless runs only
## exercise the flow.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
var app
var destination := ""
var manifest: Array = []
var failures: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message); printerr("FAIL: " + message)

func capture(name: String) -> void:
	await process_frame
	await process_frame
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(destination.path_join(name + ".png"))
	manifest.append({"name": name, "size": [image.get_width(), image.get_height()]})

func revealed_session(seed_value: int):
	var s = Session.new_session(seed_value, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	return s

func exp_view() -> Dictionary: return {"expedition": Book.snapshot(app.session._state, app.session._store)}

func use(s) -> void:
	app.session = s; app._refresh(); app._layout()

func travel(seconds: float, steer: Callable = Callable()) -> void:
	var t := 0.0
	while t < seconds and app.expedition_ui.mode == "travel" and app.expedition_ui.overlay == "none":
		if steer.is_valid(): steer.call()
		app.expedition_ui.update(exp_view(), 0.05)
		t += 0.05

func safe_steer() -> void:
	var run = Book.snapshot(app.session._state, app.session._store).run
	if run == null: return
	var rows: Array = Book.route(int(run.seed)).rows
	var best := float(run.x); var best_score := INF
	for i in range(1, 22):
		var x := i * .5; var score := absf(x - float(run.x)) * .01
		for ahead in [0.0, .3, .6, 1.0, 1.4]:
			if Book._overlaps(rows, x, float(run.y) - ahead, Vector2(.32, .44)): score += 10.0 / (1.0 + ahead)
		if score < best_score: best_score = score; best = x
	# Braking-aware stick: never more sideways speed than can stop at the target.
	var rules: Dictionary = Book.definition()
	var err := best - float(run.x)
	var speed := float(rules.lateral_columns_per_second)
	app.session.command({"type": "expedition_steer", "input": signf(err) * minf(1.0, sqrt(2.0 * float(rules.lateral_acceleration) * absf(err)) * .85 / speed)})

func run() -> void:
	var args := OS.get_cmdline_user_args()
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	use(revealed_session(19))
	await capture("00-restaurant-dock-ready")
	var ui = app.expedition_ui
	app._open_landmark("Submarine")
	check(ui.visible and ui.mode == "prep", "ready dock opens preparation")
	check(Book.charge(app.session._state, Time.get_unix_time_from_system()).ready, "preparation spends no charge")
	await capture("01-preparation")
	ui.close_prep()
	check(not ui.visible and Book.charge(app.session._state, Time.get_unix_time_from_system()).ready, "Sushi Bar return before Start is free")
	app._open_landmark("Submarine"); ui.start()
	check(ui.mode == "travel" and app.session.snapshot().expedition.run != null, "Start departs once")
	travel(4.0, safe_steer)
	await capture("02-travel")
	travel(9.0, safe_steer)
	await capture("03-travel-later")
	# Real-time travel through the game's own frame loop.
	var started := Time.get_ticks_msec()
	var frames := 0
	while Time.get_ticks_msec() - started < 3000 and ui.mode == "travel":
		safe_steer(); await process_frame; frames += 1
	var fps := frames * 1000.0 / maxf(1.0, Time.get_ticks_msec() - started)
	manifest.append({"name": "travel-frame-rate", "fps": snappedf(fps, 0.1)})
	print("Travel frame rate: %.1f fps" % fps)
	# Drive into the wall until the hull runs low.
	var hits := 0
	while exp_view().expedition.run != null and not exp_view().expedition.run.low_hull and hits < 400:
		app.session.command({"type": "expedition_steer", "input": -1.0}); app.expedition_ui.update(exp_view(), 0.05); hits += 1
	for i in range(30): safe_steer(); app.expedition_ui.update(exp_view(), 0.05)
	check(exp_view().expedition.run.low_hull, "low hull warning shows")
	await capture("04-low-hull")
	ui.pause()
	await capture("05-paused")
	ui._show_overlay("confirm")
	await capture("06-return-early-confirm")
	ui._show_overlay("paused"); ui.resume()
	await capture("07-resume-countdown")
	ui._finish_countdown()
	ui.pause(); ui.return_early()
	check(ui.mode == "results" and ui.result.outcome == "returned_early", "confirmed early return shows Returned early")
	await capture("08-results-returned-early")
	ui.finish_results()
	check(not ui.visible and app.session.snapshot().camera.x == 0.0, "Restaurant returns to the recentred bar")
	await capture("09-back-at-restaurant")
	app._open_landmark("Submarine")
	check(not ui.visible and app.clearance_toast.visible and app.clearance_toast.text.begins_with("Charging"), "charging dock tap shows the time remaining")
	await capture("10-charging-message")

	# A complete run and a hull-depleted run on fresh restaurants.
	use(revealed_session(23))
	app._open_landmark("Submarine"); ui.start()
	travel(200.0, safe_steer)
	check(ui.mode == "results" and ui.result.outcome == "complete" and int(ui.result.bonus) > 0, "steering clear completes with the bonus")
	await capture("11-results-complete")
	ui.finish_results()
	use(revealed_session(29))
	app._open_landmark("Submarine"); ui.start()
	var guard := 0
	while ui.mode == "travel" and guard < 4000:
		app.session.command({"type": "expedition_steer", "input": -1.0}); ui.update(exp_view(), 0.05); guard += 1
	check(ui.result.get("outcome") == "hull_depleted", "running out of hull shows Hull depleted")
	await capture("12-results-hull-depleted")
	ui.finish_results()

	# Reopening with unfinished travel waits behind Paused.
	use(revealed_session(31))
	app._open_landmark("Submarine"); ui.start(); travel(3.0, safe_steer)
	var saved: Dictionary = JSON.parse_string(JSON.stringify(app.session.save_data(), "", true, true))
	ui.suspend(); ui.mode = "hidden"; ui.hide()
	var reopened = Session.new(); reopened.restore(saved); use(reopened)
	ui.resume_suspended(app.session.snapshot())
	check(ui.mode == "travel" and ui.overlay == "paused" and app.session.snapshot().expedition.run.paused, "reopened travel waits behind Paused")
	await capture("13-reopened-paused")

	if not destination.is_empty():
		var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify(manifest, "\t")); file.close()
	print("Expedition native flow: %d failures, %d captures" % [failures.size(), manifest.size()])
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0 if failures.is_empty() else 1)
