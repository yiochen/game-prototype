extends SceneTree
## Sixty seconds of actual service, sampled at the source animation's 12 fps.

const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("A customer-motion output directory is required.")
		quit(1)
		return
	var app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	var events: Array = []
	for frame in range(720):
		events.append_array(app.advance_time(1.0 / 12.0))
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(destination.path_join("frame_%03d.png" % frame))
	var file := FileAccess.open(destination.path_join("motion.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"frames": 720, "fps": 12, "seconds": 60, "events": events, "final_state": app.session.snapshot()}, "\t"))
	file.close()
	print("Captured sixty seconds of real customer service at twelve frames per second.")
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)
