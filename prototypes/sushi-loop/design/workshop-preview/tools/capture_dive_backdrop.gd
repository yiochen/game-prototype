extends SceneTree
## #28 preview: a live travelling expedition frame for the dive comparison.
## Copy to godot/tests/, then: python3 godot/tools/test_native.py --script tests/capture_dive_backdrop.gd --visible --resolution 780x1688 --output <dir>

const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(21)
	app.session.command({"type": "expedition_start", "now": 0.0, "seed": 21})
	for step in range(70): app.session.command({"type": "expedition_advance", "elapsed": 0.05, "now": 0.0})
	app._refresh()
	app.expedition_ui.resume_suspended(app.session.snapshot())
	app.expedition_ui.cards.paused.buttons[1].pressed.emit()
	var started := Time.get_ticks_msec()
	while Time.get_ticks_msec() - started < 5600: await process_frame
	app.performance_overlay.visible = false
	Engine.time_scale = 0.0  # freeze so both frames match
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join("dive.png"))
	# #28 r3: the same frame without the 3D ship (the HUD icon is already built).
	app.expedition_ui.view.pieces.objects.erase("submarine-yellow")
	app.expedition_ui.view.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join("dive-empty.png"))
	print("CAPTURED dive")
	quit(0)
