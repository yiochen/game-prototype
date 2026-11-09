extends SceneTree
## #28 native evidence: the Edit inventory dock on the shared tab control.
##   python3 tools/test_native.py --script tests/capture_edit_tabs.gd --visible --resolution 780x1688 --output <dir>
const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app

func _initialize() -> void: call_deferred("run")

func shot(name: String) -> void:
	for i in range(6): await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT").path_join(name + ".png"))
	print("CAPTURED ", name)

func run() -> void:
	app = APP.instantiate(); app.simulation_enabled = false; root.add_child(app)
	await process_frame
	app.session = Session.new_session(7)
	app.performance_overlay.visible = false
	app._editor_command({"type": "set_mode", "mode": "edit"})
	for layer in ["layout", "people", "floor"]:
		app._editor_command({"type": "editor_layer", "layer": layer})
		app._refresh(); app._layout()
		await shot("edit-" + layer)
	quit(0)
