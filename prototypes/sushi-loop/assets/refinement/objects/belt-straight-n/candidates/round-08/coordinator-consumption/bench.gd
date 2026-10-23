extends SceneTree

class SpriteRun:
	extends Node2D
	var image: Texture2D
	var rectangles: Array[Rect2] = []
	func _draw() -> void:
		for rectangle in rectangles:
			draw_texture_rect(image, rectangle, false)

func _initialize() -> void:
	call_deferred("run")

func texture(path: String, mipmaps: bool) -> Texture2D:
	var pixels := Image.load_from_file(path)
	if mipmaps: pixels.generate_mipmaps()
	return ImageTexture.create_from_image(pixels)

func run() -> void:
	var tests: Array[Dictionary] = []
	for tile in [128, 32]:
		var factor := float(tile) / 256.0
		for mode in ["linear", "linear-mips", "nearest", "composite-linear-mips", "composite-nearest", "imported-linear-mips", "composite-imported-linear-mips"]:
			var viewport := SubViewport.new()
			viewport.size = Vector2i(roundi(384 * factor), roundi(1216 * factor))
			viewport.transparent_bg = true
			viewport.disable_3d = true
			viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
			root.add_child(viewport)
			var drawing := SpriteRun.new()
			drawing.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if mode.ends_with("nearest") else CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS if mode.ends_with("mips") else CanvasItem.TEXTURE_FILTER_LINEAR
			if mode.begins_with("composite"):
				drawing.image = load("res://inputs/composite.png") if mode.contains("imported") else texture("res://inputs/composite.png", mode.ends_with("mips"))
				drawing.rectangles.append(Rect2(Vector2.ZERO, Vector2(viewport.size)))
			else:
				drawing.image = load("res://inputs/sprite.png") if mode.contains("imported") else texture("res://inputs/sprite.png", mode.ends_with("mips"))
				for y in [0, 256, 512]:
					drawing.rectangles.append(Rect2(Vector2(0, y * factor), Vector2(384, 704) * factor))
			viewport.add_child(drawing)
			tests.append({"viewport": viewport, "output": "%s-%d.png" % [mode, tile]})
	await process_frame
	await RenderingServer.frame_post_draw
	await process_frame
	await RenderingServer.frame_post_draw
	for entry in tests:
		var pixels: Image = entry.viewport.get_texture().get_image()
		var result := pixels.save_png("res://" + entry.output)
		assert(result == OK)
	print("Saved %d actual Godot filter comparisons" % tests.size())
	quit()
