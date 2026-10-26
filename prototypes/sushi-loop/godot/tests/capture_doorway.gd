extends SceneTree
const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var manifest: Array = []
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty(): quit(1); return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	var capture_seed := int(OS.get_environment("SUSHI_LOOP_CAPTURE_SEED")) if not OS.get_environment("SUSHI_LOOP_CAPTURE_SEED").is_empty() else 41
	app.session = Session.new_session(capture_seed, {"objects": [], "service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0}})
	app._refresh()
	for stage in [[0.1,"01-dark-spawn"], [0.15,"02-behind-curtain"], [0.25,"03-front-of-curtain"], [0.6,"04-inside"], [4.6,"05-leaving"], [4.8,"06-returning-to-dark"], [5.0,"07-behind-curtain-exit"], [5.1,"08-removed-in-dark"]]:
		app.advance_time(float(stage[0]) - float(app.session.snapshot().elapsed))
		await capture(stage[1])
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(manifest,"\t"))
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)
func capture(label: String) -> void:
	for frame in range(4): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(label + ".png"))
	manifest.append({"name": label, "snapshot": app.session.snapshot()})
