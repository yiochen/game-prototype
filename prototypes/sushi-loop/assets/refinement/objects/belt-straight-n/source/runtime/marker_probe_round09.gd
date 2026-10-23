extends SceneTree
const BaselineMarker = preload("marker_baseline_round09.gd")
const NativeMarker = preload("marker_native_round09.gd")
var records: Array = []
var failures: Array = []
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
func run() -> void:
	var output := OS.get_environment("BELT_MARKER_OUTPUT")
	DirAccess.make_dir_recursive_absolute(output)
	for fixture in [{"name": "phone32", "size": Vector2i(224,400)}, {"name": "phone55", "size": Vector2i(385,700)}, {"name": "portrait", "size": Vector2i(720,1280)}, {"name": "landscape", "size": Vector2i(1440,1000)}]:
		for shift in [Vector2.ZERO,Vector2(0.12345,0.45678)]:
			for marker in ["ground", "ghost-valid", "ghost-invalid"]:
				var before := target(fixture.size)
				var after := target(fixture.size)
				var baseline: Control = BaselineMarker.new()
				var native: Control = NativeMarker.new()
				before.add_child(baseline)
				after.add_child(native)
				var state: Dictionary = {"mode":"edit", "floor":{"columns":7}, "camera":{"x":shift.x, "y":shift.y}, "objects":[{"id":"marker", "x":2, "y":2}], "editor":{"selected_id":"marker" if marker=="ground" else ""}}
				for view in [baseline,native]:
					view.size=Vector2(fixture.size)
					view.state=state
					view.editor_preview={} if marker=="ground" else {"x":2,"y":2,"valid":marker=="ghost-valid"}
					view.update_layout()
					view.queue_redraw()
				native._native_world_layer.sync()
				await process_frame
				await RenderingServer.frame_post_draw
				await process_frame
				await RenderingServer.frame_post_draw
				var phase := "aligned" if shift==Vector2.ZERO else "fractional"
				var prefix: String = fixture.name+"-"+phase+"-"+marker
				before.get_texture().get_image().save_png(output.path_join(prefix+"-baseline.png"))
				after.get_texture().get_image().save_png(output.path_join(prefix+"-native.png"))
				var layer: Node=native._native_world_layer
				var factor: float=layer.native_view._native_screen_pixel_scale
				var roundtrip: float=factor*native.cell/256.0
				if absf(roundtrip-1.0)>.000001:failures.append(prefix+" fixed pixel scale")
				var tile := Rect2(baseline.cell_base(2,2)-Vector2.ONE*baseline.cell*.5,Vector2.ONE*baseline.cell)
				records.append({"name":prefix,"fixture":fixture.name,"marker":marker,"source_size":[fixture.size.x,fixture.size.y],"cell":baseline.cell,"tile":[tile.position.x,tile.position.y,tile.size.x,tile.size.y],"camera":[shift.x,shift.y],"native_pixel_scale":factor,"fixed_pixel_roundtrip":roundtrip,"ground_inset_px":2.0*roundtrip,"ground_stroke_px":maxf(2.0*factor,256.0*.04)*native.cell/256.0,"ghost_inset_px":1.5*roundtrip,"ghost_stroke_px":3.0*roundtrip,"baseline":output.path_join(prefix+"-baseline.png"),"native":output.path_join(prefix+"-native.png")})
				before.queue_free()
				after.queue_free()
				await process_frame
	var file := FileAccess.open(output.path_join("marker-record.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"captures":records,"failures":failures,"method":"Actual Godot GL Compatibility baseline marker methods and fixed native clone methods, isolated on transparent viewports. Full helper camera/floor transform and GPU reduction/presentation remain active. Source-coordinate geometry and raster cross-sections are compared separately; antialias methods can differ."},"  "))
	file.close()
	print("MARKERS ",records.size()," / failures ",failures)
	quit(0 if failures.is_empty() else 1)
