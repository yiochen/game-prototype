extends SceneTree
## #29 native review captures: the while-away cue (short and long amounts,
## zero suppressed, reduced motion) over the restored restaurant, and the
## new-stock dot on Edit, on the Shop action and cleared inside Shop.
##   python3 tools/test_native.py --script tests/capture_away.gd --visible --resolution 390x844 --output review/29/native/phone

const Session = preload("res://scripts/session.gd")
var app
var destination := ""

func _initialize() -> void: call_deferred("run")

func settle(seconds: float) -> void:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end: await process_frame

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name + ".png"))
	print("captured " + name)

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	if app.performance_overlay != null: app.performance_overlay.hide()
	app.session = Session.new_session(29, {"starting_coins": 1240})
	for i in range(300): app.session.advance(0.1)
	app.session._state.shop.fresh = true
	app._refresh(); app._layout()
	app._present_away(420)
	await settle(1.2)
	await capture("01-return-short-cue-dot")
	app.away_notice.hide()
	app._present_away(1284093)
	await settle(1.2)
	await capture("02-long-cue")
	app.away_notice.hide()
	app._present_away(0)
	await settle(0.6)
	await capture("03-zero-suppressed")
	app.world.reduced_motion = true
	app._present_away(87)
	await settle(0.1)
	await capture("04-reduced-motion-cue")
	app.away_notice.hide()
	app.world.reduced_motion = false
	app.dispatch({"type": "set_mode", "mode": "edit"})
	app._refresh()
	await settle(0.6)
	await capture("05-edit-shop-dot")
	app._open_shop()
	await settle(0.8)
	await capture("06-shop-entered-dot-cleared")
	quit()
