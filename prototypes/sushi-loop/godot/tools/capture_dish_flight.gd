extends SceneTree
var app
var destination := ""
func _initialize() -> void: call_deferred("run")
func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty() or not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopRecipePreview"):
		printerr("An isolated recipe preview and capture directory are required.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.show_editor_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	await process_frame
	app.set_process(false)
	app.session = app.Session.new_session(55)
	app.session.command({"type":"set_mode","mode":"live"})
	app._refresh()
	var found := false
	for step in range(1800):
		app.advance_time(0.05)
		if not app.world.dish_flights.is_empty():
			found = true
			break
		await process_frame
	if not found:
		printerr("No dish handoff was reached")
		quit(1)
		return
	print("FLIGHT "+str(app.world.dish_flights))
	await capture("01-source")
	app.advance_time(0.12)
	await capture("02-midpoint")
	app.advance_time(0.13)
	await capture("03-landing")
	app.advance_time(0.10)
	await capture("04-held")
	print("Renderer: "+RenderingServer.get_current_rendering_method()+" / "+RenderingServer.get_current_rendering_driver_name())
	app.queue_free()
	await process_frame
	quit()
func capture(label: String) -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(label+".png"))
	print("Rendered "+label)
