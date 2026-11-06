extends SceneTree
## Native issue #24 evidence from the real game: the hooked chase through
## route terrain (live arrows, draining resistance, speed streaks), a hit, the
## catch cutscene with the harpoon reeled home, the recipe award, the results
## and the NEW recipe in a chef's picker; then a second dive whose hull gives
## out mid-chase (the cable snaps, the eel escapes). Run through
## tools/test_native.py --visible with an output folder.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
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

func live() -> Variant: return app.session._state.expedition.run
func play(seconds: float) -> void: await create_timer(seconds).timeout

## Dive, jump to the arena, hook the creature (real button press).
func hook() -> void:
	var ui = app.expedition_ui
	app._open_landmark("Submarine"); ui.start()
	var r: Dictionary = live()
	r.y = float(Book.run_route(r).encounter_start) + 1.2; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state)}, 0.0); ui.view.snap_camera()
	await play(2.2)
	live().x = Book.creature_centre(live()).x; live().vx = 0.0
	ui.fire()
	var guard := 0
	while live().encounter.state != "hooked" and guard < 400: await process_frame; guard += 1

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = revealed_session(24); app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui
	var recipe := str(Book.definition().encounter.recipe)
	check(not recipe in app.session._state.recipe_book.discovered, "the eel roll starts undiscovered")

	await hook()
	check(live().encounter.state == "hooked", "the harpoon hooks the creature")
	await play(0.5)
	await capture("01-hooked")
	await play(1.2)
	check(not ui.view.controls_disabled and not ui.harpoon_button.visible, "the chase keeps the arrows live and hides the Harpoon")
	check(Book.pursuit_speed(live()) > 1.3, "ship and creature speed up together")
	app.session.command({"type": "expedition_steer", "input": 1.0})
	await play(0.4)
	await capture("02-chase-steering")
	app.session.command({"type": "expedition_steer", "input": 0.0})
	# Low resistance: amber bar, thrashing eel.
	live().encounter.resistance = 20.0
	await play(0.6)
	check(ui.view.creature.clip == "struggle", "low resistance makes the creature thrash")
	await capture("03-chase-low-resistance")

	# The catch: the rules commit it, then the cutscene plays.
	live().encounter.resistance = 0.4
	var guard := 0
	while ui.overlay != "outro" and guard < 200: await process_frame; guard += 1
	check(ui.overlay == "outro" and recipe in app.session._state.recipe_book.discovered and live() == null, "zero resistance commits the catch and discovery before the cutscene")
	await play(0.3)
	await capture("04-caught")
	await play(0.6)
	await capture("05-harpoon-reeling-home")
	await play(0.9)
	await capture("06-cutscene")
	guard = 0
	while ui.overlay != "award" and guard < 400: await process_frame; guard += 1
	check(ui.overlay == "award" and ui.cards.award.panel.visible, "the cutscene opens the recipe award by itself")
	check(ui.award.name.text == "Eel roll" and ui.award.chips[0].value.text == "48" and ui.award.chips[1].value.text == "7.5 sec", "the award shows the recipe's name, price and base prep")
	await play(0.3)
	await capture("07-award")
	ui._award_continue()
	await play(0.2)
	check(ui.mode == "results" and ui.result.outcome == "complete" and int(ui.result.bonus) > 0, "Continue opens the complete results with the bonus")
	await capture("08-results")
	ui.finish_results()
	await play(0.3)
	check(recipe in app.session._state.recipe_book.new, "back at the restaurant the recipe is NEW")
	var chef := str(app.session.snapshot().objects.filter(func(c): return c.kind == "chef")[0].id)
	app._open_recipes(chef)
	await play(0.4)
	await capture("09-restaurant-new-recipe")
	app.recipe_ui.dismiss()
	await play(0.2)

	# Second dive: the hull gives out mid-chase.
	app.session._state.expedition.charge = {"ready": true, "recharge_started": null}
	await hook()
	await play(1.0)
	live().hull = float(Book.definition().impact_damage); live().protection = 0.0
	var rows: Array = Book.run_route(live()).rows
	var rock := Vector2(-1, -1)
	for ry in range(int(live().y) - 2, maxi(1, int(live().y) - 120), -1):
		for rx in range(1, 10):
			if Route.is_rock(str(rows[ry])[rx]) and not Route.is_rock(str(rows[ry + 1])[rx]): rock = Vector2(rx + .5, ry + .5); break
		if rock.x > 0: break
	check(rock.x > 0, "a rock lies ahead in the pursuit terrain")
	live().x = rock.x; live().y = rock.y + .6
	guard = 0
	while ui.overlay != "outro" and guard < 200: await process_frame; guard += 1
	check(ui.overlay == "outro", "zero hull mid-chase plays the escape")
	await play(0.35)
	await capture("10-escape-cable-snaps")
	guard = 0
	while ui.mode != "results" and guard < 400: await process_frame; guard += 1
	check(ui.mode == "results" and ui.result.outcome == "hull_depleted" and ui.result.creature.outcome == "escaped", "the escape ends in Hull depleted results, no recipe")
	await play(0.2)
	await capture("11-results-hull-depleted")
	print("Expedition pursuit captures: %d failures" % failures.size())
	quit(1 if failures.size() else 0)
