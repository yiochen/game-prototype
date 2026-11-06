extends SceneTree
## Native evidence for ship handling: banking into a turn, a rock hit (knock
## back, wobble, red flash, sparks) and the debug cheat buttons. Run through
## tools/test_native.py --visible with an output folder and `-- --cheats`.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const Cheats = preload("res://scripts/cheats.gd")
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

func live() -> Dictionary: return app.session._state.expedition.run

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
	await create_timer(1.0).timeout
	check(Cheats.enabled() and ui.cheat_buttons.size() == 2 and ui.cheat_buttons.all(func(b): return b.visible), "the cheats flag shows the debug buttons")

	# Banking: hold right.
	app.session.command({"type": "expedition_steer", "input": 1.0})
	await create_timer(0.35).timeout
	check(ui.view._tilt > 0.15, "steering right banks the ship right (%.2f)" % ui.view._tilt)
	await capture("01-bank-right")
	app.session.command({"type": "expedition_steer", "input": -1.0})
	await create_timer(0.5).timeout
	check(ui.view._tilt < -0.15, "steering left banks it left")
	await capture("02-bank-left")
	app.session.command({"type": "expedition_steer", "input": 0.0})

	# A rock hit: stage the ship just south of a rock face.
	var rows: Array = Book.run_route(live()).rows
	var y0 := int(float(live().y)) - 4
	var rock := Vector2(-1, -1)
	for ry in range(y0, y0 - 40, -1):
		for rx in range(2, 9):
			if Route.is_rock(str(rows[ry])[rx]) and not Route.is_rock(str(rows[ry + 1])[rx]): rock = Vector2(rx + .5, ry + .5); break
		if rock.x > 0: break
	var r := live(); r.x = rock.x; r.y = rock.y + 1.05; r.vx = 0.0; r.protection = 0.0
	ui.view.snap_camera()
	var hull := float(r.hull)
	await create_timer(0.3).timeout
	check(float(live().hull) < hull, "the ship runs into the rock and takes damage")
	check(ui.view._hurt > 0.3, "the damage animation plays")
	await capture("03-hit")
	await create_timer(0.25).timeout
	await capture("04-hit-recovering")

	# Cheats: shield now, then skip to the eel.
	ui.cheat_shield()
	await create_timer(0.3).timeout
	check(float(live().shield) > 0.0, "the Shield cheat raises the shield")
	await capture("05-cheat-shield")
	ui.cheat_encounter()
	await create_timer(3.0).timeout
	check(live().encounter is Dictionary and live().encounter.state == "aiming", "the To Eel cheat reaches the encounter")
	await capture("06-cheat-encounter")
	print("Expedition handling captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
