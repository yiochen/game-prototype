extends SceneTree
## Current wood-dock captures; run through tools/test_native.py for isolated saves.
var app
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty() or not str(ProjectSettings.get_setting("application/config/custom_user_dir_name","")).begins_with("SushiLoopTicketsTest-"):
		printerr("Use test_native.py with --output for isolated editor captures.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dimensions.size()==2: root.size = Vector2i(int(dimensions[0]),int(dimensions[1]))
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	app.audio.set_muted(true)
	await process_frame
	var suite = load("res://tests/wood_editor_checks.gd").new()
	await suite.run(app,self,destination)
	for failure in suite.failures: printerr("FAIL: "+failure)
	var result := 0 if suite.failures.is_empty() else 1
	var checks: int = suite.checks
	suite = null
	app.queue_free()
	await process_frame
	app = load("res://main.tscn").instantiate()
	app.show_editor_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	app.audio.set_muted(true)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join("07-shared-editor-gallery.png"))
	var file := FileAccess.open(destination.path_join("capture-report.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"status":"PASS" if result==0 else "FAIL","window":[root.size.x,root.size.y],"shared_editor_script":str(app.editor_ui.get_script().resource_path)},"\t"))
	file.close()
	app.queue_free()
	app = null
	await process_frame
	await create_timer(0.2).timeout
	print("Captured current native wood editor and shared gallery: %s checks" % checks)
	quit(result)
