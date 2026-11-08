extends SceneTree
## #61 preview: live backdrop plus per-depth sprite layers so HTML cash piles sort between rows.
## Copy to godot/tests/, then: python3 godot/tools/test_native.py --script tests/capture_cash_layers.gd --visible --resolution 780x1688 --output <dir>

const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app
var destination := ""

func _initialize() -> void:
	call_deferred("run")

func shot() -> Image:
	app.world.queue_redraw()
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func show_state(scene: Dictionary) -> void:
	app.world.state = scene

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	app._refresh()
	for step in range(900):
		app.advance_time(0.05)
	app._refresh()
	for node in [app.coin_panel, app.coin, app.money, app.performance_overlay]:
		if node != null: node.visible = false
	var scene: Dictionary = app.session.snapshot()
	var full: Image = await shot()
	full.save_png(destination.path_join("restaurant-live.png"))
	app.set_process(false)
	app.world.ground_shadows_enabled = false
	var empty := scene.duplicate(true)
	empty.objects = []
	empty.customers = []
	show_state(empty)
	var bare: Image = await shot()
	var buckets := {}
	for object in scene.objects:
		buckets[int(ceil(float(object.y) - 0.001))] = true
	for customer in scene.customers:
		buckets[int(ceil(float(customer.y) + float(customer.get("render_offset_y", 0)) - 0.001))] = true
	var layers := []
	for bucket in buckets.keys():
		var only := scene.duplicate(true)
		only.objects = scene.objects.filter(func(o): return int(ceil(float(o.y) - 0.001)) == bucket)
		only.customers = scene.customers.filter(func(c): return int(ceil(float(c.y) + float(c.get("render_offset_y", 0)) - 0.001)) == bucket)
		show_state(only)
		var image: Image = await shot()
		var layer := Image.create(image.get_width(), image.get_height(), false, Image.FORMAT_RGBA8)
		var a := image.get_data()
		var b := bare.get_data()
		var stride := 4 if image.get_format() == Image.FORMAT_RGBA8 else 3
		var out := PackedByteArray()
		out.resize(image.get_width() * image.get_height() * 4)
		var i := 0
		var o := 0
		while i < a.size():
			var d: int = absi(a[i] - b[i]) + absi(a[i + 1] - b[i + 1]) + absi(a[i + 2] - b[i + 2])
			if d > 18:
				out[o] = a[i]; out[o + 1] = a[i + 1]; out[o + 2] = a[i + 2]; out[o + 3] = 255
			i += stride
			o += 4
		layer.set_data(image.get_width(), image.get_height(), false, Image.FORMAT_RGBA8, out)
		var name := "row-%02d.png" % bucket
		layer.save_png(destination.path_join(name))
		layers.append({"depth": bucket, "file": name})
	var origin: Vector2 = app.world.cell_base(0, 0)
	var info := {"pixels": [full.get_width(), full.get_height()], "canvas": [app.size.x, app.size.y], "cell": app.world.cell, "cell0_center": [origin.x, origin.y], "layers": layers, "objects": scene.objects, "customers": scene.customers, "floor": scene.floor}
	var file := FileAccess.open(destination.path_join("restaurant-live.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(info, "\t"))
	file.close()
	app.queue_free()
	await process_frame
	quit(0)
