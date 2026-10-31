extends SceneTree
var app
func _init() -> void: call_deferred("run")
func run() -> void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"): quit(1);return
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size() == 2: root.size = Vector2i(int(dimensions[0]),int(dimensions[1]))
	app = load("res://main.tscn").instantiate();root.add_child(app)
	for i in range(4): await process_frame
	var passed: bool = app.show_exhibition_gallery and app.show_gallery and app.clearance_ui.visible and app.clearance_ui.unlock_popup and app.clearance_ui.gallery and app.session.snapshot().expansion.dock_open
	var output := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty() and DisplayServer.get_name() != "headless":
		DirAccess.make_dir_recursive_absolute(output);await RenderingServer.frame_post_draw
		passed = root.get_texture().get_image().save_png(output.path_join("gallery.png")) == OK and passed
	app.audio.set_muted(true);app.audio._music.stop();app.queue_free()
	for i in range(3): await process_frame
	print("Exhibition gallery entry: "+("PASS" if passed else "FAIL"));quit(0 if passed else 1)
