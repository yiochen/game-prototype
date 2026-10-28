extends SceneTree
## Capture the real command-line Shared host, not a substitute popup.
func _initialize()->void:call_deferred("run")
func run()->void:
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):quit(1);return
	root.size=Vector2i(390,844)
	var app=load("res://main.tscn").instantiate();root.add_child(app)
	for i in range(6):await process_frame
	if not app.show_chef_gallery or not app.recipe_ui.visible or app.recipe_ui.tab!="manage":printerr("FAIL: Shared chef gallery did not open");quit(1);return
	var output:=OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty() and DisplayServer.get_name()!="headless":
		DirAccess.make_dir_recursive_absolute(output);await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(output.path_join("shared-chef-gallery.png"))
	app.queue_free();await process_frame
	print("PASS: production --chef-gallery host opens the shared Manage popup")
	quit()
