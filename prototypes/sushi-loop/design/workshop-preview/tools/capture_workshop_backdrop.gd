extends SceneTree
## #28 preview: clean Live restaurant with the dock revealed, plus the dock sprite geometry.
## Copy to godot/tests/, then: python3 godot/tools/test_native.py --script tests/capture_workshop_backdrop.gd --visible --resolution 780x1688 --output <dir>

const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app

func _initialize() -> void:
	call_deferred("run")

func shot() -> Image:
	app.world.queue_redraw()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(19, {"starting_coins": 9180})
	for identity in ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]:
		app.session.command({"type":"clear_trash","id":identity})
	app.session.command({"type":"reveal_dock"})
	app.session.command({"type":"set_camera","x":4,"y":0})
	app._refresh()
	for step in range(600):
		app.advance_time(0.05)
	app._refresh()
	app._layout()
	app.set_process(false)
	for node in [app.odometer, app.coin_panel, app.coin, app.money, app.performance_overlay, app.edit, app.shop, app.editing_panel, app.editing_cue, app.editing_icon]:
		if node != null: node.visible = false
	var full: Image = await shot()
	full.save_png(destination.path_join("restaurant-dock.png"))
	# #28 r3: the layered ImageGen ship replaces the 3D sprite, so also capture the deck without it.
	for view in [app.world] + ([app.world._native_world_controller] if app.world.get("_native_world_controller") != null else []):
		var book = view.get("art")
		if book == null: continue
		var record: Dictionary = book._clip_record("submarine-yellow", "static", "S")
		if record.is_empty(): continue
		book.frame_data("submarine-yellow", "static", "S")
		var blank := Image.create(book.sources[record.path].get_width(), book.sources[record.path].get_height(), false, Image.FORMAT_RGBA8)
		book.sources[record.path] = ImageTexture.create_from_image(blank)
	app.world.ground_shadows_enabled = false
	(await shot()).save_png(destination.path_join("restaurant-dock-empty.png"))
	app.world.ground_shadows_enabled = true
	var report := {"viewport": [full.get_width(), full.get_height()], "cell": app.world.cell, "floor_origin": [app.world.floor_origin.x, app.world.floor_origin.y], "props": {}}
	for entry in app.world._decor_plan():
		if entry.get("key") in ["submarine-yellow", "workshop-hut", "dock-floor"]:
			var rect: Rect2 = app.world.art.registered_rect(entry.key, entry.base, app.world.cell, entry.clip, entry.direction) if app.world.get("art") != null else Rect2()
			report.props[entry.key] = {"base": [entry.base.x, entry.base.y], "rect": [rect.position.x, rect.position.y, rect.size.x, rect.size.y], "clip": entry.clip}
	var file := FileAccess.open(destination.path_join("restaurant-dock.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("CAPTURED ", JSON.stringify(report))
	quit(0)
