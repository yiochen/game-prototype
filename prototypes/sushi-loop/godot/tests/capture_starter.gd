extends SceneTree

const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var manifest: Array = []

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("A capture output directory is required.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	app._refresh()
	await capture("01-starter")
	for stage in [[2.0, "02-walking"], [8.0, "03-eating"], [24.0, "04-live-service"]]:
		while float(app.session.snapshot().elapsed) < float(stage[0]) - 0.001:
			app.advance_time(0.05)
		await capture(str(stage[1]))
	app.session = Session.new_session(41)
	app.session.command({"type": "set_entrance_open", "open": false})
	for _step in range(600):
		app.advance_time(0.05)
	await capture("05-full-open-belt-held-food")
	app.session.command({"type": "set_camera", "x": 9.0, "y": 0.0})
	app._refresh()
	await capture("06-continuous-room")
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	app = load("res://main.tscn").instantiate()
	app.show_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	await capture("07-shared-components")
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest, "\t"))
	file.close()
	print("Captured %s actual native screens in %s" % [manifest.size(), destination])
	app.queue_free()
	await process_frame
	# Audio playback references are released on the asynchronous mixer thread.
	await create_timer(0.1).timeout
	await process_frame
	quit(0)

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var status := image.save_png(destination.path_join(name + ".png"))
	if status != OK:
		push_error("Could not save capture: " + name)
	manifest.append({"name": name, "pixels": [image.get_width(), image.get_height()], "canvas": [app.size.x, app.size.y], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "cell_pitch": app.world.cell, "session": app.session.snapshot()})
