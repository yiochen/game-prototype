extends SceneTree
## Native issue #70 evidence from the real game: the Inkfin Cuttlefish's ink
## blackout during the hooked chase. The cuttlefish before the ink, the warning
## pulse, the ink seeping in, the purple light cone straight and swung into a
## turn, the ink lifting, and a catch under the ink that clears it at once.
## Run through tools/test_native.py --visible with an output folder.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const INKFIN := "inkfin-cuttlefish"
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
func ink() -> Variant: return live().encounter.get("ink") if live() != null and live().encounter is Dictionary else null
## Wait frame by frame until `test` passes, holding resistance and (while
## `guide` is on) keeping the ship in open water so the evidence run survives.
func wait_for(test: Callable, limit := 900) -> bool:
	for i in range(limit):
		if live() == null: return false
		live().encounter.resistance = 100.0; live().protection = 1.0
		if guide:
			var rows: Array = Book.run_route(live()).rows
			live().x = Book._centre_of(str(rows[clampi(int(floor(float(live().y) - 0.6)), 0, rows.size() - 1)])); live().vx = 0.0
		if test.call(): return true
		await process_frame
	return false
func play(seconds: float) -> void:
	var until := Time.get_ticks_msec() + int(seconds * 1000)
	await wait_for(func(): return Time.get_ticks_msec() >= until, 100000)

## Dive for the Inkfin, jump to the arena and hook it.
func hook_inkfin() -> void:
	var ui = app.expedition_ui
	if ui.cheat_creature_button == null: ui._cheat_creature = INKFIN
	app._open_landmark("Submarine")
	# The scene transition (#28) closes, loads and reopens on the preparation.
	for i in range(600):
		if ui.mode == "prep" and not app.transition.visible: break
		await process_frame
	await create_timer(0.4).timeout
	# With the cheats flag, the preparation's debug button picks the species.
	if ui.cheat_creature_button != null:
		check(ui.cheat_creature_button.visible, "the debug creature button shows during preparation")
		for press in range(3):
			if ui._cheat_creature == INKFIN: break
			ui.cheat_creature_button.pressed.emit()
		check(ui._cheat_creature == INKFIN and ui.cheat_creature_button.text == "DEBUG · Inkfin Cuttlefish", "pressing it chooses the Inkfin")
		await process_frame
	if DisplayServer.window_get_size().x == 390: await capture("00-prep-cheats" if ui.cheat_creature_button != null else "00-prep")
	ui.start()
	check(live() != null and Book.creature_of(live()) == INKFIN, "the debug choice dives for the Inkfin")
	if live() == null: print("Expedition ink captures: the dive did not start"); quit(1); return
	var r: Dictionary = live()
	r.y = float(Book.run_route(r).encounter_start) + 1.2; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); ui.view.snap_camera()
	guide = false
	await create_timer(2.2).timeout
	await capture("01-inkfin-arrives")
	for shot in range(5):
		live().x = Book.creature_centre(live()).x; live().vx = 0.0
		ui.fire()
		if await wait_for(func(): return live().encounter.state == "hooked", 120): break
	guide = true
	await play(1.3)

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
	var k: Dictionary = Book.definition().encounter.ink
	app.audio.cue_played.connect(func(cue): heard.append(cue))

	await hook_inkfin()
	check(view.creature.species == INKFIN, "the view shows the cuttlefish model")
	await capture("02-hooked-chase")
	check(app.session.command({"type": "expedition_cheat_zone"}).ok, "the debug skip reaches an ink zone")
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); view.snap_camera()
	check(await wait_for(func(): return ink() != null), "the Inkfin warns in its ink zone")
	check(view.ink() != null and view._ink_layer.visible and view.creature.clip == "windup", "the warning shows and the cuttlefish swells")
	await wait_for(func(): return ink().phase == "warn" and float(ink().t) >= float(k.warn_seconds) / 6.0)
	await capture("03-warning-pulse")
	await wait_for(func(): return ink().phase == "spread" and float(ink().t) >= float(k.spread_seconds) * 0.3)
	await capture("04-ink-seeping-in")
	await wait_for(func(): return ink().phase == "spread" and float(ink().t) >= float(k.spread_seconds) * 0.7)
	await capture("05-ink-nearly-full")
	await wait_for(func(): return ink().phase == "hold" and float(ink().t) >= 0.5)
	check(Book.ink_cover(live()) == 1.0, "the ink holds at full cover")
	await capture("06-light-cone")
	# Steering swings the beam into the turn.
	guide = false
	live().steer = -1.0
	await play(0.3)
	check(view._cone_tilt < -0.1, "steering left swings the beam left")
	await capture("07-light-cone-steering-left")
	live().steer = 0.0; guide = true
	await wait_for(func(): return ink() == null or ink().phase == "lift")
	await play(0.45)
	await capture("08-ink-lifting")
	check("ink_warn" in heard and "ink_burst" in heard and "ink_lift" in heard, "the warning, burst and lift each play their cue (heard %s)" % str(heard))

	# A catch under the ink clears it at once.
	check(await wait_for(func(): return ink() != null and ink().phase == "hold", 3000), "the second zone inks too")
	live().encounter.resistance = 0.01
	for i in range(60):
		if ui.overlay == "outro": break
		await process_frame
	check(ui.overlay == "outro" and view.ink() == null and not view._ink_layer.visible, "catching the Inkfin under the ink removes it at once")
	await create_timer(1.2).timeout
	await capture("09-caught")
	for i in range(400):
		if ui.overlay == "award": break
		await process_frame
	check(ui.overlay == "award" and ui.award.name.text == "Ika nigiri", "the award names Ika nigiri")
	await create_timer(0.6).timeout
	await capture("10-award")

	# The light on a 16:9 phone and a wider window.
	for size in [Vector2i(405, 720), Vector2i(600, 820)]:
		while ui.overlay in ["outro", "award"] or ui.mode == "results":
			if ui.overlay == "award": ui._award_continue()
			if ui.mode == "results": ui.finish_results()
			await process_frame
		# Results return to the restaurant through the scene transition.
		for i in range(600):
			if ui.mode == "hidden" and not app.transition.visible: break
			await process_frame
		DisplayServer.window_set_size(size); root.size = size
		await create_timer(0.3).timeout; app._layout()
		app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
		await hook_inkfin()
		app.session.command({"type": "expedition_cheat_zone"})
		ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); view.snap_camera()
		await wait_for(func(): return ink() != null and ink().phase == "hold" and float(ink().t) >= 0.5)
		await capture("11-light-cone-%dx%d" % [size.x, size.y])
		ui.pause(); ui.give_up(); await process_frame
	print("Expedition ink captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
