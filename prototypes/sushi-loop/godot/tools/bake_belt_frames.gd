extends SceneTree
## Native-resolution baking: fixed generated structure plus a scrolling deck.
## Run through tools/test_native.py --visible --script tools/bake_belt_frames.gd.
## All phases share exact quarter cuts; no module is resized independently.

class BeltCanvas extends Node2D:
	var source: Texture2D
	var deck_texture: Texture2D
	var source_rect: Rect2
	var deck_polygon: PackedVector2Array
	var deck_bounds: Rect2
	var tile_width := 0.0
	var phase := 0

	func _draw() -> void:
		draw_texture_rect_region(source, Rect2(Vector2.ZERO, source_rect.size), source_rect)
		var uv := PackedVector2Array()
		for point in deck_polygon:
			uv.append(Vector2((point.x - deck_bounds.position.x) / (tile_width * 0.5) - float(phase) / 6.0, (point.y - deck_bounds.position.y) / deck_bounds.size.y))
		draw_polygon(deck_polygon, PackedColorArray([Color.WHITE]), uv, deck_texture)

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/provenance/belt-bake.json"))
	var destination := OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if destination.is_empty():
		push_error("Pass --output pointing to assets/production to save belt frames.")
		quit(1)
		return
	var values: Array = config.source_region
	var source_rect := Rect2(values[0], values[1], values[2], values[3])
	var viewport := SubViewport.new()
	viewport.size = Vector2i(int(source_rect.size.x), int(source_rect.size.y))
	viewport.transparent_bg = true
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	var canvas := BeltCanvas.new()
	canvas.source = load("res://assets/production/" + str(config.source))
	canvas.source_rect = source_rect
	var image := Image.load_from_file("res://assets/production/belt_deck_material.png")
	var material_values: Array = config.material_region
	canvas.deck_texture = ImageTexture.create_from_image(image.get_region(Rect2i(material_values[0], material_values[1], material_values[2], material_values[3])))
	canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	canvas.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	canvas.tile_width = float(viewport.size.x) / 4.0
	for point in config.deck_polygon:
		canvas.deck_polygon.append(Vector2(float(point[0]), float(point[1])))
	var bounds: Array = config.deck_bounds
	canvas.deck_bounds = Rect2(bounds[0], bounds[1], bounds[2], bounds[3])
	viewport.add_child(canvas)
	for phase in range(6):
		canvas.phase = phase
		canvas.queue_redraw()
		await process_frame
		await RenderingServer.frame_post_draw
		var result := viewport.get_texture().get_image()
		if result.save_png(destination.path_join("belt_frame_%02d.png" % phase)) != OK:
			push_error("Could not save connected conveyor frame.")
			quit(1)
			return
	print("Baked six %s connected conveyor frames with exact quarter cuts." % viewport.size)
	viewport.queue_free()
	await process_frame
	quit(0)
