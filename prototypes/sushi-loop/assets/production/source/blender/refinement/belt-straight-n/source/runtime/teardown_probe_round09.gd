extends SceneTree
const Session = preload("res://scripts/session.gd")
var records: Array = []
var watches: Array = []
func _initialize() -> void:
	call_deferred("run")
func track(value: Object, label: String) -> void:
	if value != null: watches.append({"ref": weakref(value), "label": label, "class": value.get_class(), "id": value.get_instance_id()})
func track_tree(node: Node, label: String) -> void:
	track(node, label)
	for child in node.get_children(): track_tree(child, label + "/" + str(child.name))
func track_helper(app: Control) -> void:
	track_tree(app.world._native_world_layer, "helper")
	var layer: Node = app.world._native_world_layer
	var pipe: Node = layer.native_pipeline
	track(layer.native_view.font, "clone/font")
	track(layer.native_view.heading, "clone/heading")
	track(layer.get_script(), "helper/script")
	track(pipe.get_script(), "pipeline/script")
	track(layer.surface.get_script(), "surface/script")
	track(pipe.reduction_canvases[0].get_script(), "reduction/script")
	track(pipe.presentation_material, "pipeline/presentation_material")
	track(pipe.native_viewport.get_texture(), "pipeline/native_texture")
	for index in range(pipe.reduction_viewports.size()):
		track(pipe.reduction_viewports[index].get_texture(), "pipeline/mip_texture%d" % index)
		track(pipe.reduction_canvases[index].material, "pipeline/reduction_material%d" % index)
	for key in pipe._belt_textures: track(pipe._belt_textures[key], "pipeline/belt_wrapper")
func run() -> void:
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	for cycle in range(4):
		for gallery in [false, true]:
			var app: Control = load("res://main.tscn").instantiate()
			app.show_gallery = gallery
			app.simulation_enabled = false
			root.add_child(app)
			await process_frame
			app.session = Session.new_session(41)
			app._refresh()
			await process_frame
			await RenderingServer.frame_post_draw
			watches.clear()
			track_helper(app)
			app.queue_free()
			await process_frame
			await create_timer(0.1).timeout
			await process_frame
			var survivors: Array = []
			for item in watches:
				if item.ref.get_ref() != null:
					survivors.append({"label": item.label, "class": item.class, "id": item.id})
			records.append({"cycle": cycle, "gallery": gallery, "tracked": watches.size(), "survivors": survivors, "orphan_node_count": Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)})
			print("TEARDOWN ", records[-1])
	var file := FileAccess.open(destination.path_join("ownership.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(records, "  "))
	file.close()
	quit(0)
