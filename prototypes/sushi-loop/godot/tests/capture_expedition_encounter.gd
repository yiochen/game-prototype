extends SceneTree
## Native issue #23 evidence from the real game: the creature arriving with
## the Harpoon button ready, a shot in flight with the reload ring, a miss
## reeling back, the slow-motion strike, the hooked handoff (pinned harpoon,
## dimmed arrows, callout), Pause over the hook, and a restless creature that
## escapes. Run through tools/test_native.py --visible with an output folder.
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

func run_state() -> Dictionary: return Book.snapshot(app.session._state).run

## Let the running game advance for `seconds` of real time (the app drives
## the presentation every frame, slow motion included).
func play(seconds: float) -> void:
	await create_timer(seconds).timeout

## Test-only cut: move the saved run to the encounter's opening row.
func to_encounter() -> void:
	var r: Dictionary = app.session._state.expedition.run
	r.y = float(Book.run_route(r).encounter_start) + 1.2; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	app.expedition_ui.update({"expedition": Book.snapshot(app.session._state)}, 0.0)
	app.expedition_ui.view.snap_camera()

## Put the ship under the creature, or `offset` columns beside it toward the
## arena's middle (clear of the walls).
func line_up(offset := 0.0) -> void:
	var r: Dictionary = app.session._state.expedition.run
	var x := Book.creature_centre(r).x
	r.x = x + (offset if x < 5.5 else -offset); r.vx = 0.0

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = revealed_session(23); app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); ui.start()
	to_encounter()
	await play(2.6)
	check(run_state().encounter != null and run_state().encounter.state == "aiming", "the window opens in the arena")
	check(ui.harpoon_button.visible and ui.harpoon_button.state == "ready" and ui.resistance_pill.visible, "Harpoon and resistance appear with the creature")
	await capture("01-aiming-ready")

	line_up(2.2); ui.fire()
	await play(0.3)
	check(ui.harpoon_button.state == "reloading", "the ring reloads after a shot")
	await capture("02-shot-in-flight")
	await play(0.9)
	await capture("03-miss-reeling")
	await play(1.2)
	check(ui.harpoon_button.state == "ready", "the harpoon is ready again after the reload")

	line_up(); ui.fire()
	var guard := 0
	while ui.time_scale > 0.3 and guard < 180: await process_frame; guard += 1
	check(ui.time_scale < 0.5 and ui.view.focus_amount > 0.5, "the strike slows the game and focuses on the impact")
	await capture("04-strike-slow-motion")
	guard = 0
	while run_state().encounter.state != "hooked" and guard < 240: await process_frame; guard += 1
	await play(0.15)
	check(run_state().encounter.state == "hooked", "the harpoon hooks the creature")
	await capture("05-hooked")
	await play(1.6)
	check(not ui.harpoon_button.visible and ui.view.controls_disabled, "after the hook the button goes and the arrows dim")
	await capture("06-hooked-holding")
	ui.pause()
	await capture("07-hooked-paused")

	# A second dive: never hook; the creature turns restless, then escapes.
	ui.return_early(); ui.finish_results()
	app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
	app._open_landmark("Submarine"); ui.start()
	to_encounter()
	var rules: Dictionary = Book.definition().encounter
	await play(float(rules.window_seconds) - float(rules.restless_seconds) + 1.0)
	check(ui.view.creature.clip == "restless", "the creature turns restless before the window closes")
	await capture("08-restless")
	await play(float(rules.restless_seconds) + 0.4)
	check(run_state().encounter.state == "escaped", "the window expires and the creature escapes")
	await capture("09-escaped")
	print("Expedition encounter captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
