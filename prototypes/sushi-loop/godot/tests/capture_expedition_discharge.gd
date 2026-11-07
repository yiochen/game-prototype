extends SceneTree
## Native issue #25 evidence from the real game: the Storm Eel's discharge in
## its own chunk during the hooked chase. Entering the eel chunk, the warned
## strip (steady, then flashing on and off), the live strike dodged, a hit, and
## a catch in the middle of a strike that clears the strip at once. Run through
## tools/test_native.py --visible with an output folder.
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
func strike() -> Variant: return live().encounter.get("discharge") if live() != null else null
## Wait (frame by frame, holding resistance) until `test` passes.
func wait_for(test: Callable, limit := 600) -> bool:
	for i in range(limit):
		if live() == null: return false
		live().encounter.resistance = 100.0
		if test.call(): return true
		await process_frame
	return false

## Dive, jump to the arena, hook the creature, then skip to the next eel chunk.
func into_eel_chunk() -> void:
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); ui.start()
	var r: Dictionary = live()
	r.y = float(Book.run_route(r).encounter_start) + 1.2; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); ui.view.snap_camera()
	await play(2.2)
	for shot in range(5):
		live().x = Book.creature_centre(live()).x; live().vx = 0.0
		ui.fire()
		if await wait_for(func(): return live().encounter.state == "hooked", 120): break
	await play(1.2)
	check(app.session.command({"type": "expedition_cheat_zone"}).ok, "the debug skip reaches an eel chunk")
	ui.update({"expedition": Book.snapshot(app.session._state, app.session._store)}, 0.0); ui.view.snap_camera()

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
	var d: Dictionary = Book.definition().encounter.discharge
	var warn := float(d.warn_seconds)
	var flash_from := warn - float(d.flash_seconds)
	var blink := float(d.flash_seconds) / (int(d.flashes) * 2)

	await into_eel_chunk()
	await capture("01-eel-chunk")
	check(await wait_for(func(): return strike() != null), "the eel winds up in its chunk")
	check(view.discharge() != null and view.creature.clip == "windup", "the warned strip shows and the eel plays its windup")
	await wait_for(func(): return float(strike().t) >= 0.45)
	await capture("02-windup-steady")
	await wait_for(func(): return float(strike().t) >= flash_from + 0.01)
	await capture("03-windup-flash-on")
	await wait_for(func(): return float(strike().t) >= flash_from + blink + 0.01)
	await capture("04-windup-flash-off")
	# Dodge: steer clear of the strip before it goes live.
	var shape: Dictionary = strike()
	live().x = clear_side(shape); live().vx = 0.0
	await wait_for(func(): return strike() != null and strike().phase == "strike" and float(strike().t) >= warn + 0.1)
	check(view.creature.clip == "attack", "the eel plays its attack while the strip is live")
	await capture("05-strike-dodged")
	var hull_before := float(live().hull)
	await wait_for(func(): return strike() == null)
	check(float(live().hull) == hull_before, "the dodged strike does no damage")

	# A hit: the ship sits in the next strip when it goes live.
	await next_windup()
	check(strike() != null, "the eel winds up again")
	if strike() == null: finish(); return
	live().x = float(strike().x0) + float(strike().w) / 2.0; live().vx = 0.0; live().protection = 0.0
	await wait_for(func(): return live().protection > 0.0 or strike() == null)
	check(float(live().hull) < hull_before, "standing in the live strip costs hull")
	await play(0.05)
	await capture("06-strike-hit")

	# A catch in the middle of a strike: the strip and lightning go at once.
	await wait_for(func(): return strike() == null)
	live().protection = 0.0
	await next_windup()
	check(await wait_for(func(): return strike() != null and strike().phase == "strike", 200), "a third strike goes live")
	live().encounter.resistance = 0.01
	for i in range(60):
		if ui.overlay == "outro": break
		await process_frame
	check(ui.overlay == "outro" and view.discharge() == null and view._bolts.is_empty() and view._afterglow.is_empty(), "catching the eel mid-strike removes the strip and lightning")
	await play(0.3)
	await capture("07-caught-mid-strike")
	# The same warning on a 16:9 phone and a wider window.
	for size in [Vector2i(405, 720), Vector2i(600, 820)]:
		while ui.overlay in ["outro", "award"] or ui.mode == "results":
			if ui.overlay == "award": ui._award_continue()
			if ui.mode == "results": ui.finish_results()
			await process_frame
		DisplayServer.window_set_size(size); root.size = size
		await play(0.3); app._layout()
		app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
		await into_eel_chunk()
		await wait_for(func(): return strike() != null and float(strike().t) >= flash_from + 0.01)
		await capture("08-windup-%dx%d" % [size.x, size.y])
		ui.pause(); ui.give_up(); await process_frame
	finish()

func finish() -> void:
	print("Expedition discharge captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)

## Open water beside the strip: the side with more room before the walls.
func clear_side(shape: Dictionary) -> float:
	var rows: Array = Book.run_route(live()).rows
	var y := float(live().y)
	for x in [float(shape.x0) + float(shape.w) + 1.0, float(shape.x0) - 1.0, float(shape.x0) + float(shape.w) + 0.6, float(shape.x0) - 0.6]:
		if x > 0.5 and x < 10.5 and not Book._collides(rows, x, y - 1.5, 0.45) and not Book._collides(rows, x, y, 0.45): return x
	return float(shape.x0) - 1.0

## The next windup in this chunk, or skip to the next eel chunk for it.
func next_windup() -> void:
	if await wait_for(func(): return strike() != null, 360): return
	if live() == null: return
	app.session.command({"type": "expedition_cheat_zone"})
	await wait_for(func(): return strike() != null, 360)
