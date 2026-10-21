extends SceneTree
const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
var app
var destination := ""
var screens: Array = []

func _init() -> void:
	call_deferred("run")

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty(): quit(1); return
	var requested := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	root.size = Vector2i(int(requested[0]), int(requested[1]))
	app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	app.session = Session.new_session(41)
	app._layout()
	app._refresh()
	await capture("01-live-sky")
	app._editor_command({"type":"set_mode","mode":"edit"})
	await capture("02-edit-sky")
	app._layout_for_safe_top(180.0)
	await capture("03-large-camera-clearance")
	var report := FileAccess.open(destination.path_join("manifest.json"), FileAccess.WRITE)
	report.store_string(JSON.stringify(screens,"\t"))
	report.close()
	app.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	print("Captured three actual sky and camera-clearance screens")
	quit(0)

func capture(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image.save_png(destination.path_join(name+".png")) != OK: quit(1); return
	screens.append({"name":name,"pixels":[image.get_width(),image.get_height()],"sky_height":app.world.sky_height,"safe_top":app.world.safe_top,"hud_top":app.coin_panel.position.y,"floor_origin":[app.world.floor_origin.x,app.world.floor_origin.y]})
