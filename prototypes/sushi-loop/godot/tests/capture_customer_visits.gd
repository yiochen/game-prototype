extends SceneTree
## Capture the real demonstration through public elapsed-time simulation only.

const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app
var destination := ""
var manifest: Array = []
var observed: Dictionary = {}
var due: Dictionary = {}
var events_seen: Array = []
var sales_by_visitor: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("A capture output directory is required.")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(destination)
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	app._refresh()
	await capture("01-two-menu-restaurant", {})
	for step in range(3600):
		var events: Array = app.advance_time(0.05)
		var scene: Dictionary = app.session.snapshot()
		for event in events:
			events_seen.append({"elapsed": scene.elapsed, "event": event})
			match event.type:
				"preference_matched": schedule("03-preference-happy", scene, event)
				"preference_expired": schedule("04-preference-expired", scene, event)
				"customer_restless": schedule("05-restless-wait", scene, event)
				"visit_abandoned": schedule("06-unfed-leaving", scene, event)
				"sale":
					var count := int(sales_by_visitor.get(event.customer_id, 0)) + 1
					sales_by_visitor[event.customer_id] = count
					if count >= 2:
						schedule("07-second-dish-same-visit", scene, event)
		for customer in scene.customers:
			if customer.get("preference_phase") == "active":
				schedule("02-preference-and-timer", scene, {"customer_id": customer.id})
			if customer.get("yielding", false):
				schedule("08-yielding-in-aisle", scene, {"customer_id": customer.id})
			if absf(float(customer.get("render_offset_x", 0.0))) + absf(float(customer.get("render_offset_y", 0.0))) > 0.05:
				schedule("09-passing-in-aisle", scene, {"customer_id": customer.id})
		for name in due.keys():
			if float(scene.elapsed) + 0.000001 >= float(due[name].time):
				await capture(name, due[name].trigger)
				due.erase(name)
		if observed.size() == 8 and due.is_empty():
			break
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	app._refresh()
	await capture("10-sustained-live-service", {})
	app.queue_free()
	await process_frame
	app = APP.instantiate()
	app.show_gallery = true
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	await capture("11-shared-reactions", {})
	var file := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"screens": manifest, "observed": observed, "events": events_seen}, "\t"))
	file.close()
	print("Captured %s native customer-visit screens; observed: %s" % [manifest.size(), observed.keys()])
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	quit(0)

func schedule(name: String, scene: Dictionary, trigger: Dictionary) -> void:
	if observed.has(name):
		return
	observed[name] = scene.elapsed
	due[name] = {"time": float(scene.elapsed) + 0.25, "trigger": trigger.duplicate(true)}

func capture(name: String, trigger: Dictionary) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var status := image.save_png(destination.path_join(name + ".png"))
	if status != OK:
		push_error("Could not save capture: " + name)
	manifest.append({"name": name, "trigger": trigger, "pixels": [image.get_width(), image.get_height()], "canvas": [app.size.x, app.size.y], "portrait": [app.world.portrait.position.x, app.world.portrait.size.x, app.world.portrait.size.y], "cell_pitch": app.world.cell, "session": app.session.snapshot()})
