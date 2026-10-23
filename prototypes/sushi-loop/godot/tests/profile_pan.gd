extends SceneTree
## Isolated Mobile-renderer pan benchmark; desktop timings are not Android FPS.
const Session = preload("res://scripts/session.gd")
var app
var output := ""

func _initialize() -> void:
	call_deferred("run")

func frames(count := 6) -> void:
	for _index in range(count): await process_frame
	await RenderingServer.frame_post_draw

func summary(values: Array) -> Dictionary:
	values.sort()
	return {"median": values[values.size() / 2], "p95": values[mini(values.size() - 1, int(values.size() * 0.95))]}

func run() -> void:
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if output.is_empty() or not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Use test_native.py --visible --output for an isolated GPU benchmark")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	app.audio.set_muted(true)
	await frames()
	app.set_process(false)
	var pipeline = app.world._native_world_layer.native_pipeline
	var lighting = app.world._native_world_layer.native_view._ground_shadows
	var targets := {"native": pipeline.native_viewport, "shadow": lighting.lighting_viewport, "shadow_present": lighting.viewport}
	for viewport in targets.values(): RenderingServer.viewport_set_measure_render_time(viewport.get_viewport_rid(), true)
	var report := {"renderer": RenderingServer.get_current_rendering_method(), "driver": RenderingServer.get_current_rendering_driver_name(), "device": RenderingServer.get_video_adapter_name(), "window": [root.size.x, root.size.y], "gpu_timing_available": false, "cases": {}}
	var cpu_samples: Array = []
	for index in range(120):
		var start := Time.get_ticks_usec()
		app._process(1.0 / 60.0)
		cpu_samples.append(float(Time.get_ticks_usec() - start))
	report["main_loop_cpu_us"] = summary(cpu_samples)
	for mode in ["edit", "live"]:
		app.session = Session.new_session(41)
		for _step in range(200): app.advance_time(0.05)
		app.session.command({"type": "set_mode", "mode": mode})
		app.world.ground_shadows_enabled = true
		for frame in range(32):
			app.session.command({"type": "set_camera", "x": 14.0 * float(frame % 16) / 15.0, "y": 0.0})
			app._refresh()
			await frames(1)
		var times: Array = []
		var shadow_calls: Array = []
		var gpu := {"native": [], "shadow": [], "shadow_present": []}
		for frame in range(180):
			var start := Time.get_ticks_usec()
			app.session.command({"type": "set_camera", "x": 7.0 - 7.0 * cos(float(frame) / 179.0 * TAU), "y": 0.0})
			if mode == "live": app.advance_time(1.0 / 60.0)
			else: app._refresh()
			await frames(1)
			times.append(float(Time.get_ticks_usec() - start) / 1000.0)
			for name in targets:
				gpu[name].append(RenderingServer.viewport_get_measured_render_time_gpu(targets[name].get_viewport_rid()))
			shadow_calls.append(lighting.lighting_viewport.get_render_info(Viewport.RENDER_INFO_TYPE_SHADOW, Viewport.RENDER_INFO_DRAW_CALLS_IN_FRAME))
		var result := {"frame_wall_ms": summary(times), "shadow_draw_calls": summary(shadow_calls), "gpu_ms": {}}
		for name in gpu: result.gpu_ms[name] = summary(gpu[name])
		result["resident_atlases"] = app.world.art.sources.size()
		var texels := 0
		for texture in app.world.art.sources.values(): texels += texture.get_width() * texture.get_height()
		result["resident_atlas_texels"] = texels
		result["allocation"] = pipeline.allocation_record()
		result["active_reduction_levels"] = pipeline.active_reduction_levels
		if lighting.has_method("diagnostics"): result["shadow_counters"] = lighting.diagnostics()
		report.cases[mode] = result
		app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
		app._refresh()
		await frames()
		root.get_texture().get_image().save_png(output.path_join(mode + ".png"))
	var file := FileAccess.open(output.path_join("pan-profile.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print(JSON.stringify(report))
	app.queue_free()
	await frames()
	quit(0)
