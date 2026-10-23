extends SceneTree
## Native GPU A/B evidence in an isolated save, using the same paused session.
const Session = preload("res://scripts/session.gd")
const GroundShadows = preload("res://scripts/ground_shadows.gd")
var app
var destination := ""

func _initialize() -> void:
	call_deferred("run")

func frames() -> void:
	for _index in range(6): await process_frame
	await RenderingServer.frame_post_draw

func capture(name: String) -> Image:
	await frames()
	var image := root.get_texture().get_image()
	image.save_png(destination.path_join(name + ".png"))
	return image

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty() or not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Use tools/test_native.py --visible --output for isolated GPU captures.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	var renderer := RenderingServer.get_current_rendering_method()
	var driver := RenderingServer.get_current_rendering_driver_name()
	if renderer != "mobile" or (OS.get_name() == "Android" and driver != "vulkan"):
		printerr("FAIL: expected Mobile renderer (Vulkan on Android), got %s / %s" % [renderer, driver])
		quit(1)
		return
	var renderer_report := FileAccess.open(destination.path_join("renderer.json"), FileAccess.WRITE)
	renderer_report.store_string(JSON.stringify({"platform": OS.get_name(), "renderer": renderer, "driver": driver, "android_driver": ProjectSettings.get_setting("rendering/rendering_device/driver.android"), "opengl_fallback": ProjectSettings.get_setting("rendering/rendering_device/fallback_to_opengl3")}, "\t"))
	renderer_report.close()
	print("GPU verification: %s / %s on %s" % [renderer, driver, OS.get_name()])
	await check_native_blackboard()
	var dimensions := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(dimensions[0]), int(dimensions[1]))
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	app.audio.set_muted(true)
	await process_frame
	app.session = Session.new_session(41)
	for _step in range(200): app.advance_time(0.05)
	app._refresh()
	await frames()
	var before: Dictionary = app.session.snapshot().duplicate(true)
	var before_hits: Array = app.world.sprite_hits()
	app.world.ground_shadows_enabled = false
	var baseline := await capture("01-live-before")
	app.world.ground_shadows_enabled = true
	var shadows := await capture("02-live-shadows")
	var after_hits: Array = app.world.sprite_hits()
	assert(before == app.session.snapshot(), "Rendering shadows must not advance the paused session")
	assert(before_hits.size() == after_hits.size(), "Shadows must not enter sprite picking records")
	for index in range(before_hits.size()):
		assert(before_hits[index].rect == after_hits[index].rect and before_hits[index].owner_id == after_hits[index].owner_id, "Shadows must preserve selection geometry and ownership")
	assert(baseline.get_data() != shadows.get_data(), "The native GPU output must include the shadows")
	# Isolate conveyors to catch a shadow pass that exists but is entirely hidden
	# beneath the raised deck. Inspect actual floor pixels beyond the end module.
	app.set_process(false)
	app.world.state = before.duplicate(true)
	app.world.state.customers = []
	app.world.state.objects = app.world.state.objects.filter(func(object): return object.kind == "belt")
	app.world.ground_shadows_enabled = false
	var belt_before := await capture("05-conveyors-before")
	app.world.ground_shadows_enabled = true
	var belt_after := await capture("06-conveyors-top-right")
	var to_screen: Transform2D = app.get_viewport_transform() * app.world.get_global_transform()
	var last_belt: Vector2 = app.world.cell_base(4, 6)
	var upper_right := Rect2(to_screen * (last_belt + Vector2(0.5, -0.6) * app.world.cell), to_screen.basis_xform(Vector2(0.65, 0.59) * app.world.cell))
	var darkened := 0
	for y in range(ceili(upper_right.position.y), floori(upper_right.end.y)):
		for x in range(ceili(upper_right.position.x), floori(upper_right.end.x)):
			if belt_before.get_pixel(x, y).r - belt_after.get_pixel(x, y).r > 0.015:
				darkened += 1
	assert(darkened > 15, "Conveyor shadow must visibly reach the floor to the upper right of its end module")
	print("PASS: %s visible upper-right conveyor shadow pixels" % darkened)
	app.set_process(true)
	app.session.command({"type": "set_mode", "mode": "edit"})
	app._refresh()
	await capture("03-edit-shadows")
	for window in [Vector2i(768, 1024), Vector2i(1280, 720)]:
		root.size = window
		await frames()
		await capture("04-edit-%sx%s" % [window.x, window.y])
	print("PASS: shadow GPU A/B, frozen session and unchanged selection geometry at %s" % root.size)
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)

func check_native_blackboard() -> void:
	# Real GPU regression: no shadow can originate left of the board's physical
	# footprint under a top-right light. The former flattened sprite broke this.
	var lighting := GroundShadows.new()
	root.add_child(lighting)
	lighting.begin(Vector2(640, 640), 128.0)
	lighting.add_caster("chef-blackboard", Vector2(320, 320), 128.0, "S")
	lighting.finish()
	await frames()
	var mask: Image = lighting.texture().get_image()
	lighting.lighting_viewport.get_texture().get_image().save_png(destination.path_join("07-blackboard-native-shadow-map.png"))
	var left_limit := floori((320.0 - 0.44 * 128.0) * GroundShadows.RESOLUTION)
	var left_artifact := 0
	var shadow_pixels := 0
	for y in range(mask.get_height()):
		for x in range(mask.get_width()):
			if mask.get_pixel(x, y).a > 0.03:
				shadow_pixels += 1
				if x < left_limit: left_artifact += 1
	if shadow_pixels < 20 or left_artifact > 0:
		printerr("FAIL: native blackboard shadow pixels=%s, pixels left of physical footprint=%s" % [shadow_pixels, left_artifact])
		quit(1)
		return
	var cached: Dictionary = lighting.diagnostics()
	for _index in range(6):
		lighting.begin(Vector2(640, 640), 128.0)
		lighting.add_caster("chef-blackboard", Vector2(320, 320), 128.0, "S")
		lighting.finish()
		await frames()
	assert(lighting.diagnostics().batch_uploads == cached.batch_uploads, "Unchanged geometry must not reupload instance buffers")
	assert(lighting.diagnostics().proxy_shapes_built == 1, "Repeated draws must reuse the same blackboard shape")
	# Changing the actual light, without moving any geometry, must move shadows.
	lighting.light.look_at_from_position(Vector3.ZERO, Vector3(-0.55, -1, -0.35))
	await frames()
	assert(mask.get_data() != lighting.texture().get_image().get_data(), "Native shadow output must respond to the DirectionalLight3D direction")
	# A shadow crossing the back edge of the floor must not paint the wall.
	lighting.begin(Vector2(640, 640), 128.0, 350.0)
	lighting.add_caster("chef-blackboard", Vector2(320, 320), 128.0, "S")
	lighting.finish()
	await frames()
	var clipped: Image = lighting.texture().get_image()
	for y in range(floori(350.0 * GroundShadows.RESOLUTION) - 1):
		for x in range(clipped.get_width()):
			assert(clipped.get_pixel(x, y).a < 0.01, "Native shadows must stop at the floor/wall boundary")
	lighting.begin(Vector2(640, 640), 128.0, 350.0)
	lighting.finish()
	await frames()
	var cleared: Image = lighting.texture().get_image()
	for y in range(cleared.get_height()):
		for x in range(cleared.get_width()):
			assert(cleared.get_pixel(x, y).a < 0.01, "Removing an object must clear its shadow")
	print("PASS: native DirectionalLight3D blackboard shadows, %s pixels, no left extrusion, responds to light direction" % shadow_pixels)
	lighting.queue_free()
	await process_frame
