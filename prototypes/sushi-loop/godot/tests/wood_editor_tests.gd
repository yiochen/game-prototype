extends SceneTree
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var sizes := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if sizes.size()==2: root.size=Vector2i(int(sizes[0]),int(sizes[1]))
	var app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	app.audio.set_muted(true)
	await process_frame
	var suite = load("res://tests/wood_editor_checks.gd").new()
	await suite.run(app,self,OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT"))
	for failure in suite.failures: printerr("FAIL: "+failure)
	print("Wood editor: %s checks, %s failures" % [suite.checks,suite.failures.size()])
	var result := 0 if suite.failures.is_empty() else 1
	suite = null
	app.queue_free()
	app = null
	await process_frame
	await create_timer(0.1).timeout
	quit(result)
