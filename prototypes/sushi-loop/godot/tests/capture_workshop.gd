extends SceneTree
## #28 native evidence: restaurant dock (outlined ship and hut), the iris into
## the Workshop, both tabs, an upgrade (NEW look, test-fire), leaving through
## the doorway, and the dive with gear. Not part of the default suite.
##   python3 tools/test_native.py --script tests/capture_workshop.gd --visible --resolution 780x1688 --output <dir>
const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
const ExpeditionBook = preload("res://scripts/expedition/expedition_book.gd")
var app
var out := ""

func _initialize() -> void: call_deferred("run")

func wait(seconds: float) -> void:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < seconds * 1000.0: await process_frame

func shot(name: String) -> void:
	await process_frame; await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out.path_join(name + ".png"))
	print("CAPTURED ", name)

func run() -> void:
	out = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(out)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(19, {"starting_coins": 9180})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]:
		app.session.command({"type":"clear_trash","id":identity})
	app.session.command({"type":"reveal_dock"})
	app.session.command({"type":"set_camera","x":4,"y":0})
	app.session._state.expedition.salvage = 420
	app.performance_overlay.visible = false
	app._refresh(); app._layout()
	await wait(.6)
	await shot("01-restaurant-dock")
	app._open_landmark("Workshop")
	await wait(.12)
	await shot("02-iris-closing")
	while not app.transition._loading: await process_frame
	await wait(.1)
	await shot("03-loading")
	await wait(1.0)
	await shot("04-workshop-equipment")
	# Upgrade Hull twice: the second crosses the Lv 3 look (NEW + new hull sprite).
	app.workshop_ui._request("hull")
	await wait(.2)
	app.workshop_ui._request("hull")
	await wait(.5)
	await shot("05-hull-lv3-new-look")
	app.workshop_ui._request("harpoon")
	await wait(.35)
	await shot("06-harpoon-test-fire")
	app.workshop_ui.select_group("powerup")
	await wait(.3)
	await shot("07-workshop-powerups")
	app.session._state.expedition.salvage = 10
	app._refresh()
	await wait(.2)
	await shot("08-not-enough-salvage")
	app.workshop_ui.leave()
	await wait(1.6)
	await shot("09-back-on-dock")
	# Dive with gear: violet shield (Lv 3), launch shield, a portal and a shield pickup ahead.
	app.session._state.expedition.salvage = 2000
	for id in ["shield", "shield", "passage", "passage", "launch", "collector", "collector"]:
		var level: int = app.session.snapshot().workshop.tracks.filter(func(t): return t.id == id)[0].level
		app.session.command({"type": "workshop_upgrade", "id": id, "token": "%s:%d" % [id, level]})
	app._refresh()
	app._open_landmark("Submarine")
	await wait(2.0)
	await shot("10-dive-prep")
	app.expedition_ui.start()
	await wait(.6)
	await shot("11-dive-launch-shield")
	var run: Dictionary = app.session._state.expedition.run
	var path := ExpeditionBook.run_route(run)
	var portal: Dictionary = path.portals[0]
	run.x = float(portal.x); run.y = float(portal.y) + 4.0
	await wait(.4)
	await shot("12-dive-portal-signal")
	if not path.shields.is_empty():
		var b: Vector2 = path.shields[0]
		run.x = b.x + 1.5; run.y = b.y + 3.5
		await wait(.3)
		await shot("13-dive-shield-pickup")
	print("levels ", app.session.snapshot().workshop.tracks.map(func(t): return [t.id, t.level]))
	quit(0)
