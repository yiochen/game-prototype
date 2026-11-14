extends SceneTree
## Native issue #76 evidence from the real game: the Boulderhead Parrotfish's
## broken path. The hooked parrotfish, cracks spreading on the reef wall, the
## smash with break frames and debris, the breach, a crash through reef off the
## path with the hit feedback, and the catch award.
## Run through tools/test_native.py --visible with an output folder.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Reef = preload("res://scripts/expedition/reef.gd")
const PARROT := "boulderhead-parrotfish"
var app
var destination := ""
var failures: Array[String] = []
var guide := true
var heard: Array = []

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message); printerr("FAIL: " + message)

func capture(name: String) -> void:
	await process_frame
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name + ".png"))

func live() -> Variant: return app.session._state.expedition.run
## Wait frame by frame until `test` passes, holding resistance and (while
## `guide` is on) keeping the ship on the parrotfish's line.
func wait_for(test: Callable, limit := 900) -> bool:
	for i in range(limit):
		if live() == null: return false
		live().encounter.resistance = 100.0
		if guide:
			var path := Book.run_route(live())
			var zone = Book.reef_zone_at(path, float(live().y))
			if zone != null: live().x = Reef.line_at(zone.xs, int(zone.bottom) - int(zone.y0), float(live().y) - float(zone.y0))
			else: live().x = Book._centre_of(str(path.rows[clampi(int(floor(float(live().y) - 0.6)), 0, path.rows.size() - 1)]))
			live().vx = 0.0; live().protection = 1.0
		if test.call(): return true
		await process_frame
	return false

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
	var view = ui.view
	app.audio.cue_played.connect(func(cue): heard.append(cue))

	ui._cheat_creature = PARROT
	app._open_landmark("Submarine")
	for i in range(600):
		if ui.mode == "prep" and not app.transition.visible: break
		await process_frame
	await create_timer(0.4).timeout
	ui.start()
	check(live() != null and Book.creature_of(live()) == PARROT, "the dive is for the parrotfish")
	if live() == null: print("Expedition reef captures: the dive did not start"); quit(1); return
	var r: Dictionary = live()
	r.y = float(Book.run_route(r).encounter_start) + 1.2; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); view.snap_camera()
	guide = false
	await create_timer(2.2).timeout
	await capture("01-parrotfish-arrives")
	for shot in range(5):
		live().x = Book.creature_centre(live()).x; live().vx = 0.0
		ui.fire()
		if await wait_for(func(): return live().encounter.state == "hooked", 120): break
	check(live().encounter.state == "hooked", "the parrotfish is hooked")
	guide = true
	# Let the hook's slow motion and focus ring finish first.
	await wait_for(func(): return ui.time_scale >= 0.999 and view.focus_amount <= 0.001, 600)
	check(view.creature.species == PARROT, "the view shows the parrotfish model")
	check(app.session.command({"type": "expedition_cheat_zone"}).ok, "the debug skip reaches a reef chunk")
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); view.snap_camera()
	await create_timer(0.3).timeout
	await capture("02-reef-ahead")
	check(await wait_for(func(): return not Book.reef_cracks(live()).is_empty()), "cracks spread before the smash")
	await wait_for(func(): return Book.reef_cracks(live()).values().any(func(k): return k > .7))
	await capture("03-cracks")
	check(await wait_for(func(): return live().reef_broken.size() > 0), "the parrotfish smashes the wall")
	await create_timer(0.12).timeout
	await capture("04-smash")
	await wait_for(func(): return live().reef_broken.size() >= 12)
	await capture("05-breach")
	check("reef_breach" in heard and "reef_smash" in heard, "the breach and smash cues play (heard %s)" % str(heard))

	# Off the path: the hull crashes through reef with the full hit feedback.
	guide = false
	var zone = Book.reef_zone_at(Book.run_route(live()), float(live().y) - 3.0)
	if zone != null:
		var line := Reef.line_at(zone.xs, int(zone.bottom) - int(zone.y0), float(live().y) - float(zone.y0))
		live().x = clampf(line + (2.6 if line < 5.5 else -2.6), 1.5, 9.5); live().vx = 0.0; live().protection = 0.0
	var hull := float(live().hull)
	for i in range(120):
		if float(live().hull) < hull: break
		live().encounter.resistance = 100.0
		await process_frame
	check(float(live().hull) < hull, "ramming reef costs hull")
	await create_timer(0.1).timeout
	await capture("06-crash")
	check("reef_crash" in heard, "the crash cue plays")

	guide = true
	live().encounter.resistance = 0.01
	for i in range(400):
		if ui.overlay == "award": break
		if live() != null: live().protection = 1.0
		await process_frame
	check(ui.overlay == "award" and ui.award.name.text == "Budai sashimi", "the award names Budai sashimi")
	await create_timer(0.6).timeout
	await capture("07-award")
	print("Expedition reef captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
