extends SceneTree
const BaselineView = preload("restaurant_view_baseline.gd")
const Session = preload("res://scripts/session.gd")
var records: Array[Dictionary] = []
var failures: Array[String] = []
var output := ""
var native_script: GDScript
func _initialize() -> void:
	call_deferred("run")
func target(dimensions: Vector2i) -> SubViewport:
	var viewport := SubViewport.new()
	viewport.size = dimensions
	viewport.disable_3d = true
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	return viewport
func check(value: bool, text: String) -> void:
	if not value: failures.append(text)
func fingerprint(view: Control) -> Array:
	var values: Array = []
	for item in view.sprite_hits():
		values.append([item.owner_id, item.art_id, item.clip, item.direction, item.frame, item.region, item.rect, item.tint])
	return values
func painter_fingerprint(view: Control) -> Array:
	var result: Array = []
	for item in view.render_plan():
		result.append([item.kind, item.depth, item.get("priority", 0), item.get("owner_id", ""), item.get("key", ""), item.get("value", {}).get("id", "")])
	return result
func run() -> void:
	output = OS.get_environment("BELT_RUNTIME_OUTPUT")
	DirAccess.make_dir_recursive_absolute(output)
	native_script = load(get_script().resource_path.get_base_dir().path_join("restaurant_view_native.gd"))
	var session = Session.new_session(41)
	session.advance(8.0)
	var snapshot: Dictionary = session.snapshot()
	for fixture in [{"name": "portrait", "size": Vector2i(720, 1280), "camera": Vector2.ZERO}, {"name": "landscape-pan", "size": Vector2i(1280, 720), "camera": Vector2(3.12345, 0.45678)}, {"name": "phone32-editor", "size": Vector2i(224, 400), "camera": Vector2(0.001953125, 0.001953125)}, {"name": "transformed", "size": Vector2i(720, 1280), "camera": Vector2(1.252, 0.312)}]:
		var before := target(fixture.size)
		var after := target(fixture.size)
		var baseline: Control = BaselineView.new()
		var native: Control = native_script.new()
		baseline.size = Vector2(fixture.size)
		native.size = Vector2(fixture.size)
		before.add_child(baseline)
		native.art = baseline.art
		after.add_child(native)
		var state: Dictionary = snapshot.duplicate(true)
		state.camera = {"x": fixture.camera.x, "y": fixture.camera.y}
		if fixture.name == "phone32-editor":
			state.mode = "edit"
			state.editor.selected_id = "chef-1"
		for view in [baseline, native]:
			view.state = state
			view.time = 8.25
			view.sale_pops = [{"x": 4, "y": 5, "time": 8.0}]
			view.safe_top = 18.0
			view.editor_selection_alpha = 0.7
			view.editor_preview = {"x": 2, "y": 7, "valid": true} if fixture.name == "phone32-editor" else {}
			view.update_layout()
			if fixture.name == "transformed":
				view.position = Vector2(17.0, 23.0)
				view.scale = Vector2(0.8, 0.8)
			view.queue_redraw()
		native._native_world_layer.sync()
		await process_frame
		await RenderingServer.frame_post_draw
		await process_frame
		await RenderingServer.frame_post_draw
		var a := fingerprint(baseline)
		var b := fingerprint(native)
		check(a == b, fixture.name + ": exact hit records/painter order differ")
		var pick_count := 0
		var mismatches := 0
		for y in range(0, fixture.size.y, 13):
			for x in range(0, fixture.size.x, 13):
				pick_count += 1
				if baseline.object_at(Vector2(x + .5, y + .5)).get("id", "") != native.object_at(Vector2(x + .5, y + .5)).get("id", ""): mismatches += 1
		check(mismatches == 0, fixture.name + ": picking differs")
		var layer: Node = native._native_world_layer
		var clone: Control = layer.native_view
		var anchor_error := 0.0
		for object in state.objects:
			var base: Vector2 = clone.cell_base(float(object.x), float(object.y))
			var corrected: Vector2 = base + layer.native_pipeline.native_viewport.canvas_transform.origin + layer.surface.native_offset
			var mapped: Vector2 = native.portrait.position + corrected * native.cell / 256.0
			anchor_error = maxf(anchor_error, mapped.distance_to(native.cell_base(float(object.x), float(object.y))))
		check(anchor_error < .001, fixture.name + ": source anchors drift")
		check(absf(clone.cell - 256.0) < .0001, fixture.name + ": native cell is not256")
		check(layer.surface.position == native.portrait.position and layer.surface.size == native.portrait.size, fixture.name + ": portrait crop changed")
		check(clone.sale_pops == native.sale_pops and clone.editor_preview == native.editor_preview and clone.editor_selection_alpha == native.editor_selection_alpha, fixture.name + ": world overlays lost")
		check(painter_fingerprint(clone) == painter_fingerprint(native), fixture.name + ": painter pass changed")
		assert(before.get_texture().get_image().save_png(output.path_join(fixture.name + "-baseline.png")) == OK)
		assert(after.get_texture().get_image().save_png(output.path_join(fixture.name + "-native-world.png")) == OK)
		records.append({"name": fixture.name, "source_size": [fixture.size.x, fixture.size.y], "pick_probes": pick_count, "pick_mismatches": mismatches, "hit_records_equal": a == b, "hit_records_count": a.size(), "anchor_max_pixel_error": anchor_error, "painter_order_equal": painter_fingerprint(clone) == painter_fingerprint(native), "overlays_equal": clone.sale_pops == native.sale_pops and clone.editor_preview == native.editor_preview, "allocation": layer.diagnostics()})
		# Gallery remains the original direct renderer; no native target updates.
		if fixture.name == "portrait":
			baseline.show_gallery = true
			native.show_gallery = true
			baseline.queue_redraw()
			native.queue_redraw()
			layer.sync()
			await process_frame
			await RenderingServer.frame_post_draw
			check(not layer.surface.visible and layer.native_pipeline.native_viewport.render_target_update_mode == SubViewport.UPDATE_DISABLED, "gallery: compositor still visible/updating")
			check(native.sprite_hits().is_empty(), "gallery: ownership picking enabled")
			assert(before.get_texture().get_image().save_png(output.path_join("gallery-baseline.png")) == OK)
			assert(after.get_texture().get_image().save_png(output.path_join("gallery-native-disabled.png")) == OK)
		before.queue_free()
		after.queue_free()
		await process_frame
	var file := FileAccess.open(output.path_join("integration-record.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"fixtures": records, "failures": failures, "source": "Production Session/ArtBook/restaurant_view baseline and candidate render-hook copy. Production files were not edited; this is a concrete integration prototype, not final game acceptance."}, "  "))
	print("INTEGRATION ", records.size(), " fixtures / failures ", failures)
	quit(0 if failures.is_empty() else 1)
