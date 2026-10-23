extends SceneTree
var app
func _initialize() -> void: call_deferred("run")
func settle() -> void:
	for i in range(90): await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	var output := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	assert(not output.is_empty())
	assert(str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"))
	app = load("res://main.tscn").instantiate()
	root.add_child(app)
	app.audio.set_muted(true)
	for dimensions in [Vector2i(390,844), Vector2i(720,1280), Vector2i(844,390)]:
		root.size = dimensions
		await settle()
		var overlay = app.performance_overlay
		assert(overlay.mouse_filter == Control.MOUSE_FILTER_IGNORE)
		assert(overlay.focus_mode == Control.FOCUS_NONE)
		assert(overlay.statistics().fps > 0)
		assert(overlay.get_global_rect().end.y <= app.coin_panel.get_global_rect().position.y)
		root.get_texture().get_image().save_png(output.path_join("overlay-%dx%d.png" % [dimensions.x, dimensions.y]))
	app._layout_for_safe_top(30.0)
	await settle()
	assert(app.performance_overlay.position.y >= 30)
	assert(app.performance_overlay.get_global_rect().end.y <= app.coin_panel.get_global_rect().position.y)
	print("Overlay visible, safe-area layout and touch pass-through checks passed: ", RenderingServer.get_current_rendering_method(), "/", RenderingServer.get_current_rendering_driver_name())
	app.queue_free()
	await process_frame
	quit()
